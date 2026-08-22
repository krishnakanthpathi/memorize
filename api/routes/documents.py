"""
Dedicated Document & PDF API Router for Memorize.
Handles multi-page PDF uploads, pypdfium2 page extraction, Ollama GLM-OCR batching,
per-page re-scans, and direct file downloads.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

import config.constants as constants
from core.logger import logger
from media.pdf_processor import (
    process_pdf_document,
    render_pdf_pages_to_images,
    reprocess_single_page_ocr,
)
from storage.db_manager import (
    get_media_record,
    get_media_record_by_filename,
    list_all_media_records,
)
from storage.media_store_manager import (
    get_media_download_info,
    get_media_file_path,
    save_raw_image,
)

router = APIRouter(prefix="/api/documents", tags=["Document & PDF Engine"])


@router.post("/upload-pdf")
async def upload_pdf_document(
    file: UploadFile = File(...),
    memory_id: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    run_ocr: bool = Form(True),
    custom_prompt: Optional[str] = Form(None),
    max_pages: int = Form(50),
):
    """
    Uploads a multi-page PDF document:
    1. Stores original PDF byte-for-byte in data/media/.
    2. Renders pages into PNG images using pypdfium2.
    3. Generates cover thumbnail.
    4. Runs local Ollama GLM-OCR per page.
    5. Returns structured document metadata, page list, and ready-to-insert markdown card.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No PDF file provided.")

    original_filename = filename or file.filename or "document.pdf"
    if not original_filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF document.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF file uploaded.")

    if len(pdf_bytes) > constants.MAX_MEDIA_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"PDF size exceeds maximum allowed limit of {constants.MAX_MEDIA_UPLOAD_SIZE // (1024 * 1024)}MB.",
        )

    try:
        result = process_pdf_document(
            file_bytes=pdf_bytes,
            filename=original_filename,
            memory_id=memory_id,
            run_ocr=run_ocr,
            custom_prompt=custom_prompt,
            max_pages=max_pages,
        )
        return result
    except Exception as e:
        logger.error(f"PDF document processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {e}")


@router.get("/item/{identifier:path}")
async def get_document_details(identifier: str):

    """
    Retrieves document metadata, page records, and OCR status.
    Identifier can be document ID, full URL, or filename.
    Automatically renders pages on-demand if they are not yet cached on disk.
    """
    clean_ident = identifier.split("?")[0].replace("/api/media/", "").replace("/api/documents/", "").strip("/ ")
    clean_ident = Path(clean_ident).name

    doc_record = get_media_record(identifier)
    if not doc_record:
        doc_record = get_media_record_by_filename(clean_ident)

    # If resolved record is a thumbnail or page image, follow parent memory_id to PDF document
    if doc_record and doc_record.get("memory_id"):
        parent_doc = get_media_record(doc_record["memory_id"])
        if parent_doc and parent_doc["filename"].endswith(".pdf"):
            doc_record = parent_doc

    # If still pointing to thumbnail/image, search matching PDF by stem
    all_media = list_all_media_records()
    if doc_record and not doc_record["filename"].endswith(".pdf"):
        import re
        stem = Path(doc_record.get("original_filename") or doc_record["filename"]).stem
        stem = stem.replace("_thumb", "").replace("_page_", "")
        stem = re.sub(r"\d+$", "", stem).strip("_")
        for m in all_media:
            if m["filename"].endswith(".pdf") and (stem in m["filename"] or stem in (m.get("original_filename") or "")):
                doc_record = m
                break

    # Fallback to search list by clean_ident
    if not doc_record:
        for m in all_media:
            if m["filename"] == clean_ident or m.get("original_filename") == clean_ident:
                doc_record = m
                break
            if clean_ident in m["filename"] and m["filename"].endswith(".pdf"):
                doc_record = m
                break

    if not doc_record:
        raise HTTPException(status_code=404, detail=f"Document '{identifier}' not found.")


    doc_record["url"] = f"/api/media/{doc_record['filename']}"
    doc_record["download_url"] = f"/api/media/download/{doc_record['filename']}"

    doc_id = doc_record["id"]
    doc_orig = doc_record.get("original_filename") or doc_record["filename"]
    doc_stem = Path(doc_orig).stem

    all_media = list_all_media_records()
    seen_page_indices = {}
    
    import re
    def extract_page_idx(filename: str) -> int:
        match = re.search(r"_page_(\d+)", filename)
        if match:
            return int(match.group(1))
        return 9999

    # 1. Check media items linked via memory_id
    for m in all_media:
        if m.get("memory_id") == doc_id:
            fname = m["filename"]
            if "_page_" in fname or (fname.endswith(".png") and not fname.endswith("_thumb.png")):
                fpath = get_media_file_path(fname)
                if fpath and fpath.exists():
                    p_idx = extract_page_idx(fname)
                    if p_idx not in seen_page_indices or (m.get("ocr_text") and not seen_page_indices[p_idx].get("ocr_text")):
                        seen_page_indices[p_idx] = {
                            "id": m["id"],
                            "filename": m["filename"],
                            "url": f"/api/media/{m['filename']}",
                            "ocr_text": m.get("ocr_text", ""),
                            "ocr_status": m.get("ocr_status", "skipped"),
                        }

    # 2. Check matching stem if memory_id wasn't set on legacy uploads
    if len(seen_page_indices) == 0:
        for m in all_media:
            fname = m["filename"]
            if f"{doc_stem}_page_" in fname:
                fpath = get_media_file_path(fname)
                if fpath and fpath.exists():
                    p_idx = extract_page_idx(fname)
                    if p_idx not in seen_page_indices or (m.get("ocr_text") and not seen_page_indices[p_idx].get("ocr_text")):
                        seen_page_indices[p_idx] = {
                            "id": m["id"],
                            "filename": m["filename"],
                            "url": f"/api/media/{m['filename']}",
                            "ocr_text": m.get("ocr_text", ""),
                            "ocr_status": m.get("ocr_status", "skipped"),
                        }

    # 3. If still no page records, dynamically render pages from PDF file on disk
    if len(seen_page_indices) == 0:
        pdf_path = Path(doc_record["file_path"])
        if pdf_path.exists() and pdf_path.is_file() and pdf_path.suffix.lower() == ".pdf":
            try:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                rendered_images = render_pdf_pages_to_images(pdf_bytes)
                for idx, p_bytes in enumerate(rendered_images):
                    page_num = idx + 1
                    p_rec = save_raw_image(
                        file_bytes=p_bytes,
                        filename=f"{doc_stem}_page_{page_num}.png",
                        mime_type="image/png",
                        memory_id=doc_id,
                    )
                    seen_page_indices[page_num] = {
                        "id": p_rec["id"],
                        "filename": p_rec["filename"],
                        "url": f"/api/media/{p_rec['filename']}",
                        "ocr_text": "",
                        "ocr_status": "skipped",
                    }
            except Exception as err:
                logger.warning(f"On-demand PDF page rendering failed: {err}")

    # Sort pages by page index ascending
    sorted_page_keys = sorted(seen_page_indices.keys())
    page_records = [seen_page_indices[k] for k in sorted_page_keys]

    return {
        "status": "success",
        "document": doc_record,
        "total_pages": len(page_records),
        "pages": page_records,
    }



