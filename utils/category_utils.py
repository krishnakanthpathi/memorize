from pathlib import Path
from typing import List, Optional

import config.constants as constants
from config.settings import get_memories_dir


def get_available_categories() -> List[str]:
    """
    Returns strictly the predefined list of allowed memory categories.
    Prevents dynamic creation of duplicate or rogue category folders.
    """
    return sorted(list(set(cat.lower() for cat in constants.DEFAULT_CATEGORIES)))


def get_category_dir(category: str) -> Path:
    """
    Returns (and creates if missing) the directory Path for a category under the active memories_dir.
    Strictly validates category against DEFAULT_CATEGORIES, defaulting to 'personal' if invalid.
    """
    cat_name = category.strip().lower() if category and category.strip() else "personal"
    allowed = get_available_categories()

    if cat_name not in allowed:
        cat_name = "personal"

    base_mem_dir = get_memories_dir()
    cat_dir = base_mem_dir / cat_name
    cat_dir.mkdir(parents=True, exist_ok=True)
    return cat_dir


def slugify_title(title: str) -> str:
    """
    Converts a title string into a clean filename/foldername slug.
    Example: "Krishna Kanth's Contact & ID Details" -> "krishna_kanth_s_contact_id_details"
    """
    import re
    if not title:
        return "untitled_memory"
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "_", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")


def get_memory_bundle_dir(category: str, title_or_slug: str, create_subdirs: bool = True) -> Path:
    """
    Returns the dedicated bundle directory Path for a memory note:
    <category_dir>/<memory_slug>/
    Optionally creates 'media/' and 'thumbnails/' subfolders.
    """
    cat_dir = get_category_dir(category)
    slug = slugify_title(title_or_slug)
    bundle_dir = cat_dir / slug

    if create_subdirs:
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "media").mkdir(parents=True, exist_ok=True)
        (bundle_dir / "thumbnails").mkdir(parents=True, exist_ok=True)

    return bundle_dir


def get_memory_media_dir(category: str, title_or_slug: str) -> Path:
    """Returns the 'media/' subdirectory inside a memory's bundle folder."""
    bundle_dir = get_memory_bundle_dir(category, title_or_slug, create_subdirs=True)
    media_dir = bundle_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir


def get_memory_thumbnails_dir(category: str, title_or_slug: str) -> Path:
    """Returns the 'thumbnails/' subdirectory inside a memory's bundle folder."""
    bundle_dir = get_memory_bundle_dir(category, title_or_slug, create_subdirs=True)
    thumb_dir = bundle_dir / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    return thumb_dir


