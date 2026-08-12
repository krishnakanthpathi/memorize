from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from config.constants import MEMORIES_DIR
from core.hashing import compute_string_hash
from core.logger import handle_errors, logger
from storage.backup_manager import clear_all_backups
from storage.db_manager import (
    clear_all_index_memories,
    get_memory_by_id,
)
from storage.markdown_handler import read_markdown_file
from vector.vector_db import get_chroma_client


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