@router.post("/re-ocr-page")
async def reprocess_page_ocr_endpoint(
    page_identifier: str = Body(..., embed=True),
    custom_prompt: Optional[str] = Body(None, embed=True),
):
    """
    Re-runs Ollama GLM-OCR on an individual document page image with optional custom prompt.
    """
    try:
        result = reprocess_single_page_ocr(
            page_identifier=page_identifier,
            custom_prompt=custom_prompt,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to re-run OCR for page {page_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"Page OCR re-run failed: {e}")


@router.post("/trigger-ocr")
async def trigger_document_ocr_endpoint(
    doc_identifier: str = Body(..., embed=True),
    custom_prompt: Optional[str] = Body(None, embed=True),
):
    """
    Triggers GLM-OCR batch extraction across all pages of a PDF document on-demand.
    """
    details = await get_document_details(doc_identifier)
    pages = details.get("pages", [])
    if not pages:
        raise HTTPException(status_code=400, detail="No pages available for OCR extraction.")

    aggregated_parts: List[str] = []
    updated_pages = []

    for idx, p in enumerate(pages):
        page_num = idx + 1
        page_id = p["id"]
        try:
            logger.info(f"Running GLM-OCR on page {page_num}/{len(pages)} ({p['filename']})...")
            rec = reprocess_single_page_ocr(
                page_identifier=page_id,
                custom_prompt=custom_prompt,
            )
            page_text = rec.get("ocr_text", "")
            updated_pages.append({
                "id": page_id,
                "filename": p["filename"],
                "url": p["url"],
                "ocr_text": page_text,
                "ocr_status": "completed",
            })
            if page_text.strip():
                if len(pages) > 1:
                    aggregated_parts.append(f"### Page {page_num}\n\n{page_text.strip()}")
                else:
                    aggregated_parts.append(page_text.strip())
        except Exception as err:
            logger.warning(f"GLM-OCR failed on page {page_num}: {err}")
            updated_pages.append({
                "id": page_id,
                "filename": p["filename"],
                "url": p["url"],
                "ocr_text": "",
                "ocr_status": "failed",
            })

    full_ocr = "\n\n---\n\n".join(aggregated_parts)
    return {
        "status": "success",
        "document": details["document"],
        "total_pages": len(pages),
        "ocr_text": full_ocr,
        "pages": updated_pages,
    }



@router.get("/download/{filename_or_id}")
async def download_document_file(filename_or_id: str):
    """
    Direct download endpoint for PDF documents and media files with Content-Disposition attachment header.
    """
    info = get_media_download_info(filename_or_id)
    if not info:
        raise HTTPException(status_code=404, detail="File not found.")

    file_path = Path(info["file_path"])
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Physical file missing from disk.")

    orig_name = info.get("original_filename") or file_path.name
    return FileResponse(
        path=str(file_path),
        media_type=info.get("mime_type", "application/pdf"),
        filename=orig_name,
        headers={
            "Content-Disposition": f'attachment; filename="{orig_name}"',
            "Cache-Control": "private, no-cache",
        },
    )
