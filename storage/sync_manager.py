from datetime import datetime, timezone
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Union

from config.constants import MEMORIES_DIR
from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from core.logger import handle_errors, logger
from storage.backup_manager import (
    backup_all_memories,
    backup_single_memory_file,
    clear_all_backups,
    delete_single_backup_file,
    restore_memories_from_backup,
)
from storage.db_manager import (
    clear_all_index_memories,
    delete_memory_from_index,
    get_all_memories,
    get_memory_by_id,
    init_db,
    upsert_memory_index,
)
from storage.markdown_handler import (
    create_markdown_file,
    delete_markdown_file,
    read_markdown_file,
)
from utils import get_available_categories
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
    1. Restores any missing .md files from data/backups/memories/ if necessary.
    2. Detects new or updated .md files -> parses YAML frontmatter, auto-chunks, auto-embeds, creates backup, and updates SQLite + ChromaDB.
    3. Assigns missing memory_id to files created directly on disk.
    4. Detects deleted files -> purges corresponding memory entries from SQLite and ChromaDB.
    """
    if not MEMORIES_DIR.exists():
        MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

    # First, restore any missing memory files from backup store
    restore_memories_from_backup()

    init_db()
    existing_memories = {m["id"]: m for m in get_all_memories()}

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
                    file_path=full_path,
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
            existing = existing_memories.get(memory_id)
            if existing and existing.get("content_hash") == content_hash and existing.get("file_path") == str(full_path):
                continue  # Content & path unchanged

            # Content is new or modified -> re-chunk & embed
            delete_chunks_by_memory_id(memory_id)

            if existing:
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

            upsert_memory_index(memory_entry)
            existing_memories[memory_id] = memory_entry

    # Auto-rematerialize missing files from SQLite database instead of purging
    all_indexed_memories = get_all_memories()
    rematerialized_count = 0
    for mem in all_indexed_memories:
        mem_id = mem["id"]
        file_path_str = mem.get("file_path", "")
        db_content = mem.get("content")

        if mem_id not in found_memory_ids and (not file_path_str or not Path(file_path_str).exists()):
            if db_content:
                # Re-materialize file on disk from SQLite database content
                title = mem.get("title", "Untitled Memory")
                category = mem.get("category", "personal")
                tags = mem.get("tags", [])
                target_path = Path(file_path_str) if file_path_str else MEMORIES_DIR / category / f"{mem_id}.md"

                create_markdown_file(
                    memory_id=mem_id,
                    title=title,
                    category=category,
                    tags=tags,
                    content=db_content,
                    created_at=mem.get("created_at", ""),
                    updated_at=mem.get("updated_at", ""),
                    file_path=target_path,
                    overwrite=True,
                )
                rematerialized_count += 1
                found_memory_ids.add(mem_id)
                logger.info(f"Auto-rematerialized missing memory file from SQLite DB: '{title}' -> {target_path}")
            else:
                delete_chunks_by_memory_id(mem_id)
                delete_memory_from_index(mem_id)
                deleted_count += 1

    # Keep backup repository & README snapshot updated
    backup_all_memories()

    total_count = len(get_all_memories())

    return {
        "status": "success",
        "added": added_count,
        "updated": updated_count,
        "deleted": deleted_count,
        "rematerialized": rematerialized_count,
        "total_memories": total_count,
    }



@handle_errors
def clear_all_memories(clear_backups: bool = True) -> Dict[str, Any]:
    """
    Completely purges all memory Markdown files and directories in MEMORIES_DIR,
    re-initializes standard category folders, resets SQLite DB,
    clears ChromaDB vector store collection, and purges backups if clear_backups is True.
    """
    import shutil
    from config.constants import DEFAULT_CATEGORIES

    deleted_files = 0
    if MEMORIES_DIR.exists():
        for item in MEMORIES_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted_files += 1
            except Exception as e:
                logger.error(f"Error removing {item}: {e}")

    if clear_backups:
        clear_all_backups()

    # Re-initialize standard category subdirectories with .gitkeep
    for cat in DEFAULT_CATEGORIES:
        cat_dir = MEMORIES_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        gitkeep = cat_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    # Reset SQLite database
    clear_all_index_memories()

    # Clear ChromaDB vector database collection
    try:
        client = get_chroma_client()
        try:
            client.delete_collection(name="memories")
        except Exception:
            pass
        client.get_or_create_collection(name="memories")
    except Exception as e:
        logger.warning(f"Error resetting ChromaDB collection: {e}")

    return {
        "status": "success",
        "message": f"Successfully cleared memories directory, reset SQLite database, and purged ChromaDB vector store.",
        "deleted_files_count": deleted_files,
    }


@handle_errors
def get_memory_file_status(memory_id_or_path: str) -> Dict[str, Any]:
    """
    Finds a Markdown file by Memory ID or filepath and returns its exact status,
    parsed frontmatter, raw text, content hash, token count estimate, and sync status.
    """
    target_mem = get_memory_by_id(memory_id_or_path)

    target_path = None
    if target_mem:
        target_path = Path(target_mem["file_path"])
    else:
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
        "is_indexed": target_mem is not None and target_mem.get("content_hash") == content_hash,
        "frontmatter": frontmatter,
        "content": content,
        "raw_file_text": raw_text,
    }


# Watchdog Observer Class
_watcher_observer: Optional[Any] = None


class MarkdownFileEventHandler(FileSystemEventHandler if HAS_WATCHDOG else object):
    """Handles file system events for .md files in data/memories/."""

    def __init__(self, debounce_seconds: float = 1.0):
        if HAS_WATCHDOG:
            super().__init__()
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
