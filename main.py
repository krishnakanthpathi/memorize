from pathlib import Path
import sys
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from classification.classifier import classify_memory
from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from search.relevance_scorer import search_hybrid_relevance
from storage.db_manager import (
    delete_memory_from_index,
    find_memory_by_title_or_slug,
    get_all_memories,
    get_memory_by_id,
    init_db,
    upsert_memory_index,
)
from storage.markdown_handler import (
    append_to_markdown_file,
    create_markdown_file,
    delete_markdown_file,
    normalize_title,
    read_markdown_file,
    title_to_slug,
)
from storage.sync_manager import (
    clear_all_memories as sync_clear_all_memories,
    get_memory_file_status as sync_get_memory_file_status,
    start_background_watcher,
    sync_markdown_files as sync_scan_markdown_files,
)
from utils import get_available_categories, get_category_dir
from utils.model_fetcher import fetch_and_bifurcate_models
from vector.chunker import chunk_text
from vector.embedder import generate_local_embeddings
from vector.vector_db import (
    add_chunks_to_vector_db,
    delete_chunks_by_memory_id,
    peek_vector_db,
)

# Initialize FastMCP Server
mcp = FastMCP("Memorize Server")


# ==========================================
# 🟢 1. Core End-to-End Memory Pipeline
# ==========================================

@mcp.tool()
def upsert_memory(
    title: str,
    content: str = "",
    action: str = "auto",  # 'auto' | 'insert' | 'update' | 'append' | 'delete'
    category: str = "personal",
    tags: List[str] = None,
    memory_id: Optional[str] = None,
) -> dict:
    """
    Unified memory lifecycle tool to Insert, Update, Append, or Delete memories.
    Normalizes title strings, prevents filename duplication, and appends to existing files seamlessly.
    """
    if tags is None:
        tags = []

    norm_title = normalize_title(title)
    cat_clean = category.strip().lower() if category else "personal"
    action_clean = action.strip().lower()

    # 1. Handle DELETE action
    if action_clean == "delete":
        target = None
        if memory_id:
            target = get_memory_by_id(memory_id)
        if not target and norm_title:
            target = find_memory_by_title_or_slug(norm_title, cat_clean)

        if not target:
            return {"status": "error", "message": f"Memory not found for deletion."}

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

    # 2. Check if target memory already exists
    existing = None
    if memory_id:
        existing = get_memory_by_id(memory_id)
    if not existing and norm_title:
        existing = find_memory_by_title_or_slug(norm_title, cat_clean)

    # 3. Process AUTO / INSERT / UPDATE / APPEND
    if existing:
        target_id = existing["id"]
        file_path = Path(existing["file_path"])

        if action_clean in ("append", "auto"):
            # APPEND to existing memory
            updated_path, target_id, full_content = append_to_markdown_file(
                file_path=file_path,
                additional_content=content,
                tags=tags,
            )
            content_hash = compute_string_hash(full_content)
            actual_action = "append"
        else:  # update
            # OVERWRITE existing memory
            combined_tags = list(set(existing.get("tags", []) + tags))
            content_hash = compute_string_hash(content)
            updated_path = create_markdown_file(
                memory_id=target_id,
                title=norm_title,
                category=cat_clean,
                tags=combined_tags,
                content=content,
                content_hash=content_hash,
                created_at=existing.get("created_at"),
                file_path=file_path,
                overwrite=True,
            )
            full_content = content
            actual_action = "update"

        # Re-chunk and re-embed in ChromaDB
        delete_chunks_by_memory_id(target_id)
        chunks = chunk_text(target_id, full_content)
        chunk_ids = []
        if chunks:
            chunk_texts = [c.get("text") or c.get("content", "") for c in chunks]
            embeddings = generate_local_embeddings(chunk_texts)
            add_chunks_to_vector_db(chunks, embeddings)
            chunk_ids = [c.get("chunk_id") or c.get("id", "") for c in chunks]

        memory_entry = {
            "id": target_id,
            "title": norm_title,
            "category": cat_clean,
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
            "category": cat_clean,
            "file_path": str(updated_path),
            "chunk_count": len(chunks),
        }

    # 4. Create NEW memory (Insert)
    new_id = memory_id if memory_id else generate_memory_id()
    content_hash = compute_string_hash(content)

    new_file_path = create_markdown_file(
        memory_id=new_id,
        title=norm_title,
        category=cat_clean,
        tags=tags,
        content=content,
        content_hash=content_hash,
        overwrite=False,
    )

    chunks = chunk_text(new_id, content)
    chunk_ids = []
    if chunks:
        chunk_texts = [c.get("text") or c.get("content", "") for c in chunks]
        embeddings = generate_local_embeddings(chunk_texts)
        add_chunks_to_vector_db(chunks, embeddings)
        chunk_ids = [c.get("chunk_id") or c.get("id", "") for c in chunks]

    memory_entry = {
        "id": new_id,
        "title": norm_title,
        "category": cat_clean,
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
        "category": cat_clean,
        "tags": tags,
        "file_path": str(new_file_path),
        "chunk_count": len(chunks),
    }


