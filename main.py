from pathlib import Path
import sys
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from classification.classifier import classify_memory
from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from search.relevance_scorer import search_hybrid_relevance
from storage.index_manager import (
    add_category_to_index,
    add_memory_to_index,
    delete_category_from_index,
    load_index,
    save_index,
)
from storage.markdown_handler import (
    create_markdown_file,
    delete_markdown_file,
    read_markdown_file,
)
from storage.sync_manager import (
    _remove_memory_from_index_dict,
    clear_all_memories as sync_clear_all_memories,
    get_memory_file_status as sync_get_memory_file_status,
    start_background_watcher,
    sync_markdown_files as sync_scan_markdown_files,
)
from utils import get_available_categories
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
def store_memory(
    title: str,
    content: str,
    category: str = "personal",
    tags: List[str] = None,
) -> dict:
    """
    Full end-to-end memory pipeline:
    Generates a unique Memory ID, creates Markdown storage file on disk,
    chunks text, generates vector embeddings, upserts chunks to ChromaDB,
    and records metadata in data/index.json.
    """
    if tags is None:
        tags = []

    memory_id = generate_memory_id()
    content_hash = compute_string_hash(content)

    # 1. Create Markdown file on disk
    file_path = create_markdown_file(
        memory_id=memory_id,
        title=title,
        category=category,
        tags=tags,
        content=content,
        content_hash=content_hash,
    )

    # 2. Model-aware text chunking
    chunks = chunk_text(memory_id, content)

    # 3. Generate embeddings & store in ChromaDB
    chunk_ids = []
    if chunks:
        chunk_texts = [c["content"] for c in chunks]
        embeddings = generate_local_embeddings(chunk_texts)
        add_chunks_to_vector_db(chunks, embeddings)
        chunk_ids = [c["id"] for c in chunks]

    # 4. Save metadata to index.json
    memory_entry = {
        "id": memory_id,
        "title": title,
        "category": category,
        "tags": tags,
        "file_path": str(file_path),
        "content": content,
        "content_hash": content_hash,
        "chunk_ids": chunk_ids,
    }

    add_memory_to_index(memory_entry)

    return {
        "status": "success",
        "memory_id": memory_id,
        "title": title,
        "category": category,
        "tags": tags,
        "file_path": str(file_path),
        "chunk_count": len(chunks),
    }


@mcp.tool()
def read_memory(memory_id: str) -> dict:
    """
    Fetches frontmatter metadata, tags, and full content for a given Memory ID.
    """
    index_data = load_index()
    target_mem = None

    for m in index_data.get("memories", []):
        if m["id"] == memory_id:
            target_mem = m
            break

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
    Deletes a memory across Markdown disk storage, index.json, and ChromaDB vector store.
    """
    index_data = load_index()
    target_mem = None

    for m in index_data.get("memories", []):
        if m["id"] == memory_id:
            target_mem = m
            break

    if not target_mem:
        return {"status": "error", "message": f"Memory with ID '{memory_id}' not found."}

    # 1. Delete Markdown file
    file_path = target_mem.get("file_path")
    if file_path:
        delete_markdown_file(file_path)

    # 2. Delete ChromaDB vector chunks
    delete_chunks_by_memory_id(memory_id)

    # 3. Remove from index.json
    _remove_memory_from_index_dict(index_data, memory_id)
    save_index(index_data)

    return {
        "status": "success",
        "message": f"Memory '{memory_id}' deleted successfully from disk, index.json, and ChromaDB.",
    }


@mcp.tool()
def clear_all_memories() -> dict:
    """
    Completely purges all memories from disk, resets data/index.json,
    and clears ChromaDB vector database store.
    """
    return sync_clear_all_memories()


@mcp.tool()
def list_memories(
    category_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
) -> dict:
    """
    Lists stored memories with optional filtering by category or tag.
    """
    index_data = load_index()
    memories = index_data.get("memories", [])

    if category_filter:
        cat_lower = category_filter.strip().lower()
        memories = [m for m in memories if m.get("category", "").lower() == cat_lower]

    if tag_filter:
        tag_lower = tag_filter.strip().lower()
        memories = [m for m in memories if any(t.lower() == tag_lower for t in m.get("tags", []))]

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
    automatically chunking, embedding, and updating index.json + ChromaDB.
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
    Analyzes raw text, automatically assigns a category (creating new ones dynamically if needed),
    and extracts relevant tags.
    """
    return classify_memory(text=text)


# ==========================================
# 📁 3. Category & Model Tools
# ==========================================

@mcp.tool()
def get_categories() -> dict:
    """
    Returns all currently available memory categories on disk and in index.json.
    """
    return {"status": "success", "categories": get_available_categories()}


@mcp.tool()
def add_category(category: str) -> dict:
    """
    Dynamically registers a new category in index.json and creates its storage directory.
    """
    return add_category_to_index(category=category)


@mcp.tool()
def delete_category(category: str) -> dict:
    """
    Deletes a category from index.json and removes its directory on disk.
    """
    return delete_category_from_index(category=category)


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
    # Start background file watcher for Markdown directory
    start_background_watcher()
    # Initial scan/sync on launch
    sync_scan_markdown_files()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
