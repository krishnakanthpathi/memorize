from datetime import datetime, timezone
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Union

from config.constants import INDEX_PATH, MEMORIES_DIR
from core.hashing import compute_string_hash
from core.id_generator import generate_chunk_id, generate_memory_id
from core.logger import handle_errors, logger
from storage.index_manager import (
    add_memory_to_index,
    get_initial_index_structure,
    load_index,
    save_index,
)
from storage.markdown_handler import (
    create_markdown_file,
    delete_markdown_file,
    read_markdown_file,
)
from utils import get_available_categories, get_category_dir
from vector.chunker import chunk_text
from vector.embedder import generate_local_embeddings
from vector.vector_db import (
    add_chunks_to_vector_db,
    delete_chunks_by_memory_id,
    get_chroma_client,
)

# Watchdog imports
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


@handle_errors
def sync_markdown_files() -> Dict[str, Any]:
    """
    Scans data/memories/ recursively.
    1. Detects new or updated .md files -> parses YAML frontmatter, auto-chunks, auto-embeds, and updates index.json + ChromaDB.
    2. Assigns missing memory_id to files created directly on disk.
    3. Detects deleted files -> purges corresponding memory entries from index.json and ChromaDB.
    """
    if not MEMORIES_DIR.exists():
        MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

    index_data = load_index()
    existing_memories_by_id = {m["id"]: m for m in index_data.get("memories", [])}

    updated_count = 0
    added_count = 0
    deleted_count = 0

    found_file_paths = set()
    found_memory_ids = set()

    # Iterate over all .md files in memories directory
    for root, _, files in os.walk(MEMORIES_DIR):
        for file in files:
            if not file.endswith(".md") or file.startswith("."):
                continue

            full_path = Path(root) / file
            found_file_paths.add(str(full_path))

            read_result = read_markdown_file(full_path)
            if isinstance(read_result, dict) and read_result.get("status") == "error":
                continue

            frontmatter, content = read_result
            memory_id = frontmatter.get("id")

            # Determine category from folder name if possible
            category = frontmatter.get("category")
            if not category:
                rel_dir = full_path.parent.name
                category = rel_dir if rel_dir in get_available_categories() else "personal"

            # Auto-assign memory_id if created manually on disk without YAML frontmatter id
            if not memory_id:
                memory_id = generate_memory_id()
                title = frontmatter.get("title", full_path.stem.replace("_", " ").title())
                tags = frontmatter.get("tags", [])
                create_markdown_file(
                    memory_id=memory_id,
                    title=title,
                    category=category,
                    tags=tags,
                    content=content,
                )
                # Re-read to get updated YAML block
                frontmatter, content = read_markdown_file(full_path)

            found_memory_ids.add(memory_id)
            title = frontmatter.get("title", full_path.stem.replace("_", " ").title())
            tags = frontmatter.get("tags", [])
            content_hash = compute_string_hash(content)
            created_at = frontmatter.get("created_at", datetime.now(timezone.utc).isoformat())
            updated_at = frontmatter.get("updated_at", datetime.now(timezone.utc).isoformat())

            # Check if memory already indexed and unchanged
            existing = existing_memories_by_id.get(memory_id)
            if existing and existing.get("content_hash") == content_hash:
                continue  # Content unchanged

            # Content is new or modified -> re-chunk & embed
            delete_chunks_by_memory_id(memory_id)

            # Remove old memory record from index if modifying
            if existing:
                _remove_memory_from_index_dict(index_data, memory_id)
                updated_count += 1
            else:
                added_count += 1

            # Chunk text
            chunks = chunk_text(memory_id, content)

            # Embed chunks
            if chunks:
                chunk_texts = [c.get("text") or c.get("content", "") for c in chunks]
                embeddings = generate_local_embeddings(chunk_texts)
                add_chunks_to_vector_db(chunks, embeddings)

            chunk_ids = [c.get("chunk_id") or c.get("id") for c in chunks]


            memory_entry = {
                "id": memory_id,
                "title": title,
                "category": category,
                "tags": tags,
                "file_path": str(full_path),
                "content": content,
                "content_hash": content_hash,
                "created_at": created_at,
                "updated_at": updated_at,
                "chunk_ids": chunk_ids,
            }

            index_data = add_memory_to_index(memory_entry)
            existing_memories_by_id[memory_id] = memory_entry

    # Detect deleted files (present in index.json but missing from disk)
    all_indexed_memories = list(index_data.get("memories", []))
    for mem in all_indexed_memories:
        mem_id = mem["id"]
        file_path_str = mem.get("file_path", "")
        if mem_id not in found_memory_ids and (not file_path_str or not Path(file_path_str).exists()):
            delete_chunks_by_memory_id(mem_id)
            _remove_memory_from_index_dict(index_data, mem_id)
            deleted_count += 1

    save_index(index_data)

    return {
        "status": "success",
        "added": added_count,
        "updated": updated_count,
        "deleted": deleted_count,
        "total_memories": index_data.get("total_memories", 0),
    }


