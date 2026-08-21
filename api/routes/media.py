import base64
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import requests

import config.constants as constants
from core.logger import logger
from media.image_processor import process_image
from storage.db_manager import (
    get_media_record,
    get_media_record_by_filename,
    list_all_media_records,
    update_media_ocr_result,
)
from storage.media_store_manager import (
    delete_all_orphan_media,
    delete_media_item,
    get_media_download_info,
    get_media_file_path,
    list_orphan_media_files,
    save_raw_image,
)
from utils.llm_client import extract_text_with_ollama_ocr

router = APIRouter(prefix="/api/media", tags=["Media Store & OCR"])


def extract_data_uri_bytes(data_uri: str) -> tuple[bytes, str]:
    """Decodes data URI (e.g. data:image/png;base64,...) into (bytes, mime_type)."""
    match = re.match(r"^data:([^;]+);base64,(.*)$", data_uri, re.DOTALL)
    if not match:
        raise ValueError("Invalid Data URL format.")
    mime_type = match.group(1)
    b64_data = match.group(2)
    return base64.b64decode(b64_data), mime_type


@router.post("/upload")
async def upload_media(
    file: Optional[UploadFile] = File(None),
    data_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    memory_id: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    run_ocr: bool = Form(True),
    custom_prompt: Optional[str] = Form(None),
):
    """
    Uploads an original, uncompressed image file (via multipart file, base64 Data URL, or remote URL),
    stores it byte-for-byte in data/media/, and triggers local Ollama GLM-OCR model extraction.
    """
    image_bytes = None
    original_filename = filename or "image.png"
    mime_type = "image/png"

    # 1. Handle direct file upload
    if file is not None:
        image_bytes = await file.read()
        original_filename = file.filename or original_filename
        mime_type = file.content_type or mime_type

    # 2. Handle Base64 Data URL
    elif data_url:
        try:
            image_bytes, mime_type = extract_data_uri_bytes(data_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode base64 image: {e}")

    # 3. Handle remote Image URL
    elif image_url:
        try:
            resp = requests.get(image_url, timeout=15)
            if resp.status_code == 200:
                image_bytes = resp.content
                mime_type = resp.headers.get("content-type", "image/png").split(";")[0]
                original_filename = Path(image_url).name or original_filename
            else:
                raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL: HTTP {resp.status_code}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error downloading image from URL: {e}")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="No valid image payload provided (file, data_url, or image_url).")

    if len(image_bytes) > constants.MAX_MEDIA_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Image size exceeds maximum allowed limit of {constants.MAX_MEDIA_UPLOAD_SIZE // (1024 * 1024)}MB.",
        )

    try:
        return process_image(
            file_bytes=image_bytes,
            filename=original_filename,
            mime_type=mime_type,
            memory_id=memory_id,
            run_ocr=run_ocr,
            custom_prompt=custom_prompt,
        )
    except Exception as e:
        logger.error(f"Failed to process and store image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store media: {e}")


def resolve_media_record(identifier: str) -> Optional[Dict[str, Any]]:
    """Resolves media record by ID, filename, or URL path."""
    if not identifier:
        return None
    # 1. Try direct ID lookup
    rec = get_media_record(identifier)
    if rec:
        return rec
    # 2. Try clean filename (strip /api/media/ or query params)
    clean_name = identifier.split("?")[0].replace("/api/media/", "").strip("/ ")
    clean_name = Path(clean_name).name
    rec = get_media_record_by_filename(clean_name)
    if rec:
        return rec
    # 3. Try original identifier as filename
    rec = get_media_record_by_filename(identifier)
    if rec:
        return rec
    return None


@router.get("/item/{media_id}")
async def get_media_item_details(media_id: str):
    """Retrieves metadata and OCR results for a specific media item."""
    record = resolve_media_record(media_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media item not found.")
    record["url"] = f"/api/media/{record['filename']}"
    record["download_url"] = f"/api/media/download/{record['filename']}"
    return {"status": "success", "media": record}


@router.post("/{media_id}/ocr")
async def trigger_media_ocr(
    media_id: str,
    prompt: Optional[str] = Body(None, embed=True),
):
    """Triggers or re-runs local Ollama GLM-OCR on an existing stored image."""
    record = resolve_media_record(media_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media item not found.")

    file_path = Path(record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical media file missing from disk.")

    with open(file_path, "rb") as f:
        image_bytes = f.read()

    try:
        ocr_text = extract_text_with_ollama_ocr(
            image_bytes=image_bytes,
            prompt=prompt,
        )
        update_media_ocr_result(
            media_id=record["id"],
            ocr_text=ocr_text,
            ocr_status="completed",
            ocr_model=constants.OLLAMA_OCR_MODEL,
        )
        return {
            "status": "success",
            "media_id": record["id"],
            "ocr_text": ocr_text,
            "ocr_model": constants.OLLAMA_OCR_MODEL,
        }
    except Exception as e:
        logger.error(f"Re-running OCR failed: {e}")
        update_media_ocr_result(
            media_id=record["id"],
            ocr_text="",
            ocr_status="failed",
            ocr_model=constants.OLLAMA_OCR_MODEL,
        )
        raise HTTPException(status_code=500, detail=f"OCR execution failed: {e}")


@router.get("/list")
async def list_media():
    """Lists all stored media files and metadata."""
    records = list_all_media_records()
    for r in records:
        r["url"] = f"/api/media/{r['filename']}"
        r["download_url"] = f"/api/media/download/{r['filename']}"
    return {"status": "success", "total": len(records), "media": records}


@router.delete("/{media_id}")
async def delete_media(media_id: str):
    """Deletes a media item from disk and SQLite index."""
    record = resolve_media_record(media_id)
    target_id = record["id"] if record else media_id
    success = delete_media_item(target_id)
    return {"status": "success", "media_id": media_id, "deleted": success}


@router.get("/orphans")
async def get_orphan_media():
    """Returns list and disk space of all unreferenced media and document files."""
    orphans = list_orphan_media_files()
    total_bytes = sum(o.get("file_size", 0) for o in orphans)
    return {
        "status": "success",
        "total_orphans": len(orphans),
        "total_bytes": total_bytes,
        "orphans": orphans,
    }


@router.post("/cleanup-orphans")
async def cleanup_orphan_media_endpoint():
    """Safely removes all unreferenced media files from disk and SQLite index."""
    result = delete_all_orphan_media()
    return {
        "status": "success",
        **result,
    }


@router.get("/download/{filename_or_id}")
async def download_media_file(filename_or_id: str):
    """
    Direct download endpoint with Content-Disposition attachment header for file sharing.
    """
    info = get_media_download_info(filename_or_id)
    if not info:
        raise HTTPException(status_code=404, detail="Media file not found.")

    file_path = Path(info["file_path"])
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Physical file missing from disk.")

    orig_name = info.get("original_filename") or file_path.name
    return FileResponse(
        path=str(file_path),
        media_type=info.get("mime_type", "application/octet-stream"),
        filename=orig_name,
        headers={
            "Content-Disposition": f'attachment; filename="{orig_name}"',
            "Cache-Control": "private, no-cache",
        },
    )


@router.get("/{filename}")
async def serve_media_file(filename: str):
    """
    Streams original uncompressed file directly from data/media/ with caching headers.
    """
    path = get_media_file_path(filename)
    if not path or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found.")

    # Extended MIME type map
    ext = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
        ".pdf": "application/pdf",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    media_type = mime_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=path.name,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )
