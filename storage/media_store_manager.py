import hashlib
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import uuid

import config.constants as constants
from core.logger import handle_errors, logger
from storage.db_manager import (
    delete_media_record,
    get_all_memories,
    get_media_record,
    get_media_record_by_filename,
    get_media_record_by_hash,
    get_media_records_for_memory,
    list_all_media_records,
    upsert_media_record,
)


def compute_bytes_hash(data: bytes) -> str:
    """Computes standard SHA-256 hex digest for binary data."""
    return hashlib.sha256(data).hexdigest()


def sanitize_media_filename(filename: str) -> str:
    """Cleans filename to be filesystem-safe and lowercase extension."""
    if not filename:
        return f"image_{uuid.uuid4().hex[:8]}.png"
    # Extract stem and ext
    p = Path(filename)
    stem = re.sub(r"[^\w\-.]", "_", p.stem).strip("_")
    ext = p.suffix.lower() if p.suffix else ".png"
    if not stem:
        stem = f"image_{uuid.uuid4().hex[:8]}"
    return f"{stem}{ext}"


@handle_errors
def save_raw_image(
    file_bytes: bytes,
    filename: str,
    mime_type: str = "image/png",
    memory_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saves an original, uncompressed image file byte-for-byte into data/media/.
    Guarantees no lossy re-encoding or compression.
    Uses SHA-256 deduplication and indexes metadata in SQLite.
    """
    if not file_bytes:
        raise ValueError("Cannot save empty image bytes.")

    constants.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    content_hash = compute_bytes_hash(file_bytes)
    file_size = len(file_bytes)

    # Check for existing media with the exact same content hash
    existing_record = get_media_record_by_hash(content_hash)
    if existing_record and Path(existing_record["file_path"]).exists():
        logger.info(f"Reusing existing media file for content hash {content_hash[:10]}...")
        # Update memory_id if provided and not set
        if memory_id and not existing_record.get("memory_id"):
            existing_record["memory_id"] = memory_id
            upsert_media_record(existing_record)
        return {
            **existing_record,
            "url": f"/api/media/{existing_record['filename']}",
            "is_duplicate": True,
        }

    # Generate unique stored filename: <hash_prefix>_<sanitized_name>
    clean_name = sanitize_media_filename(filename)
    prefix = content_hash[:10]
    stored_filename = f"{prefix}_{clean_name}"
    target_path = constants.MEDIA_DIR / stored_filename

    # Write raw uncompressed bytes directly to disk
    with open(target_path, "wb") as f:
        f.write(file_bytes)

    media_id = f"med_{prefix}_{uuid.uuid4().hex[:6]}"
    media_entry = {
        "id": media_id,
        "memory_id": memory_id,
        "filename": stored_filename,
        "original_filename": filename,
        "file_path": str(target_path),
        "mime_type": mime_type,
        "file_size": file_size,
        "content_hash": content_hash,
        "ocr_text": "",
        "ocr_status": "pending",
        "ocr_model": constants.OLLAMA_OCR_MODEL,
    }

    saved_record = upsert_media_record(media_entry)
    saved_record["url"] = f"/api/media/{stored_filename}"
    saved_record["is_duplicate"] = False
    logger.info(f"Saved uncompressed image: {target_path} ({file_size} bytes)")
    return saved_record


@handle_errors
def get_media_file_path(filename_or_id: str) -> Optional[Path]:
    """Resolves local absolute Path for a given stored filename or media ID."""
    # Try finding by media_id first
    record = get_media_record(filename_or_id)
    if record and Path(record["file_path"]).exists():
        return Path(record["file_path"])

    # Try finding by filename in DB
    record = get_media_record_by_filename(filename_or_id)
    if record and Path(record["file_path"]).exists():
        return Path(record["file_path"])

    # Fallback to direct path check in constants.MEDIA_DIR
    direct_path = constants.MEDIA_DIR / filename_or_id
    if direct_path.exists() and direct_path.is_file():
        return direct_path

    return None


@handle_errors
def delete_media_item(media_id_or_filename: str) -> bool:
    """Deletes media record from SQLite and removes physical file from data/media/."""
    record = get_media_record(media_id_or_filename)
    if not record:
        record = get_media_record_by_filename(media_id_or_filename)

    file_path = None
    if record:
        file_path = Path(record["file_path"])
        delete_media_record(record["id"])
    else:
        file_path = constants.MEDIA_DIR / media_id_or_filename

    if file_path and file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
            logger.info(f"Deleted physical media file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to unlink media file {file_path}: {e}")

    return True


@handle_errors
def list_orphan_media_files() -> List[Dict[str, Any]]:
    """
    Finds unreferenced media and document files in data/media/ that are not linked
    to any active Markdown memory notes or valid DB records.
    """
    constants.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    on_disk_files = {
        f.name: f
        for f in constants.MEDIA_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".")
    }
    all_memories = get_all_memories()

    # Collect all file references from memory contents
    referenced_filenames = set()
    for mem in all_memories:
        content = mem.get("content", "")
        # Match /api/media/..., /api/media/download/..., /api/documents/...
        matches = re.findall(
            r"/api/(?:media|documents)(?:/download)?/([a-zA-Z0-9_\-\.]+)", content
        )
        for m in matches:
            referenced_filenames.add(m.strip())

    # Collect all media recorded in DB
    db_records = list_all_media_records()
    active_memory_ids = {m["id"] for m in all_memories}

    # DB records whose memory_id is alive or whose file is directly referenced
    db_valid_filenames = set()
    orphan_db_record_ids = []

    for r in db_records:
        fname = r["filename"]
        mem_id = r.get("memory_id")
        if (mem_id and mem_id in active_memory_ids) or (fname in referenced_filenames):
            db_valid_filenames.add(fname)
        else:
            orphan_db_record_ids.append(r["id"])

    orphans = []
    for fname, path in on_disk_files.items():
        if fname not in referenced_filenames and fname not in db_valid_filenames:
            orphans.append({
                "filename": fname,
                "file_path": str(path),
                "file_size": path.stat().st_size,
            })

    return orphans


@handle_errors
def delete_all_orphan_media() -> Dict[str, Any]:
    """
    Deletes all detected orphan media/document files from data/media/
    and purges dangling records from SQLite.
    """
    orphans = list_orphan_media_files()
    deleted_count = 0
    freed_bytes = 0

    for orphan in orphans:
        p = Path(orphan["file_path"])
        if p.exists():
            freed_bytes += p.stat().st_size
            p.unlink()
            deleted_count += 1

        # Also purge from DB if present
        rec = get_media_record_by_filename(orphan["filename"])
        if rec:
            delete_media_record(rec["id"])

    logger.info(f"Cleaned up {deleted_count} orphan media files ({freed_bytes} bytes freed).")
    return {
        "deleted_count": deleted_count,
        "freed_bytes": freed_bytes,
        "orphans_removed": [o["filename"] for o in orphans],
    }


@handle_errors
def get_media_download_info(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves download metadata for a media or document item.
    """
    record = get_media_record(identifier)
    if not record:
        record = get_media_record_by_filename(identifier)

    if not record:
        # Check direct file existence
        direct_path = constants.MEDIA_DIR / identifier
        if direct_path.exists() and direct_path.is_file():
            return {
                "id": identifier,
                "filename": direct_path.name,
                "original_filename": direct_path.name,
                "file_path": str(direct_path),
                "file_size": direct_path.stat().st_size,
                "mime_type": "application/octet-stream",
                "download_url": f"/api/media/download/{direct_path.name}",
                "view_url": f"/api/media/{direct_path.name}",
            }
        return None

    return {
        "id": record["id"],
        "filename": record["filename"],
        "original_filename": record.get("original_filename") or record["filename"],
        "file_path": record["file_path"],
        "file_size": record.get("file_size", 0),
        "mime_type": record.get("mime_type", "application/octet-stream"),
        "download_url": f"/api/media/download/{record['filename']}",
        "view_url": f"/api/media/{record['filename']}",
    }

