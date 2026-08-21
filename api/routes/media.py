import base64
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import requests

import config.constants as constants
from core.logger import logger
from storage.db_manager import (
    get_media_record,
    get_media_record_by_filename,
    list_all_media_records,
    update_media_ocr_result,
)
from storage.media_store_manager import (
    delete_media_item,
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

    # Save original uncompressed image to disk and index in SQLite
    try:
        media_record = save_raw_image(
            file_bytes=image_bytes,
            filename=original_filename,
            mime_type=mime_type,
            memory_id=memory_id,
        )
    except Exception as e:
        logger.error(f"Failed to save image to media store: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store media: {e}")

    # Run local Ollama GLM-OCR extraction if requested
    ocr_text = ""
    ocr_status = "skipped"
    if run_ocr:
        try:
            logger.info(f"Triggering local Ollama GLM-OCR extraction for media {media_record['id']}...")
            ocr_text = extract_text_with_ollama_ocr(
                image_bytes=image_bytes,
                prompt=custom_prompt,
            )
            ocr_status = "completed"
            update_media_ocr_result(
                media_id=media_record["id"],
                ocr_text=ocr_text,
                ocr_status="completed",
                ocr_model=constants.OLLAMA_OCR_MODEL,
            )
            media_record["ocr_text"] = ocr_text
            media_record["ocr_status"] = "completed"
        except Exception as e:
            logger.warning(f"Ollama OCR processing failed for {media_record['id']}: {e}")
            ocr_status = "failed"
            update_media_ocr_result(
                media_id=media_record["id"],
                ocr_text="",
                ocr_status="failed",
                ocr_model=constants.OLLAMA_OCR_MODEL,
            )
            media_record["ocr_status"] = "failed"

    return {
        "status": "success",
        "media": media_record,
        "ocr": {
            "status": ocr_status,
            "text": ocr_text,
            "model": constants.OLLAMA_OCR_MODEL,
        },
    }


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
    return {"status": "success", "total": len(records), "media": records}


@router.delete("/{media_id}")
async def delete_media(media_id: str):
    """Deletes a media item from disk and SQLite index."""
    record = resolve_media_record(media_id)
    target_id = record["id"] if record else media_id
    success = delete_media_item(target_id)
    return {"status": "success", "media_id": media_id, "deleted": success}



@router.get("/{filename}")
async def serve_media_file(filename: str):
    """
    Streams original uncompressed image file directly from data/media/ with aggressive caching headers.
    """
    path = get_media_file_path(filename)
    if not path or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found.")

    # Determine MIME type
    ext = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
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
