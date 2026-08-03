from pathlib import Path
from typing import List

from config.constants import DEFAULT_CATEGORIES, MEMORIES_DIR


def get_available_categories() -> List[str]:
    """
    Dynamically scans data/memories/ subdirectories on disk and returns all available categories.
    """
    categories = set(DEFAULT_CATEGORIES)
    if MEMORIES_DIR.exists():
        for item in MEMORIES_DIR.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                categories.add(item.name.lower())
    return sorted(list(categories))


def get_category_dir(category: str) -> Path:
    """
    Returns (and creates if missing) the directory Path for any category.
    """
    cat_name = category.strip().lower() if category and category.strip() else "personal"
    cat_dir = MEMORIES_DIR / cat_name
    cat_dir.mkdir(parents=True, exist_ok=True)
    return cat_dir