@mcp.tool()
def store_memory(
    title: str,
    content: str,
    category: str = "personal",
    tags: List[str] = None,
) -> dict:
    """
    Stores memory into system. Automatically updates/appends if topic already exists.
    """
    return upsert_memory(
        title=title,
        content=content,
        action="auto",
        category=category,
        tags=tags,
    )


@mcp.tool()
def read_memory(memory_id: str) -> dict:
    """
    Fetches frontmatter metadata, tags, and full content for a given Memory ID.
    """
    target_mem = get_memory_by_id(memory_id)

    if not target_mem:
        return {"status": "error", "message": f"Memory with ID '{memory_id}' not found."}

    file_path = target_mem.get("file_path", "")
    read_result = read_markdown_file(file_path)

    if isinstance(read_result, dict) and read_result.get("status") == "error":
        return read_result

    frontmatter, content = read_result
    return {
        "status": "success",
        "memory_id": memory_id,
        "title": target_mem.get("title"),
        "category": target_mem.get("category"),
        "tags": target_mem.get("tags", []),
        "file_path": file_path,
        "frontmatter": frontmatter,
        "content": content,
        "created_at": target_mem.get("created_at"),
        "updated_at": target_mem.get("updated_at"),
    }


@mcp.tool()
def delete_memory(memory_id: str) -> dict:
    """
    Deletes a memory across Markdown disk storage, SQLite database, and ChromaDB vector store.
    """
    return upsert_memory(title="", memory_id=memory_id, action="delete")


@mcp.tool()
def clear_all_memories() -> dict:
    """
    Completely purges all memories from disk, resets SQLite database,
    and clears ChromaDB vector database store.
    """
    return sync_clear_all_memories()


@mcp.tool()
def list_memories(
    category_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
) -> dict:
    """
    Lists stored memories from SQLite with optional filtering by category or tag.
    """
    memories = get_all_memories(category_filter=category_filter, tag_filter=tag_filter)
    return {
        "status": "success",
        "total_count": len(memories),
        "memories": memories,
    }


@mcp.tool()
def get_memory_file_status(memory_id_or_path: str) -> dict:
    """
    Checks and returns the exact status of a Markdown file (existence, full text,
    frontmatter metadata, estimated tokens, content hash, and sync state).
    """
    return sync_get_memory_file_status(memory_id_or_path)


@mcp.tool()
def sync_markdown_files() -> dict:
    """
    Scans data/memories/ for Markdown files added, updated, or deleted on disk,
    automatically chunking, embedding, and updating SQLite + ChromaDB.
    """
    return sync_scan_markdown_files()


# ==========================================
# 🔍 2. Intelligence & Search Engine
# ==========================================

@mcp.tool()
def hybrid_search_memories(
    query: str,
    category_filter: Optional[str] = None,
    top_k: int = 5,
) -> List[dict]:
    """
    Performs hybrid weighted relevance search combining Vector Similarity (50%),
    Tag Match (30%), and Category Match (20%) to return ranked top memories.
    """
    return search_hybrid_relevance(
        query=query,
        category_filter=category_filter if category_filter else None,
        top_k=top_k,
    )


@mcp.tool()
def auto_classify_memory(text: str) -> dict:
    """
    Analyzes raw text, automatically assigns a category, and extracts relevant tags.
    """
    return classify_memory(text=text)


# ==========================================
# 📁 3. Category & Model Tools
# ==========================================

@mcp.tool()
def get_categories() -> dict:
    """
    Returns all currently available memory categories on disk.
    """
    return {"status": "success", "categories": get_available_categories()}


@mcp.tool()
def add_category(category: str) -> dict:
    """
    Dynamically creates category storage directory.
    """
    cat_dir = get_category_dir(category)
    return {"status": "success", "category": category, "path": str(cat_dir)}


@mcp.tool()
def delete_category(category: str) -> dict:
    """
    Deletes a category directory on disk and purges category records from SQLite.
    """
    cat_dir = get_category_dir(category)
    import shutil
    if cat_dir.exists():
        shutil.rmtree(cat_dir)
    return {"status": "success", "category": category}


@mcp.tool()
def peek_vector_db_chunks(limit: int = 10) -> dict:
    """
    Inspects stored vector chunks in ChromaDB.
    """
    return peek_vector_db(limit=limit)


@mcp.tool()
def list_available_models(
    base_url: str = "",
    api_key: str = "",
) -> dict:
    """
    Fetches available models and bifurcates into embedding vs generative models.
    """
    return fetch_and_bifurcate_models(
        base_url=base_url if base_url else None,
        api_key=api_key if api_key else None,
    )


def main():
    sys.stderr.write("Started Memorize MCP Server\n")
    init_db()
    # Start background file watcher for Markdown directory
    start_background_watcher()
    # Initial scan/sync on launch
    sync_scan_markdown_files()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
