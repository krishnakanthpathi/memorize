import json
import os

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config.constants import INDEX_PATH, MEMORIES_CATEGORIES
from core.logger import logger, handle_errors


def get_initial_index_structure() -> Dict[str, Any]:
    """Returns a blank index structure."""
    return {
        "total_memories": 0,
        "last_updated": None,
        "last_synced": None,
        "categories": {
            name: {"count": 0, "tags": []} for name in MEMORIES_CATEGORIES.keys()
        },
        "tag_index": {},
        "memories": [],
    }


@handle_errors
def load_index() -> Dict[str, Any]:
    """
    Loads data/index.json. Seeds a fresh index file if missing or empty.
    """
    if not INDEX_PATH.exists():
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        initial_index = get_initial_index_structure()
        save_index(initial_index)
        return initial_index

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error("index.json is corrupted! Seeding new index structure.")
            initial_index = get_initial_index_structure()
            save_index(initial_index)
            return initial_index


@handle_errors
def save_index(index_data: Dict[str, Any]) -> bool:
    """
    Atomically writes index_data to data/index.json using a temp file.
    """
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = INDEX_PATH.with_suffix(".json.tmp")

    # Update last_updated timestamp
    index_data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)

    # Atomic replace guarantees file safety
    os.replace(temp_path, INDEX_PATH)
    logger.info("Successfully updated index.json")
    return True


@handle_errors
def add_memory_to_index(memory_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new memory metadata entry to index.json and updates stats & tag maps.
    """
    index_data = load_index()

    # 1. Increment total count
    index_data["total_memories"] += 1

    # 2. Update category statistics
    cat = memory_entry["category"]
    if cat in index_data["categories"]:
        index_data["categories"][cat]["count"] += 1
        for tag in memory_entry.get("tags", []):
            if tag not in index_data["categories"][cat]["tags"]:
                index_data["categories"][cat]["tags"].append(tag)

    # 3. Update reverse tag lookup index
    mem_id = memory_entry["id"]
    for tag in memory_entry.get("tags", []):
        if tag not in index_data["tag_index"]:
            index_data["tag_index"][tag] = []
        if mem_id not in index_data["tag_index"][tag]:
            index_data["tag_index"][tag].append(mem_id)

    # 4. Append memory metadata entry
    index_data["memories"].append(memory_entry)

    save_index(index_data)
    return index_data