def _remove_memory_from_index_dict(index_data: Dict[str, Any], memory_id: str):
    """Internal helper to strip a memory record and its tag references from index_data."""
    memories = index_data.get("memories", [])
    target = None
    for m in memories:
        if m["id"] == memory_id:
            target = m
            break

    if not target:
        return

    memories.remove(target)
    index_data["total_memories"] = len(memories)

    # Decrement category count
    cat = target.get("category", "").lower()
    if cat in index_data.get("categories", {}):
        index_data["categories"][cat]["count"] = max(0, index_data["categories"][cat]["count"] - 1)

    # Clean reverse tag_index
    tag_index = index_data.get("tag_index", {})
    for term, id_list in list(tag_index.items()):
        if memory_id in id_list:
            id_list.remove(memory_id)
            if not id_list:
                del tag_index[term]


@handle_errors
def clear_all_memories() -> Dict[str, Any]:
    """
    Completely purges all memory Markdown files, resets data/index.json,
    and clears ChromaDB vector store collection.
    """
    deleted_files = 0
    if MEMORIES_DIR.exists():
        for root, _, files in os.walk(MEMORIES_DIR):
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    try:
                        full_path.unlink()
                        deleted_files += 1
                    except Exception as e:
                        logger.error(f"Error removing {full_path}: {e}")

    # Re-initialize category subdirectories
    for cat in get_available_categories():
        get_category_dir(cat)

    # Reset index.json
    fresh_index = get_initial_index_structure()
    save_index(fresh_index)

    # Clear ChromaDB vector database collection
    try:
        client = get_chroma_client()
        client.delete_collection(name="memories")
        client.get_or_create_collection(name="memories")
    except Exception as e:
        logger.warning(f"Error resetting ChromaDB collection: {e}")

    return {
        "status": "success",
        "message": f"Successfully cleared {deleted_files} markdown files, reset index.json, and purged ChromaDB vector store.",
        "deleted_files_count": deleted_files,
    }


@handle_errors
def get_memory_file_status(memory_id_or_path: str) -> Dict[str, Any]:
    """
    Finds a Markdown file by Memory ID or filepath and returns its exact status,
    parsed frontmatter, raw text, content hash, token count estimate, and sync status.
    """
    index_data = load_index()
    target_mem = None

    for m in index_data.get("memories", []):
        if m["id"] == memory_id_or_path or m.get("file_path") == memory_id_or_path:
            target_mem = m
            break

    target_path = None
    if target_mem:
        target_path = Path(target_mem["file_path"])
    else:
        # Check if memory_id_or_path is a path
        path_candidate = Path(memory_id_or_path)
        if path_candidate.exists():
            target_path = path_candidate

    if not target_path or not target_path.exists():
        return {
            "status": "error",
            "message": f"Memory file or ID '{memory_id_or_path}' not found.",
            "exists": False,
        }

    frontmatter, content = read_markdown_file(target_path)
    content_hash = compute_string_hash(content)
    stat = target_path.stat()

    with open(target_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Estimate token count (~4 chars per token)
    est_tokens = len(content) // 4

    return {
        "status": "success",
        "exists": True,
        "file_path": str(target_path),
        "file_size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "memory_id": frontmatter.get("id", target_mem.get("id") if target_mem else None),
        "title": frontmatter.get("title", target_mem.get("title") if target_mem else target_path.stem),
        "category": frontmatter.get("category", target_mem.get("category") if target_mem else None),
        "tags": frontmatter.get("tags", target_mem.get("tags") if target_mem else []),
        "created_at": frontmatter.get("created_at"),
        "updated_at": frontmatter.get("updated_at"),
        "content_hash": content_hash,
        "estimated_tokens": est_tokens,
        "chunk_count": len(target_mem.get("chunk_ids", [])) if target_mem else 0,
        "is_indexed": target_mem is not None and target_mem.get("content_hash") == content_hash,
        "frontmatter": frontmatter,
        "content": content,
        "raw_file_text": raw_text,
    }


# Watchdog Observer Class
_watcher_observer: Optional[Any] = None


class MarkdownFileEventHandler:
    """Handles file system events for .md files in data/memories/."""

    def __init__(self, debounce_seconds: float = 1.0):
        self.debounce_seconds = debounce_seconds
        self._last_sync_time = 0.0

    def dispatch(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        now = time.time()
        if now - self._last_sync_time > self.debounce_seconds:
            self._last_sync_time = now
            logger.info(f"FileSystem event detected ({event.event_type} on {event.src_path}). Triggering sync...")
            sync_markdown_files()


def start_background_watcher():
    """Starts the background file system watcher for data/memories/."""
    global _watcher_observer
    if not HAS_WATCHDOG:
        logger.warning("Watchdog library not installed. Background watcher disabled.")
        return False

    if _watcher_observer and _watcher_observer.is_alive():
        return True

    if not MEMORIES_DIR.exists():
        MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

    handler = MarkdownFileEventHandler()
    observer = Observer()
    observer.schedule(handler, path=str(MEMORIES_DIR), recursive=True)
    observer.daemon = True
    observer.start()
    _watcher_observer = observer
    logger.info(f"Started background Markdown Watcher observing: {MEMORIES_DIR}")
    return True
