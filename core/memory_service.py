from pathlib import Path
from typing import Any, Dict, List, Optional

from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from core.smart_updater import smart_merge_memory_content
from core.logger import logger
from storage.db_manager import (
    db_get_version_by_number,
    db_get_versions,
    delete_memory_from_index,
    find_memory_by_content_hash,
    find_memory_by_title_or_slug,
    get_memory_by_id,
    upsert_memory_index,
)
from storage.markdown_handler import (
    append_to_markdown_file,
    create_markdown_file,
    delete_markdown_file,
    normalize_title,
    read_markdown_file,
)
from storage.version_manager import create_version_snapshot
from vector.chunker import chunk_text
from vector.embedder import generate_embeddings
from vector.vector_db import (
    add_chunks_to_vector_db,
    delete_chunks_by_memory_id,
    get_or_create_collection,
)


def reindex_memory_chunks(memory_id: str, content: str, force: bool = False) -> tuple[list, list]:
    """
    Deletes existing vector chunks, generates new chunks + embeddings, and adds them to ChromaDB.
    If content hash is unchanged and vector chunks exist in ChromaDB, skips redundant embedding generation.
    Returns tuple of (chunks, chunk_ids).
    """
    if not force:
        new_hash = compute_string_hash(content)
        existing = get_memory_by_id(memory_id)
        if existing and existing.get("content_hash") == new_hash:
            try:
                collection = get_or_create_collection("memories")
                existing_chroma = collection.get(where={"memory_id": memory_id}, include=["documents"])
                if existing_chroma and existing_chroma.get("ids"):
                    chunk_ids = existing_chroma["ids"]
                    chunks = [
                        {"chunk_id": cid, "memory_id": memory_id, "text": txt}
                        for cid, txt in zip(chunk_ids, existing_chroma.get("documents", []))
                    ]
                    logger.info(f"Skipping redundant re-indexing for '{memory_id}' (content hash {new_hash[:8]}... unchanged).")
                    return chunks, chunk_ids
            except Exception as e:
                logger.warning(f"Error checking existing ChromaDB chunks for '{memory_id}': {e}")

    delete_chunks_by_memory_id(memory_id)
    chunks = chunk_text(memory_id, content)
    chunk_ids = []

    if chunks:
        chunk_texts = [c.get("text") or c.get("content", "") for c in chunks]
        embeddings = generate_embeddings(chunk_texts)
        add_chunks_to_vector_db(chunks, embeddings)
        chunk_ids = [c.get("chunk_id") or c.get("id", "") for c in chunks]

    return chunks, chunk_ids


def handle_delete_memory(norm_title: str, category: str, memory_id: Optional[str] = None) -> dict:
    """
    Handles deleting a memory from Markdown disk, ChromaDB vector store, and SQLite index.
    """
    target = None
    if memory_id:
        target = get_memory_by_id(memory_id)
    if not target and norm_title:
        target = find_memory_by_title_or_slug(norm_title, category)

    if not target:
        return {"status": "error", "message": "Memory not found for deletion."}

    target_id = target["id"]
    file_path = target.get("file_path")
    if file_path:
        delete_markdown_file(file_path)

    delete_chunks_by_memory_id(target_id)
    delete_memory_from_index(target_id)

    return {
        "status": "success",
        "action": "delete",
        "memory_id": target_id,
        "message": f"Memory '{target_id}' successfully deleted.",
    }


def handle_existing_memory(
    existing: dict,
    norm_title: str,
    content: str,
    action_clean: str,
    category: str,
    tags: List[str],
) -> dict:
    """
    Handles updating or appending to an existing memory file using LLM smart merge,
    creates version control snapshot prior to update, and re-indexes vector chunks.
    """
    target_id = existing["id"]
    file_path = Path(existing["file_path"])

    # 1. Create a version snapshot before applying modifications
    create_version_snapshot(target_id)

    existing_content = existing.get("content", "")
    if not existing_content and file_path.exists():
        try:
            _, existing_content = read_markdown_file(file_path)
        except Exception:
            existing_content = ""

    if action_clean == "append":
        updated_path, target_id, full_content = append_to_markdown_file(
            file_path=file_path,
            additional_content=content,
            tags=tags,
        )
        content_hash = compute_string_hash(full_content)
        actual_action = "append"
    else:  # 'update', 'auto', 'smart' -> Smart LLM contextual merge
        combined_tags = list(set(existing.get("tags", []) + tags))
        full_content = smart_merge_memory_content(
            existing_content=existing_content,
            new_input=content,
            title=norm_title,
        )
        content_hash = compute_string_hash(full_content)
        updated_path = create_markdown_file(
            memory_id=target_id,
            title=norm_title,
            category=category,
            tags=combined_tags,
            content=full_content,
            content_hash=content_hash,
            created_at=existing.get("created_at"),
            file_path=file_path,
            overwrite=True,
        )
        actual_action = "smart_update"

    chunks, chunk_ids = reindex_memory_chunks(target_id, full_content)

    memory_entry = {
        "id": target_id,
        "title": norm_title,
        "category": category,
        "tags": list(set(existing.get("tags", []) + tags)),
        "file_path": str(updated_path),
        "content": full_content,
        "content_hash": content_hash,
        "created_at": existing.get("created_at"),
        "chunk_ids": chunk_ids,
    }
    upsert_memory_index(memory_entry)

    return {
        "status": "success",
        "action": actual_action,
        "memory_id": target_id,
        "title": norm_title,
        "category": category,
        "file_path": str(updated_path),
        "chunk_count": len(chunks),
    }


