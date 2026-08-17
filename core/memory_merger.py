import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.settings import get_setting
from core.hashing import compute_string_hash
from core.llm_tasks import (
    DEFAULT_MAX_MERGE_CONTEXT_TOKENS,
    clean_generated_title,
    clean_llm_markdown_output,
    llm_generate_title,
    llm_organize_note,
    llm_synthesize_memories,
    llm_transform_selection,
    progressive_llm_merge,
)
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
from vector.chunker import count_tokens


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
            "message": "At least two memory IDs are required to perform a merge.",
        }

    # 1. Fetch all requested memories
    valid_memories = []
    missing_ids = []
    for m_id in memory_ids:
        mem = get_memory_by_id(m_id)
        if not mem:
            # Try loading from disk if not indexed
            from storage.sync_manager import get_memory_file_status
            status = get_memory_file_status(m_id)
            if status.get("status") != "error":
                mem = status.get("memory")
        if mem:
            # Ensure content is loaded
            if not mem.get("content") and mem.get("file_path"):
                try:
                    _, content = read_markdown_file(Path(mem["file_path"]))
                    mem["content"] = content
                except Exception:
                    pass
            valid_memories.append(mem)
        else:
            missing_ids.append(m_id)

    if len(valid_memories) < 2:
        return {
            "status": "error",
            "message": f"Insufficient valid memories found for merge. Missing: {missing_ids}",
            "missing_ids": missing_ids,
        }

    # Primary memory acts as destination/anchor
    primary_mem = valid_memories[0]
    primary_id = primary_mem["id"]
    final_title = normalize_title(target_title) if target_title else primary_mem.get("title", "Unified Consolidated Knowledge")
    final_category = target_category or primary_mem.get("category", "personal")

    # Combine & deduplicate tags
    all_tags = set(target_tags or [])
    for m in valid_memories:
        m_tags = m.get("tags", [])
        if isinstance(m_tags, str):
            try:
                import json
                m_tags = json.loads(m_tags)
            except Exception:
                m_tags = [t.strip() for t in m_tags.split(",") if t.strip()]
        if isinstance(m_tags, list):
            all_tags.update([t.strip().lower() for t in m_tags if t.strip()])
    final_tags = sorted(list(all_tags))

    # 2. Determine merge engine (AI synthesis vs deterministic)
    should_use_ai = use_ai if use_ai is not None else bool(get_setting("use_llm", False))

    merged_content = ""
    if not should_use_ai:
        logger.info(f"Merging {len(valid_memories)} memories deterministically (AI disabled).")
        merged_content = deterministic_merge_memories(valid_memories, final_title)
    else:
        logger.info(f"Merging {len(valid_memories)} memories using AI synthesis.")
        total_tokens = sum(count_tokens(m.get("content", "")) for m in valid_memories)

        if total_tokens <= max_context_tokens:
            try:
                merged_content = llm_synthesize_memories(
                    memories=valid_memories,
                    target_title=final_title,
                    custom_instruction=instruction,
                )
            except Exception as e:
                logger.warning(f"Single-shot LLM merge failed: {e}. Falling back to progressive fold.")
                merged_content = progressive_llm_merge(valid_memories, final_title, instruction, max_context_tokens)
        else:
            logger.info(f"Total tokens ({total_tokens}) exceed single prompt limit ({max_context_tokens}). Running progressive fold merge.")
            merged_content = progressive_llm_merge(valid_memories, final_title, instruction, max_context_tokens)

    if not merged_content.strip():
        merged_content = deterministic_merge_memories(valid_memories, final_title)

    # 3. Persistence: Snapshot target, write unified markdown, and update vector index
    create_version_snapshot(primary_id)

    target_file_path = Path(primary_mem["file_path"]) if primary_mem.get("file_path") else None
    content_hash = compute_string_hash(merged_content)
    snippet = merged_content[:180].replace("\n", " ").strip()

    created_path = create_markdown_file(
        memory_id=primary_id,
        title=final_title,
        category=final_category,
        tags=final_tags,
        content=merged_content,
        overwrite=True,
    )

    if target_file_path and target_file_path.exists() and target_file_path.resolve() != created_path.resolve():
        try:
            target_file_path.unlink(missing_ok=True)
        except Exception:
            pass

    # Re-index in ChromaDB
    chunk_count = 0
    chunk_ids = []
    try:
        chunks, chunk_ids = reindex_memory_chunks(primary_id, merged_content)
        chunk_count = len(chunks)
    except Exception as e:
        logger.warning(f"Vector reindexing failed during merge: {e}")

    # Upsert primary memory in DB
    updated_record = {
        "id": primary_id,
        "title": final_title,
        "category": final_category,
        "tags": final_tags,
        "file_path": str(created_path),
        "content": merged_content,
        "content_hash": content_hash,
        "created_at": primary_mem.get("created_at"),
        "chunk_ids": chunk_ids,
        "snippet": snippet,
    }
    upsert_memory_index(updated_record)

    # 4. Clean up source memories if requested
    deleted_source_ids = []
    if delete_sources:
        for mem in valid_memories[1:]:
            s_id = mem.get("id")
            if s_id and s_id != primary_id:
                try:
                    handle_delete_memory(norm_title="", category="", memory_id=s_id)
                    deleted_source_ids.append(s_id)
                except Exception as e:
                    logger.warning(f"Failed to delete source memory '{s_id}': {e}")

    logger.info(f"Merge completed successfully into '{primary_id}' ('{final_title}'). Deleted sources: {deleted_source_ids}")

    return {
        "status": "success",
        "action": "merged",
        "merged_memory_id": primary_id,
        "primary_id": primary_id,
        "title": final_title,
        "category": final_category,
        "tags": final_tags,
        "file_path": str(created_path),
        "merged_source_count": len(valid_memories),
        "deleted_source_ids": deleted_source_ids,
        "chunk_count": chunk_count,
        "content_preview": merged_content[:300],
    }


@handle_errors
def find_correlated_memories(
    memory_id: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Identifies logically related or overlapping memories based on vector similarity, shared tags, and category match.
    """
    target = get_memory_by_id(memory_id)
    if not target:
        return []

    target_category = target.get("category", "personal").lower()
    target_tags = set(target.get("tags", [])) if isinstance(target.get("tags"), list) else set()
    target_content = target.get("content", "")

    # Perform vector similarity query using target note content
    vector_scores: Dict[str, float] = {}
    if target_content:
        from search.relevance_scorer import search_hybrid_relevance
        try:
            results = search_hybrid_relevance(query=target_content[:500], top_k=top_k * 2)
            for res in results:
                m_id = res.get("id")
                if m_id and m_id != memory_id:
                    vector_scores[m_id] = float(res.get("vector_score") or res.get("final_score", 0.5))
        except Exception as e:
            logger.warning(f"Vector search failed during correlation discovery: {e}")

    all_memories = get_all_memories()
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
        try:
            title = llm_generate_title(
                content=clean_content,
                current_title=current_title,
                instruction=instruction,
            )
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

    try:
        transformed = llm_transform_selection(
            selected_text=clean_selection,
            mode=mode_clean,
            instruction=instruction,
            full_context=full_context,
        )
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
        try:
            organized_content = llm_organize_note(
                content=content,
                title=title,
                category=category,
                tags=tags,
                instruction=instruction,
            )
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
