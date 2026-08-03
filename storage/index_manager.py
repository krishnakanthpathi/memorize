from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from config.constants import INDEX_PATH, MEMORIES_DIR
from core.logger import handle_errors, logger
from search.filter_extractor import extract_keywords_and_snippet
from utils import get_available_categories, get_category_dir


def get_initial_index_structure() -> Dict[str, Any]:
    """Returns a blank index structure."""
    return {
        "total_memories": 0,
        "last_updated": None,
        "last_synced": None,
        "categories": {
            name: {"count": 0, "tags": []} for name in get_available_categories()
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
    Adds a memory metadata entry to index.json. Stores a clean snippet,
    extracted keywords, and file_path to keep index.json lightweight and fast.
    """
    index_data = load_index()

    # 1. Extract clean snippet and unique keywords from content
    full_content = memory_entry.get("content", "")
    snippet, extracted_keywords = extract_keywords_and_snippet(full_content)

    user_tags = memory_entry.get("tags", [])
    # Combine user tags + extracted keywords for reverse lookup index
    all_indexed_terms = list(set(user_tags + extracted_keywords))

    # 2. Lightweight metadata record (No full content stored in JSON!)
    lightweight_entry = {
        "id": memory_entry["id"],
        "title": memory_entry["title"],
        "category": memory_entry["category"],
        "tags": user_tags,
        "keywords": extracted_keywords,
        "file_path": memory_entry.get("file_path", ""),
        "snippet": snippet,
        "content_hash": memory_entry.get("content_hash", ""),
        "created_at": memory_entry.get("created_at", ""),
        "updated_at": memory_entry.get("updated_at", ""),
    }

    # 3. Update total memories count
    index_data["total_memories"] += 1

    # 4. Update category statistics (auto-register category if new)
    cat = memory_entry["category"].lower()
    if cat not in index_data["categories"]:
        index_data["categories"][cat] = {"count": 0, "tags": []}

    index_data["categories"][cat]["count"] += 1
    for tag in user_tags:
        if tag not in index_data["categories"][cat]["tags"]:
            index_data["categories"][cat]["tags"].append(tag)

    # 5. Update reverse lookup index (for both user tags & extracted keywords)
    mem_id = memory_entry["id"]
    for term in all_indexed_terms:
        if term not in index_data["tag_index"]:
            index_data["tag_index"][term] = []
        if mem_id not in index_data["tag_index"][term]:
            index_data["tag_index"][term].append(mem_id)

    # 6. Append entry & save atomically
    index_data["memories"].append(lightweight_entry)
    save_index(index_data)
    return index_data


@handle_errors
def add_category_to_index(category: str) -> Dict[str, Any]:
    """
    Dynamically registers a new category in index.json and creates its folder structure.
    """
    cat_lower = category.strip().lower()
    if not cat_lower:
        return load_index()

    # 1. Ensure disk directory exists
    cat_dir = get_category_dir(cat_lower)

    # 2. Update index.json structure
    index_data = load_index()
    categories = index_data.setdefault("categories", {})
    if cat_lower not in categories:
        categories[cat_lower] = {"count": 0, "tags": []}
        index_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_index(index_data)
        logger.info(f"Dynamically registered new category '{cat_lower}' in index.json")

    return index_data


@handle_errors
def delete_category_from_index(category: str) -> Dict[str, Any]:
    """
    Deletes a category from index.json and removes its directory on disk.
    """
    cat_lower = category.strip().lower()
    if not cat_lower:
        return load_index()

    # 1. Remove folder on disk if present
    cat_dir = MEMORIES_DIR / cat_lower
    if cat_dir.exists():
        import shutil
        shutil.rmtree(cat_dir)
        logger.info(f"Deleted category directory: {cat_dir}")

    # 2. Clean index.json
    index_data = load_index()
    categories = index_data.get("categories", {})
    if cat_lower in categories:
        del categories[cat_lower]
        index_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_index(index_data)
        logger.info(f"Deleted category '{cat_lower}' from index.json")

    return index_data