def handle_new_memory(
    norm_title: str,
    content: str,
    category: str,
    tags: List[str],
    memory_id: Optional[str] = None,
) -> dict:
    """
    Handles creating a new Markdown memory file, chunking, embedding, and indexing.
    """
    new_id = memory_id if memory_id else generate_memory_id()
    content_hash = compute_string_hash(content)

    new_file_path = create_markdown_file(
        memory_id=new_id,
        title=norm_title,
        category=category,
        tags=tags,
        content=content,
        content_hash=content_hash,
        overwrite=False,
    )

    chunks, chunk_ids = reindex_memory_chunks(new_id, content)

    memory_entry = {
        "id": new_id,
        "title": norm_title,
        "category": category,
        "tags": tags,
        "file_path": str(new_file_path),
        "content": content,
        "content_hash": content_hash,
        "chunk_ids": chunk_ids,
    }
    upsert_memory_index(memory_entry)

    return {
        "status": "success",
        "action": "insert",
        "memory_id": new_id,
        "title": norm_title,
        "category": category,
        "tags": tags,
        "file_path": str(new_file_path),
        "chunk_count": len(chunks),
    }


def execute_upsert_memory(
    title: str,
    content: str = "",
    action: str = "auto",
    category: str = "personal",
    tags: Optional[List[str]] = None,
    memory_id: Optional[str] = None,
) -> dict:
    """
    Orchestrates memory creation, update, append, or deletion using modular helper functions.
    """
    if tags is None:
        tags = []

    norm_title = normalize_title(title)
    cat_clean = category.strip().lower() if category else "personal"
    action_clean = action.strip().lower()

    if action_clean == "delete":
        return handle_delete_memory(
            norm_title=norm_title, category=cat_clean, memory_id=memory_id
        )

    existing = None
    if memory_id:
        existing = get_memory_by_id(memory_id)
    if not existing and norm_title:
        existing = find_memory_by_title_or_slug(norm_title, cat_clean)
    if not existing and content and content.strip():
        content_hash = compute_string_hash(content)
        existing = find_memory_by_content_hash(content_hash)
        if existing:
            logger.info(
                f"Deduplication: Content hash '{content_hash[:8]}...' matches existing memory "
                f"'{existing['id']}' ({existing['title']}). Routing to existing memory."
            )

    if existing:
        return handle_existing_memory(
            existing=existing,
            norm_title=norm_title,
            content=content,
            action_clean=action_clean,
            category=cat_clean,
            tags=tags,
        )

    return handle_new_memory(
        norm_title=norm_title,
        content=content,
        category=cat_clean,
        tags=tags,
        memory_id=memory_id,
    )


def execute_revert_memory(
    memory_id: str,
    version_number: Optional[int] = None,
) -> dict:
    """
    Reverts a memory back to a previous version snapshot from version control history.
    Updates disk Markdown file, SQLite DB index, and ChromaDB vector store embeddings.
    """
    existing = get_memory_by_id(memory_id)
    if not existing:
        return {"status": "error", "message": f"Memory with ID '{memory_id}' not found."}

    history = db_get_versions(memory_id)
    if not history:
        return {
            "status": "error",
            "message": f"No version history available for memory '{memory_id}'.",
        }

    if version_number is None:
        # Revert to the most recent saved version snapshot
        target_ver = history[0]
    else:
        target_ver = db_get_version_by_number(memory_id, version_number)
        if not target_ver:
            avail = [h["version_number"] for h in history]
            return {
                "status": "error",
                "message": f"Version {version_number} not found for memory '{memory_id}'. Available versions: {avail}",
            }

    # Snapshot current state before reverting so state isn't lost
    create_version_snapshot(memory_id)

    target_id = existing["id"]
    file_path = Path(existing["file_path"])
    restored_title = target_ver["title"]
    restored_category = target_ver["category"]
    restored_tags = target_ver["tags"]
    restored_content = target_ver["content"]
    content_hash = target_ver.get("content_hash") or compute_string_hash(restored_content)

    updated_path = create_markdown_file(
        memory_id=target_id,
        title=restored_title,
        category=restored_category,
        tags=restored_tags,
        content=restored_content,
        content_hash=content_hash,
        created_at=existing.get("created_at"),
        file_path=file_path,
        overwrite=True,
    )

    chunks, chunk_ids = reindex_memory_chunks(target_id, restored_content)

    memory_entry = {
        "id": target_id,
        "title": restored_title,
        "category": restored_category,
        "tags": restored_tags,
        "file_path": str(updated_path),
        "content": restored_content,
        "content_hash": content_hash,
        "created_at": existing.get("created_at"),
        "chunk_ids": chunk_ids,
    }
    upsert_memory_index(memory_entry)

    return {
        "status": "success",
        "action": "revert",
        "memory_id": target_id,
        "restored_version": target_ver["version_number"],
        "title": restored_title,
        "category": restored_category,
        "file_path": str(updated_path),
        "message": f"Memory '{target_id}' successfully reverted to version {target_ver['version_number']}.",
    }


