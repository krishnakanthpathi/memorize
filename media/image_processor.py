"""
Modular Single-Image Processing Engine for Memorize.
Handles uncompressed image storage and local Ollama GLM-OCR vision extraction.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import config.constants as constants
from core.logger import handle_errors, logger
from storage.db_manager import update_media_ocr_result
from storage.media_store_manager import save_raw_image
from utils.llm_client import extract_text_with_ollama_ocr


@handle_errors
def process_image(
    file_bytes: bytes,
    filename: str,
    mime_type: str = "image/png",
    memory_id: Optional[str] = None,
    run_ocr: bool = True,
    custom_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saves an original uncompressed image, indexes metadata in SQLite,
    and runs Ollama GLM-OCR extraction if requested.
    """
    if not file_bytes:
        raise ValueError("Cannot process empty image bytes.")

    clean_filename = filename or "image.png"

    # Save original uncompressed image to disk & SQLite
    media_record = save_raw_image(
        file_bytes=file_bytes,
        filename=clean_filename,
        mime_type=mime_type,
        memory_id=memory_id,
    )

    ocr_text = ""
    ocr_status = "skipped"

    if run_ocr:
        try:
            logger.info(f"Triggering GLM-OCR extraction for media {media_record['id']}...")
            ocr_text = extract_text_with_ollama_ocr(
                image_bytes=file_bytes,
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
            logger.warning(f"GLM-OCR extraction failed for media {media_record['id']}: {e}")
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
