import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.prompts import (
    MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
    ORGANIZE_MEMORY_SYSTEM_PROMPT,
    ORGANIZE_SELECTION_SYSTEM_PROMPT,
    TITLE_GENERATION_PROMPT,
)
from config.settings import get_setting
from core.hashing import compute_string_hash
from core.logger import handle_errors, logger
from core.memory_service import handle_delete_memory, reindex_memory_chunks
from storage.db_manager import (
    find_memory_by_title_or_slug,
    get_all_memories,
    get_memory_by_id,
    upsert_memory_index,
)
from storage.markdown_handler import (
    create_markdown_file,
    normalize_title,
    read_markdown_file,
)
from storage.version_manager import create_version_snapshot
from utils.llm_client import generate_llm_response
from vector.chunker import count_tokens

# Default token budget for single-shot LLM merge prompt
DEFAULT_MAX_MERGE_CONTEXT_TOKENS = 3500


def clean_llm_markdown_output(output: str) -> str:
    """Strips outer markdown code fences from LLM responses if wrapped."""
    if not output:
        return ""
    cleaned = output.strip()
    cleaned = re.sub(r"^```markdown\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def deterministic_merge_memories(
    memories: List[Dict[str, Any]],
    target_title: str,
) -> str:
    """
    Fallback deterministic merger when LLM is offline or disabled.
    Structures notes cleanly under Markdown sections and removes exact duplicate lines.
    """
    sections = [f"# {target_title}\n"]
    seen_blocks = set()

    for idx, mem in enumerate(memories, 1):
        title = mem.get("title", f"Note {idx}")
        content = mem.get("content", "").strip()
        
        # Strip duplicate top-level title header if already matches
        cleaned_content = re.sub(r"^#+\s+" + re.escape(title) + r"\s*\n*", "", content, flags=re.IGNORECASE).strip()
        
        if not cleaned_content:
            continue

        content_hash = compute_string_hash(cleaned_content)
        if content_hash in seen_blocks:
            continue
        seen_blocks.add(content_hash)

        sections.append(f"## {title}\n\n{cleaned_content}\n")

    return "\n".join(sections).strip()


def progressive_llm_merge(
    memories: List[Dict[str, Any]],
    target_title: str,
    custom_instruction: Optional[str] = None,
    max_context_tokens: int = DEFAULT_MAX_MERGE_CONTEXT_TOKENS,
) -> str:
    """
    Hierarchical / progressive fold merge for large memory sets.
    Iteratively merges notes chunk-by-chunk to stay strictly within the LLM context window.
    """
    if not memories:
        return ""
    
    current_merged = memories[0].get("content", "").strip()
    instruction_note = f"\nSpecial Instruction: {custom_instruction.strip()}" if custom_instruction else ""

    for idx in range(1, len(memories)):
        next_mem = memories[idx]
        next_title = next_mem.get("title", f"Note {idx + 1}")
        next_content = next_mem.get("content", "").strip()

        prompt = (
            f"Consolidated Title: {target_title}\n"
            f"{instruction_note}\n\n"
            f"--- EXISTING CONSOLIDATED KNOWLEDGE ---\n"
            f"{current_merged}\n\n"
            f"--- NEW NOTE TO INTEGRATE ({next_title}) ---\n"
            f"{next_content}\n\n"
            f"Synthesize all unique details, code snippets, and facts into the consolidated document:"
        )

        try:
            res = generate_llm_response(
                prompt=prompt,
                system_prompt=MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
                temperature=0.2,
            )
            cleaned = clean_llm_markdown_output(res)
            if cleaned:
                current_merged = cleaned
            else:
                current_merged = f"{current_merged}\n\n## {next_title}\n{next_content}"
        except Exception as e:
            logger.warning(f"Step {idx} of progressive merge failed: {e}. Appending deterministically.")
            current_merged = f"{current_merged}\n\n## {next_title}\n{next_content}"

    return current_merged


