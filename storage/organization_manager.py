import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional

from classification.classifier import classify_memory
import config.constants as constants
from config.settings import get_memories_dir, get_storage_layout
from core.logger import handle_errors, logger
from storage.markdown_handler import create_markdown_file, read_markdown_file
from storage.db_manager import (
    get_all_memories,
    get_media_record,
    get_media_record_by_filename,
    get_memory_by_id,
    upsert_media_record,
    upsert_memory_index,
)
from utils.category_utils import (
    get_available_categories,
    get_category_dir,
    get_memory_bundle_dir,
    slugify_title,
)


@handle_errors
def reorganize_memories(
    auto_fix: bool = True,
    reclassify: bool = False,
    convert_to_bundle: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Audits and reorganizes Markdown memory files and their associated media/thumbnails:
    1. Reads all memory notes from the active memories directory.
    2. Re-classifies content if requested and misplaced.
    3. If convert_to_bundle is True (or layout is 'bundle'):
       - Creates dedicated <category>/<memory_slug>/ folder.
       - Places <memory_slug>.md inside the folder.
       - Discovers attached media & thumbnails referenced in the note and moves them into
         <memory_slug>/media/ and <memory_slug>/thumbnails/.
       - Updates SQLite DB records with the new file paths.
    4. Cleans up empty directories.
    5. Returns a comprehensive migration report.
    """
    mem_dir = get_memories_dir()
    if not mem_dir.exists():
        return {"status": "error", "message": "Memories directory does not exist."}

    if convert_to_bundle is None:
        convert_to_bundle = (get_storage_layout() == "bundle")

    available_categories = get_available_categories()
    files_checked = 0
    files_moved: List[Dict[str, str]] = []
    files_renamed: List[Dict[str, str]] = []
    media_relocated: List[Dict[str, str]] = []
    reclassified_count = 0

    # Collect all markdown memory files
    found_md_files = []
    for root, dirs, files in os.walk(mem_dir):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                found_md_files.append(Path(root) / file)

    for full_path in found_md_files:
        if not full_path.exists():
            continue

        files_checked += 1
        read_res = read_markdown_file(full_path)
        if isinstance(read_res, dict) and read_res.get("status") == "error":
            continue

        frontmatter, content = read_res
        category = frontmatter.get("category", "personal").strip().lower()
        title = frontmatter.get("title", full_path.stem.replace("_", " ").title())
        memory_id = frontmatter.get("id")
        tags = frontmatter.get("tags", [])

        # Optional re-classification
        if reclassify:
            is_personal_identity = any(
                kw in title.lower() for kw in [
                    "personal information",
                    "contact and identification",
                    "personal summary",
                    "identification details",
                    "contact details",
                ]
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

        ideal_slug = slugify_title(title)

        # Target Path Calculation
        if convert_to_bundle:
            bundle_dir = get_memory_bundle_dir(category, ideal_slug, create_subdirs=True)
            target_path = bundle_dir / f"{ideal_slug}.md"
            media_subfolder = bundle_dir / "media"
            thumb_subfolder = bundle_dir / "thumbnails"
            media_subfolder.mkdir(parents=True, exist_ok=True)
            thumb_subfolder.mkdir(parents=True, exist_ok=True)
        else:
            target_cat_dir = get_category_dir(category)
            target_path = target_cat_dir / f"{ideal_slug}.md"

        if auto_fix:
            # 1. Relocate media referenced in the memory content or linked in database
            if convert_to_bundle:
                referenced_media = set(re.findall(
                    r"/api/(?:media|documents)(?:/download)?/([a-zA-Z0-9_\-\.]+)", content
                ))
                # Also include all media_items explicitly linked to memory_id or its parent doc in DB
                from storage.db_manager import list_all_media_records
                all_db_media = list_all_media_records()
                parent_doc_ids = set()
                for md in all_db_media:
                    if md.get("memory_id") == memory_id:
                        referenced_media.add(md["filename"])
                        parent_doc_ids.add(md["id"])
                for md in all_db_media:
                    if md.get("memory_id") in parent_doc_ids:
                        referenced_media.add(md["filename"])

                for fname in referenced_media:
                    clean_fname = Path(fname).name
                    # Find current file on disk
                    from storage.media_store_manager import get_media_file_path
                    src_media_path = get_media_file_path(clean_fname)
                    if src_media_path and src_media_path.exists():
                        is_thumb = (
                            "_thumb" in clean_fname
                            or "_page_" in clean_fname
                            or (src_media_path.parent.name == "thumbnails")
                        )
                        dest_dir = thumb_subfolder if is_thumb else media_subfolder
                        dest_media_path = dest_dir / clean_fname

                        if src_media_path.resolve() != dest_media_path.resolve():
                            try:
                                shutil.move(str(src_media_path), str(dest_media_path))
                                media_relocated.append({
                                    "filename": clean_fname,
                                    "from": str(src_media_path),
                                    "to": str(dest_media_path),
                                    "memory": title,
                                })
                                # Update SQLite media record
                                m_rec = get_media_record_by_filename(clean_fname)
                                if m_rec:
                                    m_rec["file_path"] = str(dest_media_path)
                                    m_rec["memory_id"] = memory_id
                                    upsert_media_record(m_rec)
                            except Exception as move_err:
                                logger.warning(f"Failed to relocate media asset {clean_fname}: {move_err}")

            # 2. Relocate/save Markdown file if path changed
            if full_path.resolve() != target_path.resolve():
                logger.info(f"Reorganizing memory note: '{full_path}' -> '{target_path}'")
                create_markdown_file(
                    memory_id=memory_id,
                    title=title,
                    category=category,
                    tags=tags,
                    content=content,
                    file_path=target_path,
                    overwrite=True,
                )
                # Remove old file if it wasn't the target
                if full_path.exists() and full_path.resolve() != target_path.resolve():
                    full_path.unlink(missing_ok=True)
                    # If old parent folder is now empty and not a root category, remove it
                    old_parent = full_path.parent
                    if old_parent.name not in available_categories and old_parent != mem_dir:
                        if old_parent.exists() and not any(old_parent.iterdir()):
                            shutil.rmtree(old_parent, ignore_errors=True)

                if memory_id:
                    mem_entry = get_memory_by_id(memory_id)
                    if mem_entry:
                        mem_entry["category"] = category
                        mem_entry["file_path"] = str(target_path)
                        upsert_memory_index(mem_entry)

                files_moved.append({"from": str(full_path), "to": str(target_path)})
            else:
                # Same path, ensure DB index has valid file_path
                if memory_id:
                    mem_entry = get_memory_by_id(memory_id)
                    if mem_entry and mem_entry.get("file_path") != str(target_path):
                        mem_entry["file_path"] = str(target_path)
                        upsert_memory_index(mem_entry)

    # Clean up empty category and bundle subdirectories
    if mem_dir.exists():
        for root, dirs, files in os.walk(mem_dir, topdown=False):
            p = Path(root)
            if p != mem_dir and p.name not in available_categories:
                if p.is_dir() and not any(p.iterdir()):
                    shutil.rmtree(p, ignore_errors=True)

    return {
        "status": "success",
        "files_checked": files_checked,
        "files_moved_count": len(files_moved),
        "files_moved": files_moved,
        "media_relocated_count": len(media_relocated),
        "media_relocated": media_relocated,
        "reclassified_count": reclassified_count,
        "storage_layout": "bundle" if convert_to_bundle else "flat",
    }
