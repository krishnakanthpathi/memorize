from pathlib import Path
from typing import List

from config.constants import DEFAULT_CATEGORIES, MEMORIES_DIR


def get_available_categories() -> List[str]:
    """
    Returns strictly the predefined list of allowed memory categories.
    Prevents dynamic creation of duplicate or rogue category folders.
    """
    return sorted(list(set(cat.lower() for cat in DEFAULT_CATEGORIES)))


def get_category_dir(category: str) -> Path:
    """
    Returns (and creates if missing) the directory Path for a category.
    Strictly validates category against DEFAULT_CATEGORIES, defaulting to 'personal' if invalid.
    """
    cat_name = category.strip().lower() if category and category.strip() else "personal"
    allowed = get_available_categories()

    if cat_name not in allowed:
        cat_name = "personal"

    cat_dir = MEMORIES_DIR / cat_name
    cat_dir.mkdir(parents=True, exist_ok=True)
    return cat_dir


def slugify_title(title: str) -> str:
    """
    Converts a title string into a clean filename slug.
    Example: "Krishna Kanth's Contact & ID Details" -> "krishna_kanth_s_contact_id_details"
    """
    import re
    if not title:
        return "untitled_memory"
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "_", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")