def auto_organize_note(
    content: str,
    title: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """
    Uses the managed LLM client to analyze raw note content and return:
    - title: auto-generated concise title (if missing or provided as default)
    - category: selected category from system categories
    - tags: list of extracted keywords/tags
    - summary: short summary of the note
    - organized_content: clean, nicely structured markdown note
    """
    import json
    from classification.classifier import classify_memory
    from utils import get_available_categories
    from utils.llm_client import generate_llm_response

    if not content or not content.strip():
        return {
            "status": "error",
            "message": "Content cannot be empty.",
        }

    available_categories = get_available_categories()
    
    # Run classification first to get accurate baseline category & tags
    class_res = classify_memory(content)
    fallback_cat = class_res.get("category", "personal")
    fallback_tags = class_res.get("tags", [])

    prompt = f"""You are an intelligent note organizer and memory manager assistant.
Analyze the following raw note content and refine it into a structured, clean note.

Input Content:
"{content}"

User Provided Title (if any): "{title or ''}"

Available System Categories: {available_categories}

INSTRUCTIONS:
1. Title: If the user provided a meaningful title, refine it or keep it. If not, generate a short, descriptive 3-6 word title.
2. Category: Select the best fitting category strictly from Available System Categories.
3. Tags: Provide 3-5 concise, relevant tags (lowercase, single-word or snake_case).
4. Summary: Provide a 1-2 sentence executive summary of the note.
5. Organized Content: Clean up formatting, fix typos, organize with bullet points or markdown headings where appropriate, while retaining all factual details.

Return ONLY a valid JSON object matching this structure:
{{
  "title": "Clean Descriptive Title",
  "category": "one_of_allowed_categories",
  "tags": ["tag1", "tag2"],
  "summary": "1-2 sentence summary of note",
  "organized_content": "Full markdown cleaned text"
}}
"""

    try:
        raw_res = generate_llm_response(
            prompt=prompt,
            system_prompt="You are a JSON formatting note organizing assistant. Output valid JSON only.",
            model=model,
            temperature=0.2,
        )
        clean_resp = raw_res.strip()
        if clean_resp.startswith("```"):
            clean_resp = clean_resp.split("```")[1]
            if clean_resp.startswith("json"):
                clean_resp = clean_resp[4:]
        clean_resp = clean_resp.strip()

        data = json.loads(clean_resp)
        cat = str(data.get("category", fallback_cat)).strip().lower()
        if cat not in available_categories:
            cat = fallback_cat

        gen_title = str(data.get("title") or title or "Untitled Note").strip()
        tags = [str(t).strip().lower() for t in data.get("tags", fallback_tags)]
        summary = str(data.get("summary", "")).strip()
        org_content = str(data.get("organized_content") or content).strip()

        return {
            "status": "success",
            "title": gen_title,
            "category": cat,
            "tags": tags,
            "summary": summary,
            "organized_content": org_content,
        }
    except Exception as e:
        logger.warning(f"LLM auto-organize failed ({e}). Returning baseline classification.")
        first_line = content.strip().split("\n")[0][:40]
        gen_title = title if (title and title.strip()) else (first_line or "Untitled Note")
        return {
            "status": "success",
            "title": gen_title,
            "category": fallback_cat,
            "tags": fallback_tags,
            "summary": first_line,
            "organized_content": content,
            "note": "Baseline organize applied (LLM unavailable).",
        }


def generate_auto_suggestions(
    content: str,
    title: str = "",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates intelligent completion & key point auto-suggestions for notes using active LLM model.
    """
    from utils.llm_client import generate_llm_response, get_active_model

    if not content or not content.strip():
        return {
            "status": "error",
            "message": "Content cannot be empty for auto-suggestion.",
        }

    chosen_model = model or get_active_model()

    prompt = f"""You are an AI Copilot for intelligent note-taking.
Analyze the user's current note draft and generate 2-4 concise bullet points suggesting logical next sections, key insights, or action items.

Title: {title}
Current Content:
"{content}"

FORMAT REQUIREMENTS:
- Provide clean, direct bullet points or markdown items only.
- Do NOT repeat the existing content.
- Keep output concise (max 3-4 bullet points).
"""

    try:
        suggestion_text = generate_llm_response(
            prompt=prompt,
            system_prompt="You are a helpful, concise AI writing copilot.",
            model=chosen_model,
            temperature=0.3,
        )
        return {
            "status": "success",
            "model": chosen_model,
            "suggestion": suggestion_text.strip(),
        }
    except Exception as e:
        logger.error(f"Auto-suggestion failed with model '{chosen_model}': {e}")
        return {
            "status": "error",
            "message": str(e),
            "suggestion": "- Review key concepts\n- Verify storage synchronization",
        }



