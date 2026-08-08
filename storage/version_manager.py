from typing import Any, Dict, List, Optional

from core.hashing import compute_string_hash
from core.logger import handle_errors, logger
from storage.db_manager import (
    db_get_version_by_number,
    db_get_versions,
    db_prune_versions,
    db_save_version,
    get_memory_by_id,
)
from storage.markdown_handler import read_markdown_file

MAX_RETAINED_VERSIONS = 3


@handle_errors
def create_version_snapshot(memory_id: str) -> Optional[Dict[str, Any]]:
    """
    Reads existing memory state (from DB or Markdown file) and creates a version snapshot.
    Ensures that only the last MAX_RETAINED_VERSIONS (3) are retained.
    """
    memory = get_memory_by_id(memory_id)
    if not memory:
        return None

    content = memory.get("content", "")
    file_path = memory.get("file_path", "")

    # Fallback to reading file directly if content in DB is missing
    if not content and file_path:
        try:
            _, content = read_markdown_file(file_path)
        except Exception as e:
            logger.warning(f"Could not read markdown content for snapshot '{memory_id}': {e}")
            content = ""

    title = memory.get("title", "")
    category = memory.get("category", "personal")
    tags = memory.get("tags", [])
    content_hash = memory.get("content_hash") or compute_string_hash(content)

    version_record = db_save_version(
        memory_id=memory_id,
        title=title,
        category=category,
        tags=tags,
        content=content,
        content_hash=content_hash,
    )

    db_prune_versions(memory_id=memory_id, max_versions=MAX_RETAINED_VERSIONS)
    return version_record


@handle_errors
def get_version_history(memory_id: str) -> List[Dict[str, Any]]:
    """
    Returns the list of version snapshots available for a given memory ID.
    Ordered from newest version to oldest version.
    """
    versions = db_get_versions(memory_id)
    history = []
    for v in versions:
        history.append({
            "version_number": v["version_number"],
            "title": v["title"],
            "category": v["category"],
            "tags": v["tags"],
            "created_at": v["created_at"],
            "content_snippet": v["content"][:200] + ("..." if len(v["content"]) > 200 else ""),
            "content_hash": v["content_hash"],
        })
    return history


@handle_errors
def get_version_snapshot(memory_id: str, version_number: int) -> Optional[Dict[str, Any]]:
    """
    Fetches details and full content for a specific version snapshot.
    """
    return db_get_version_by_number(memory_id, version_number)