@handle_errors
def merge_memories_service(
    memory_ids: List[str],
    target_title: Optional[str] = None,
    target_category: Optional[str] = None,
    target_tags: Optional[List[str]] = None,
    delete_sources: bool = True,
    instruction: Optional[str] = None,
    use_ai: Optional[bool] = None,
    max_context_tokens: int = DEFAULT_MAX_MERGE_CONTEXT_TOKENS,
) -> Dict[str, Any]:
    """
    Consolidates multiple memories into a single unified knowledge note using context-safe LLM synthesis.
    Persists updates across Markdown storage, SQLite, and ChromaDB vector embeddings.
    """
    if not memory_ids or len(memory_ids) < 2:
        return {
            "status": "error",
            "message": "At least 2 memory IDs are required to perform a merge.",
        }

    # 1. Fetch and validate all requested memories
    valid_memories: List[Dict[str, Any]] = []
    seen_ids = set()

    for mid in memory_ids:
        mid_clean = mid.strip()
        if not mid_clean or mid_clean in seen_ids:
            continue
        mem = get_memory_by_id(mid_clean)
        if not mem:
            continue
        
        # Ensure content is present (fallback to reading markdown file directly)
        content = mem.get("content", "")
        file_path = mem.get("file_path", "")
        if not content and file_path and Path(file_path).exists():
            try:
                _, content = read_markdown_file(Path(file_path))
                mem["content"] = content
            except Exception:
                pass

        valid_memories.append(mem)
        seen_ids.add(mid_clean)

    if len(valid_memories) < 2:
        return {
            "status": "error",
            "message": f"Could not find at least 2 valid memories from IDs: {memory_ids}",
        }

    primary_mem = valid_memories[0]
    primary_id = primary_mem["id"]

    # 2. Determine target metadata (Title, Category, Tags)
    final_title = normalize_title(target_title.strip() if target_title and target_title.strip() else primary_mem["title"])
    final_category = (target_category.strip().lower() if target_category and target_category.strip() else primary_mem.get("category", "personal"))
    
    all_tags = []
    if target_tags:
        all_tags.extend(target_tags)
    for m in valid_memories:
        m_tags = m.get("tags", [])
        if isinstance(m_tags, list):
            all_tags.extend(m_tags)
        elif isinstance(m_tags, str):
            try:
                import json
                all_tags.extend(json.loads(m_tags))
            except Exception:
                pass
    final_tags = sorted(list({t.strip().lower() for t in all_tags if t and t.strip()}))

    # 3. Calculate token requirements and execute context-safe synthesis
    if use_ai is not None:
        use_llm = bool(use_ai)
    else:
        import config.constants as constants
        use_llm = bool(constants.USE_LLM) and bool(get_setting("use_llm", True))

    total_tokens = sum(count_tokens(m.get("content", "")) for m in valid_memories)
    merged_content = ""

    if not use_llm:
        logger.info(f"USE_LLM is false. Performing deterministic structured merge for {len(valid_memories)} notes.")
        merged_content = deterministic_merge_memories(valid_memories, final_title)
    else:
        logger.info(f"Merging {len(valid_memories)} memories ({total_tokens} tokens) using LLM...")
        if total_tokens <= max_context_tokens:
            # Single-shot synthesis
            notes_context_blocks = []
            for idx, m in enumerate(valid_memories, 1):
                notes_context_blocks.append(
                    f"### NOTE {idx}: {m.get('title', 'Untitled')} [ID: {m.get('id')}, Category: {m.get('category')}]\n"
                    f"{m.get('content', '').strip()}\n"
                )
            
            instruction_text = f"\nUser Instruction: {instruction.strip()}\n" if instruction else ""
            prompt = (
                f"Unified Document Title: {final_title}\n"
                f"Target Category: {final_category}\n"
                f"{instruction_text}\n"
                f"--- SOURCE NOTES TO CONSOLIDATE ---\n"
                + "\n".join(notes_context_blocks)
                + "\nGenerate the comprehensive, consolidated Markdown documentation:"
            )

            try:
                resp = generate_llm_response(
                    prompt=prompt,
                    system_prompt=MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
                    temperature=0.2,
                )
                merged_content = clean_llm_markdown_output(resp)
            except Exception as e:
                logger.warning(f"Single-shot LLM merge failed: {e}. Falling back to progressive fold.")
                merged_content = progressive_llm_merge(valid_memories, final_title, instruction, max_context_tokens)
        else:
            # Multi-note hierarchical reduction to prevent context overflow
            logger.info(f"Total tokens ({total_tokens}) exceed single prompt limit ({max_context_tokens}). Running progressive fold merge.")
            merged_content = progressive_llm_merge(valid_memories, final_title, instruction, max_context_tokens)

    if not merged_content.strip():
        merged_content = deterministic_merge_memories(valid_memories, final_title)

    # 4. Persistence: Snapshot target, write unified markdown, and update vector index
    create_version_snapshot(primary_id)

    target_file_path = Path(primary_mem["file_path"]) if primary_mem.get("file_path") else None
    content_hash = compute_string_hash(merged_content)

    updated_path = create_markdown_file(
        memory_id=primary_id,
        title=final_title,
        category=final_category,
        tags=final_tags,
        content=merged_content,
        content_hash=content_hash,
        created_at=primary_mem.get("created_at"),
        file_path=target_file_path,
        overwrite=True,
    )

    chunks, chunk_ids = reindex_memory_chunks(primary_id, merged_content)

    memory_entry = {
        "id": primary_id,
        "title": final_title,
        "category": final_category,
        "tags": final_tags,
        "file_path": str(updated_path),
        "content": merged_content,
        "content_hash": content_hash,
        "created_at": primary_mem.get("created_at"),
        "chunk_ids": chunk_ids,
    }
    upsert_memory_index(memory_entry)

    # 5. Clean up secondary source notes if delete_sources is enabled
    deleted_source_ids: List[str] = []
    if delete_sources:
        for m in valid_memories:
            sec_id = m["id"]
            if sec_id != primary_id:
                try:
                    handle_delete_memory(norm_title="", category="", memory_id=sec_id)
                    deleted_source_ids.append(sec_id)
                except Exception as e:
                    logger.warning(f"Could not delete merged source memory '{sec_id}': {e}")

    logger.info(
        f"Successfully merged {len(valid_memories)} memories into '{primary_id}' ('{final_title}'). "
        f"Deleted {len(deleted_source_ids)} source records."
    )

    return {
        "status": "success",
        "action": "merge",
        "merged_memory_id": primary_id,
        "title": final_title,
        "category": final_category,
        "tags": final_tags,
        "file_path": str(updated_path),
        "chunk_count": len(chunks),
        "merged_source_count": len(valid_memories),
        "deleted_source_ids": deleted_source_ids,
        "content_preview": (merged_content[:300] + "...") if len(merged_content) > 300 else merged_content,
    }


