from pathlib import Path
from typing import Any, Dict, List, Optional

from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from storage.db_manager import (
    delete_memory_from_index,
    find_memory_by_title_or_slug,
    get_memory_by_id,
    upsert_memory_index,
)
from storage.markdown_handler import (
    append_to_markdown_file,
    create_markdown_file,
    delete_markdown_file,
    normalize_title,
)
from vector.chunker import chunk_text
from vector.embedder import generate_local_embeddings
from vector.vector_db import add_chunks_to_vector_db, delete_chunks_by_memory_id


def reindex_memory_chunks(memory_id: str, content: str) -> tuple[list, list]:
    """
    Deletes existing vector chunks, generates new chunks + embeddings, and adds them to ChromaDB.
    Returns tuple of (chunks, chunk_ids).
    """
    delete_chunks_by_memory_id(memory_id)
    chunks = chunk_text(memory_id, content)
    chunk_ids = []

    if chunks:
        chunk_texts = [c.get("text") or c.get("content", "") for c in chunks]
        embeddings = generate_local_embeddings(chunk_texts)
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
    Handles updating or appending to an existing memory file and re-indexing vector chunks.
    """
    target_id = existing["id"]
    file_path = Path(existing["file_path"])

    if action_clean in ("append", "auto"):
        updated_path, target_id, full_content = append_to_markdown_file(
            file_path=file_path,
            additional_content=content,
            tags=tags,
        )
        content_hash = compute_string_hash(full_content)
        actual_action = "append"
    else:  # update
        combined_tags = list(set(existing.get("tags", []) + tags))
        content_hash = compute_string_hash(content)
        updated_path = create_markdown_file(
            memory_id=target_id,
            title=norm_title,
            category=category,
            tags=combined_tags,
            content=content,
            content_hash=content_hash,
            created_at=existing.get("created_at"),
            file_path=file_path,
            overwrite=True,
        )
        full_content = content
        actual_action = "update"

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
