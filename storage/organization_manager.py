import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List

from classification.classifier import classify_memory
import config.constants as constants
from core.logger import handle_errors, logger
from storage.markdown_handler import create_markdown_file, read_markdown_file
from storage.db_manager import get_memory_by_id, upsert_memory_index
from utils import get_available_categories, get_category_dir, slugify_title


@handle_errors
def reorganize_memories(auto_fix: bool = True, reclassify: bool = True) -> Dict[str, Any]:
    """
    Audits and reorganizes Markdown memory files in data/memories/:
    1. Re-classifies content if misplaced under 'personal' or wrong category.
    2. Verifies parent folder matches frontmatter category. Moves file if misplaced.
    3. Normalizes filenames into clean snake_case/slugified conventions.
    4. Cleans up empty category directories.
    5. Re-syncs database and vector stores.
    """
    mem_dir = constants.MEMORIES_DIR
    if not mem_dir.exists():
        return {"status": "error", "message": "Memories directory does not exist."}

    available_categories = get_available_categories()
    files_checked = 0
    files_moved = []
    files_renamed = []
    reclassified_count = 0

    for root, dirs, files in os.walk(mem_dir):
        for file in files:
            if not file.endswith(".md") or file.startswith("."):
                continue

            files_checked += 1
            full_path = Path(root) / file

            read_res = read_markdown_file(full_path)
            if isinstance(read_res, dict) and read_res.get("status") == "error":
                continue

            frontmatter, content = read_res
            category = frontmatter.get("category", "personal").strip().lower()

            title = frontmatter.get("title", full_path.stem.replace("_", " ").title())
            memory_id = frontmatter.get("id")
            tags = frontmatter.get("tags", [])

            # Re-classify if requested and currently in personal or invalid
            if reclassify:
                # Personal summary safeguard: keep personal contact/identity summaries in 'personal'
                is_personal_identity = any(
                    kw in title.lower() for kw in ["personal information", "contact and identification", "personal summary", "identification details", "contact details"]
                )
                if not is_personal_identity:
                    full_text = f"{title}\n{content}"
                    cls_res = classify_memory(full_text)
                    new_cat = cls_res.get("category")
                    if new_cat and new_cat in available_categories and new_cat != category:
                        if category == "personal" or cls_res.get("confidence", 0.0) >= 0.8:
                            logger.info(f"Reclassifying '{title}': {category} -> {new_cat}")
                            category = new_cat
                            reclassified_count += 1
                else:
                    category = "personal"

            if category not in available_categories:
                category = "personal"

            target_cat_dir = get_category_dir(category)
            ideal_slug = slugify_title(title)
            ideal_filename = f"{ideal_slug}.md"
            target_path = target_cat_dir / ideal_filename

            moved = False

            if auto_fix:
                if full_path.parent != target_cat_dir or full_path.name != ideal_filename:
                    logger.info(f"Reorganizing file '{full_path.name}' -> '{category}/{ideal_filename}'")
                    full_path.unlink(missing_ok=True)
                    create_markdown_file(
                        memory_id=memory_id,
                        title=title,
                        category=category,
                        tags=tags,
                        content=content,
                        file_path=target_path,
                        overwrite=True,
                    )
                    if memory_id:
                        mem_entry = get_memory_by_id(memory_id)
                        if mem_entry:
                            mem_entry["category"] = category
                            mem_entry["file_path"] = str(target_path)
                            upsert_memory_index(mem_entry)

                    if full_path.parent != target_cat_dir:
                        files_moved.append({"from": str(full_path), "to": str(target_path)})
                        moved = True
                    else:
                        files_renamed.append({"from": file, "to": ideal_filename})

    # Remove empty directories in data/memories/
    if mem_dir.exists():
        for item in mem_dir.iterdir():
            if item.is_dir() and not any(item.iterdir()):
                shutil.rmtree(item)



    return {
        "status": "success",
        "files_checked": files_checked,
        "files_moved_count": len(files_moved),
        "files_moved": files_moved,
        "files_renamed_count": len(files_renamed),
        "files_renamed": files_renamed,
    }