def find_correlated_memories(
    memory_id: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Finds correlated/similar memories for a given memory ID using vector similarity,
    category matches, and shared tag overlaps.
    """
    target = get_memory_by_id(memory_id)
    if not target or not isinstance(target, dict):
        return []

    all_memories = get_all_memories()
    if not isinstance(all_memories, list):
        return []

    target_tags = set(target.get("tags", [])) if isinstance(target.get("tags"), list) else set()
    target_category = target.get("category", "personal").lower()
    target_text = f"{target.get('title', '')} {target.get('content', '')[:500]}".strip()

    # Perform vector similarity search safely
    vector_scores: Dict[str, float] = {}
    try:
        from search.relevance_scorer import search_hybrid_relevance
        vector_results = search_hybrid_relevance(query=target_text, top_k=top_k * 2)
        if isinstance(vector_results, list):
            for r in vector_results:
                if isinstance(r, dict) and r.get("id"):
                    vector_scores[r.get("id")] = float(r.get("final_score", r.get("score", 0.0)))
    except Exception as e:
        logger.warning(f"Vector correlation lookup failed: {e}")

    candidates = []
    for mem in all_memories:
        if not isinstance(mem, dict):
            continue
        m_id = mem.get("id")
        if not m_id or m_id == memory_id:
            continue

        m_category = mem.get("category", "personal").lower()
        m_tags = set(mem.get("tags", [])) if isinstance(mem.get("tags"), list) else set()
        
        shared_tags = list(target_tags.intersection(m_tags))
        category_match = (m_category == target_category)

        # Base similarity from vector search or heuristic
        v_score = vector_scores.get(m_id, 0.0)
        tag_score = len(shared_tags) * 0.15
        cat_score = 0.2 if category_match else 0.0

        combined_score = min(1.0, round(v_score * 0.6 + tag_score + cat_score, 3))
        
        if combined_score > 0.15 or shared_tags or category_match:
            candidates.append({
                "id": m_id,
                "title": mem.get("title", "Untitled Note"),
                "category": m_category,
                "tags": mem.get("tags", []),
                "shared_tags": shared_tags,
                "same_category": category_match,
                "similarity_score": combined_score,
                "similarity_percent": int(combined_score * 100),
                "snippet": mem.get("snippet", "") or mem.get("content", "")[:160],
            })

    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return candidates[:top_k]


def clean_generated_title(raw_title: str) -> str:
    """Strips quotes, prefixes, markdown artifacts and normalizes a generated title."""
    if not raw_title:
        return "Untitled Note"
    clean = raw_title.strip()
    # Strip wrapping quotes, backticks
    clean = re.sub(r"^[\"\'`]+|[\"\'`]+$", "", clean).strip()
    # Strip prefixes like 'Title:', '# Title:', '**Title**:'
    clean = re.sub(r"^(?:#+\s*|\*{1,2})?(?:title|summary|topic):\s*", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^#+\s*", "", clean).strip()
    clean = re.sub(r"^\*\*(.*?)\*\*$", r"\1", clean).strip()
    clean = re.sub(r"^\*(.*?)\*$", r"\1", clean).strip()
    clean = clean.split("\n")[0].strip()
    # Clean leading numbers or bullet markers
    clean = re.sub(r"^\d+[\.\)]\s*", "", clean).strip()
    return normalize_title(clean) if clean else "Untitled Note"


@handle_errors
def generate_title_service(
    content: str,
    current_title: Optional[str] = None,
    instruction: Optional[str] = None,
    use_ai: bool = True,
) -> str:
    """
    Generates a concise, descriptive, and high-signal title (3-7 words) from markdown content or excerpt.
    """
    if not content or not content.strip():
        return normalize_title(current_title) if current_title else "Untitled Note"

    clean_content = content.strip()

    if use_ai:
        prompt_parts = []
        if current_title and current_title not in ("Untitled Note", "Untitled Memory", "Untitled", "Note"):
            prompt_parts.append(f"Current Working Title: {current_title}")
        if instruction:
            prompt_parts.append(f"User Goal / Context: {instruction}")
        prompt_parts.append(f"Content Body:\n{clean_content[:3500]}\n")
        prompt_parts.append("Generate concise descriptive title:")
        prompt = "\n".join(prompt_parts)

        try:
            res = generate_llm_response(
                prompt=prompt,
                system_prompt=TITLE_GENERATION_PROMPT,
                temperature=0.3,
            )
            title = clean_generated_title(res)
            if title and title != "Untitled Note":
                return title
        except Exception as e:
            logger.warning(f"AI title generation failed: {e}. Falling back to heuristic extraction.")

    # Heuristic fallback: Extract first heading or first few words
    lines = [line.strip() for line in clean_content.split("\n") if line.strip()]
    for line in lines:
        if line.startswith("#"):
            heading = re.sub(r"^#+\s*", "", line).strip()
            if heading:
                return clean_generated_title(heading)
    if lines:
        first_line = lines[0]
        words = first_line.split()[:7]
        return clean_generated_title(" ".join(words))

    return normalize_title(current_title) if current_title else "Untitled Note"


@handle_errors
def organize_selection_service(
    selected_text: str,
    instruction: Optional[str] = None,
    mode: Optional[str] = "polish",
    full_context: Optional[str] = None,
    use_ai: bool = True,
) -> Dict[str, Any]:
    """
    Polishes, summarizes, or transforms a selected paragraph or text snippet using AI.
    """
    if not selected_text or not selected_text.strip():
        return {
            "status": "error",
            "message": "No text selected to transform.",
        }

    clean_selection = selected_text.strip()
    mode_clean = (mode or "polish").strip().lower()

    if mode_clean == "title":
        generated_title = generate_title_service(
            content=clean_selection,
            instruction=instruction,
            use_ai=use_ai,
        )
        return {
            "status": "success",
            "action": "title_generated",
            "mode": mode_clean,
            "transformed_text": generated_title,
            "title": generated_title,
        }

    if not use_ai:
        return {
            "status": "success",
            "action": "transformed",
            "mode": mode_clean,
            "transformed_text": clean_selection,
        }

    mode_instructions = {
        "polish": "Polish grammar, improve sentence flow, fix indentation, and format cleanly as Markdown.",
        "summarize": "Summarize the core insights of this selection into concise, high-impact bullet points.",
        "technical": "Restructure and format as clean technical documentation with clear subheadings, code syntax blocks, equations ($...$), or parameter lists.",
        "simplify": "Simplify this passage for maximum clarity and quick readability while keeping all key facts.",
        "expand": "Elaborate on the key ideas with structured explanations and concrete details.",
    }

    effective_instruction = instruction if instruction else mode_instructions.get(mode_clean, mode_instructions["polish"])

    prompt_parts = []
    if full_context:
        prompt_parts.append(f"Surrounding Document Context:\n{full_context[:1200]}\n")
    prompt_parts.append(f"Task / Goal: {effective_instruction}")
    prompt_parts.append(f"--- SELECTED TEXT TO TRANSFORM ---\n{clean_selection}\n\nTransformed Markdown Replacement:")
    prompt = "\n".join(prompt_parts)

    try:
        res = generate_llm_response(
            prompt=prompt,
            system_prompt=ORGANIZE_SELECTION_SYSTEM_PROMPT,
            temperature=0.2,
        )
        transformed = clean_llm_markdown_output(res)
        if not transformed:
            transformed = clean_selection
    except Exception as e:
        logger.warning(f"AI selection transformation failed: {e}. Returning original.")
        transformed = clean_selection

    return {
        "status": "success",
        "action": "transformed",
        "mode": mode_clean,
        "transformed_text": transformed,
    }


@handle_errors
def organize_single_memory_service(
    memory_id: str,
    instruction: Optional[str] = None,
    use_ai: bool = True,
    generate_title: bool = False,
) -> Dict[str, Any]:
    """
    Polishes, restructures, organizes, or summarizes a single memory using AI.
    Optionally generates and updates a concise, descriptive title.
    Automatically creates a version snapshot before updating so the user can easily revert.
    """
    target = get_memory_by_id(memory_id)
    if not target:
        return {
            "status": "error",
            "message": f"Memory '{memory_id}' not found.",
        }

    title = target.get("title", "Untitled Note")
    category = target.get("category", "personal")
    tags = target.get("tags", [])
    if isinstance(tags, str):
        try:
            import json
            tags = json.loads(tags)
        except Exception:
            tags = []
    
    file_path = target.get("file_path", "")
    content = target.get("content", "")
    if not content and file_path and Path(file_path).exists():
        try:
            _, content = read_markdown_file(Path(file_path))
        except Exception:
            content = ""

    if not content:
        return {
            "status": "error",
            "message": f"Memory '{memory_id}' has no content to organize.",
        }

    # 1. Take a version snapshot prior to modification
    create_version_snapshot(memory_id=memory_id)

    # 2. Process content using AI (or fallback formatting)
    organized_content = ""
    if use_ai:
        instruction_note = f"\nUser Instruction / Goal: {instruction.strip()}\n" if instruction else ""
        prompt = (
            f"Document Title: {title}\n"
            f"Category: {category}\n"
            f"Tags: {', '.join(tags) if tags else 'none'}\n"
            f"{instruction_note}\n"
            f"--- ORIGINAL CONTENT ---\n"
            f"{content}\n\n"
            f"Polished, well-structured, clean Markdown document:"
        )

        try:
            res = generate_llm_response(
                prompt=prompt,
                system_prompt=ORGANIZE_MEMORY_SYSTEM_PROMPT,
                temperature=0.2,
            )
            organized_content = clean_llm_markdown_output(res)
        except Exception as e:
            logger.warning(f"AI organization failed: {e}. Keeping existing content.")
            organized_content = content
    else:
        organized_content = content.strip()

    if not organized_content:
        organized_content = content

    # 3. Generate or refine title if requested or if title is untitled
    final_title = title
    if generate_title or title in ("Untitled Note", "Untitled Memory", "Untitled", ""):
        try:
            generated_t = generate_title_service(
                content=organized_content,
                current_title=title,
                instruction=instruction,
                use_ai=use_ai,
            )
            if generated_t and generated_t not in ("Untitled Note", "Untitled Memory"):
                final_title = generated_t
        except Exception as e:
            logger.warning(f"Title generation during AI organize failed: {e}")

    # 4. Save updated Markdown file to disk
    old_file_path = Path(file_path) if file_path else None
    created_path = create_markdown_file(
        memory_id=memory_id,
        title=final_title,
        category=category,
        tags=tags,
        content=organized_content,
        overwrite=True,
    )
    if old_file_path and old_file_path.exists() and old_file_path.resolve() != created_path.resolve():
        try:
            old_file_path.unlink(missing_ok=True)
        except Exception:
            pass

    # 5. Re-index vector embeddings in ChromaDB
    chunk_count = 0
    chunk_ids = []
    try:
        chunks, chunk_ids = reindex_memory_chunks(memory_id, organized_content)
        chunk_count = len(chunks)
    except Exception as e:
        logger.warning(f"Vector reindexing failed during organization: {e}")

    # 6. Upsert SQLite record
    content_hash = compute_string_hash(organized_content)
    snippet = organized_content[:180].replace("\n", " ").strip()
    memory_entry = {
        "id": memory_id,
        "title": final_title,
        "category": category,
        "tags": tags,
        "file_path": str(created_path),
        "content": organized_content,
        "content_hash": content_hash,
        "created_at": target.get("created_at"),
        "chunk_ids": chunk_ids,
        "snippet": snippet,
    }
    upsert_memory_index(memory_entry)

    logger.info(f"Successfully organized memory '{memory_id}' ('{final_title}') with AI.")
    return {
        "status": "success",
        "action": "organized",
        "memory_id": memory_id,
        "title": final_title,
        "category": category,
        "tags": tags,
        "file_path": str(created_path),
        "chunk_count": chunk_count,
        "content": organized_content,
        "content_preview": organized_content[:300],
    }

