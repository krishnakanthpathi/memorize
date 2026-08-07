from pathlib import Path
import sys
from typing import List, Optional, Union

from mcp.server.fastmcp import FastMCP

from classification.classifier import classify_memory
from core.deduplication_service import (
    detect_duplicate_clusters,
    merge_duplicate_memories,
)
from core.memory_service import execute_upsert_memory
from search.relevance_scorer import (
    search_hybrid_relevance,
    search_vector_similarity,
)
from storage.db_manager import (
    get_all_memories,
    get_memory_by_id,
    init_db,
)
from storage.markdown_handler import read_markdown_file
from storage.organization_manager import reorganize_memories
from storage.sync_manager import (
    clear_all_memories as sync_clear_all_memories,
    get_memory_file_status as sync_get_memory_file_status,
    start_background_watcher,
    sync_markdown_files as sync_scan_markdown_files,
)
from utils import get_available_categories, get_category_dir
from utils.model_fetcher import fetch_and_bifurcate_models
from vector.vector_db import peek_vector_db

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
    return execute_upsert_memory(
        title=title,
        content=content,
        action=action,
        category=category,
        tags=tags,
        memory_id=memory_id,
    )


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
def append_memory(
    title: str,
    content: str,
    category: str = "personal",
    tags: List[str] = None,
    memory_id: Optional[str] = None,
) -> dict:
    """
    Helper tool for upsert_memory to explicitly append new content to an existing memory.
    Creates a new memory if no matching title/memory_id is found.
    """
    return upsert_memory(
        title=title,
        content=content,
        action="append",
        category=category,
        tags=tags,
        memory_id=memory_id,
    )


@mcp.tool()
def update_memory(
    title: str,
    content: str,
    category: str = "personal",
    tags: List[str] = None,
    memory_id: Optional[str] = None,
) -> dict:
    """
    Helper tool for upsert_memory to explicitly update/overwrite an existing memory's content.
    """
    return upsert_memory(
        title=title,
        content=content,
        action="update",
        category=category,
        tags=tags,
        memory_id=memory_id,
    )


@mcp.tool()
def smart_upsert_memory(
    title: str,
    content: str = "",
    category: Optional[str] = None,
    tags: List[str] = None,
    action: str = "auto",
) -> dict:
    """
    Smart helper tool for upsert_memory that automatically classifies category and extracts tags
    if they are not provided, before saving.
    """
    if tags is None:
        tags = []

    if not category or not tags:
        full_text = f"{title}\n{content}".strip()
        classification = classify_memory(full_text)
        if not category and classification.get("category"):
            category = classification["category"]
        if not tags and classification.get("tags"):
            tags = classification["tags"]

    return upsert_memory(
        title=title,
        content=content,
        action=action,
        category=category or "personal",
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
) -> Union[List[dict], dict]:
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
def search_memory(
    query: str,
    category_filter: Optional[str] = None,
    top_k: int = 5,
    min_similarity: float = 0.0,
) -> Union[List[dict], dict]:
    """
    Performs pure similarity search using vector embeddings to find and rank memories based on query similarity.
    """
    return search_vector_similarity(
        query=query,
        category_filter=category_filter if category_filter else None,
        top_k=top_k,
        threshold=min_similarity,
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


# ==========================================
# 🧹 4. Organization & Deduplication Tools
# ==========================================

@mcp.tool()
def detect_duplicate_memories(
    category_filter: Optional[str] = None,
    min_similarity: float = 0.40,
) -> dict:
    """
    Scans stored memories for potential duplicate clusters based on pairwise title and content similarity.
    """
    return detect_duplicate_clusters(
        category_filter=category_filter,
        min_similarity=min_similarity,
    )


@mcp.tool()
def merge_duplicate_memories_tool(
    memory_ids: List[str],
    target_title: Optional[str] = None,
    target_category: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> dict:
    """
    Synthesizes and merges multiple duplicate memory documents into a single consolidated master file using an LLM.
    Safely purges secondary duplicate files from Markdown disk, SQLite, and ChromaDB.
    """
    return merge_duplicate_memories(
        memory_ids=memory_ids,
        target_title=target_title,
        target_category=target_category,
        llm_model=llm_model,
    )


@mcp.tool()
def organize_memory_files(auto_fix: bool = True) -> dict:
    """
    Audits and reorganizes memory Markdown files into their correct category folders,
    slugifies filenames, cleans empty directories, and refreshes indexes.
    """
    return reorganize_memories(auto_fix=auto_fix)



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
