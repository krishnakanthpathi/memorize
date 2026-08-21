"""
Modular PDF Processing Engine for Memorize.
Uses pypdfium2 (zero external binaries) to render crisp page images, generate
cover thumbnails, execute local Ollama GLM-OCR per page, and assemble structured markdown.
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image
import pypdfium2

import config.constants as constants
from core.logger import handle_errors, logger
from storage.db_manager import (
    get_media_record,
    get_media_record_by_filename,
    update_media_ocr_result,
)
from storage.media_store_manager import get_media_file_path, save_raw_image
from utils.llm_client import extract_text_with_ollama_ocr


@handle_errors
def render_pdf_pages_to_images(pdf_bytes: bytes, dpi: int = 150) -> List[bytes]:
    """
    Renders every page of a PDF into high-resolution PNG image bytes.
    Uses pypdfium2 (Google PDFium) for fast, self-contained rendering.
    """
    if not pdf_bytes:
        raise ValueError("Cannot render empty PDF bytes.")

    pdf = pypdfium2.PdfDocument(pdf_bytes)
    total_pages = len(pdf)
    logger.info(f"Rendering {total_pages} pages from PDF document at {dpi} DPI...")

    page_images: List[bytes] = []
    # 72 DPI is base PDF points scale
    scale = dpi / 72.0

    for page_idx in range(total_pages):
        page = pdf[page_idx]
        pil_image = page.render(scale=scale).to_pil()
        # Convert to PNG byte stream
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG", optimize=True)
        page_images.append(buf.getvalue())

    logger.info(f"Successfully rendered {len(page_images)} page images.")
    return page_images


@handle_errors
def generate_pdf_thumbnail(page_1_bytes: bytes, max_size: tuple[int, int] = (600, 800)) -> bytes:
    """
    Generates a crisp, proportional preview cover thumbnail from the first page image.
    """
    if not page_1_bytes:
        raise ValueError("Empty image bytes provided for thumbnail generation.")

    with Image.open(io.BytesIO(page_1_bytes)) as img:
        img_thumb = img.copy()
        img_thumb.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img_thumb.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


@handle_errors
def process_pdf_document(
    file_bytes: bytes,
    filename: str,
    memory_id: Optional[str] = None,
    run_ocr: bool = True,
    custom_prompt: Optional[str] = None,
    max_pages: int = 50,
) -> Dict[str, Any]:
    """
    Processes an uploaded PDF document:
    1. Stores raw uncompressed PDF byte-for-byte in data/media/.
    2. Converts pages into PNG images via pypdfium2.
    3. Generates and stores cover preview thumbnail.
    4. Runs local Ollama GLM-OCR per page sequentially.
    5. Assembles clean Markdown insertion card with download link and extracted text.
    """
    if not file_bytes:
        raise ValueError("Cannot process empty PDF document.")

    clean_filename = filename or "document.pdf"
    if not clean_filename.lower().endswith(".pdf"):
        clean_filename += ".pdf"

    # 1. Save original PDF file
    doc_record = save_raw_image(
        file_bytes=file_bytes,
        filename=clean_filename,
        mime_type="application/pdf",
        memory_id=memory_id,
    )

    # 2. Render pages into images
    page_byte_list = render_pdf_pages_to_images(file_bytes)
    total_pages = len(page_byte_list)
    if total_pages > max_pages:
        logger.warning(
            f"PDF has {total_pages} pages, which exceeds the max limit of {max_pages}. "
            f"Only the first {max_pages} pages will be processed."
        )
        page_byte_list = page_byte_list[:max_pages]
        total_pages = len(page_byte_list)

    # 3. Generate and store cover thumbnail from page 1
    doc_id = doc_record["id"]
    thumb_record = None
    if page_byte_list:
        try:
            thumb_bytes = generate_pdf_thumbnail(page_byte_list[0])
            doc_stem = Path(clean_filename).stem
            thumb_record = save_raw_image(
                file_bytes=thumb_bytes,
                filename=f"{doc_stem}_thumb.png",
                mime_type="image/png",
                memory_id=doc_id,
            )
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail for PDF {clean_filename}: {e}")

    # 4. Save each page image & run GLM-OCR
    pages_data: List[Dict[str, Any]] = []
    aggregated_ocr_parts: List[str] = []
    doc_stem = Path(clean_filename).stem

    for idx, p_bytes in enumerate(page_byte_list):
        page_num = idx + 1
        page_filename = f"{doc_stem}_page_{page_num}.png"
        
        # Save page image to media store linked to parent doc
        page_record = save_raw_image(
            file_bytes=p_bytes,
            filename=page_filename,
            mime_type="image/png",
            memory_id=doc_id,
        )


        page_ocr_text = ""
        ocr_status = "skipped"

        if run_ocr:
            try:
                logger.info(f"Running GLM-OCR on {clean_filename} [Page {page_num}/{total_pages}]...")
                page_ocr_text = extract_text_with_ollama_ocr(
                    image_bytes=p_bytes,
                    prompt=custom_prompt,
                )
                ocr_status = "completed"
                update_media_ocr_result(
                    media_id=page_record["id"],
                    ocr_text=page_ocr_text,
                    ocr_status="completed",
                    ocr_model=constants.OLLAMA_OCR_MODEL,
                )
                page_record["ocr_text"] = page_ocr_text
                page_record["ocr_status"] = "completed"
            except Exception as e:
                logger.warning(f"GLM-OCR failed on {clean_filename} [Page {page_num}]: {e}")
                ocr_status = "failed"
                update_media_ocr_result(
                    media_id=page_record["id"],
                    ocr_text="",
                    ocr_status="failed",
                    ocr_model=constants.OLLAMA_OCR_MODEL,
                )
                page_record["ocr_status"] = "failed"

        pages_data.append({
            "page_number": page_num,
            "media_id": page_record["id"],
            "filename": page_record["filename"],
            "image_url": page_record["url"],
            "file_size": len(p_bytes),
            "ocr_status": ocr_status,
            "ocr_text": page_ocr_text,
        })

        if page_ocr_text.strip():
            aggregated_ocr_parts.append(f"#### Page {page_num}\n{page_ocr_text.strip()}")

    aggregated_ocr_text = "\n\n".join(aggregated_ocr_parts)

    # 5. Update main document record OCR summary
    if aggregated_ocr_text:
        update_media_ocr_result(
            media_id=doc_record["id"],
            ocr_text=aggregated_ocr_text,
            ocr_status="completed" if run_ocr else "skipped",
            ocr_model=constants.OLLAMA_OCR_MODEL,
        )
        doc_record["ocr_text"] = aggregated_ocr_text
        doc_record["ocr_status"] = "completed"

    # 6. Assemble clean markdown card
    thumb_url = thumb_record["url"] if thumb_record else doc_record["url"]
    download_url = f"/api/media/download/{doc_record['filename']}"
    view_url = doc_record["url"]
    orig_name = doc_record.get("original_filename") or clean_filename

    markdown_card = (
        f"[![PDF Document: {orig_name}]({thumb_url})]({view_url})\n"
        f"> 📄 **Document:** [{orig_name}]({view_url}) • *({total_pages} page{'s' if total_pages > 1 else ''})* — [⬇️ Download Original PDF]({download_url})\n\n"
        f"---\n\n"
        f"### Extracted Document Content (GLM-OCR)\n\n"
        f"{aggregated_ocr_text if aggregated_ocr_text else '*No readable text extracted or OCR skipped.*'}\n"
    )

    return {
        "status": "success",
        "document": {
            "id": doc_record["id"],
            "filename": doc_record["filename"],
            "original_filename": orig_name,
            "url": view_url,
            "download_url": download_url,
            "thumbnail_url": thumb_url,
            "page_count": total_pages,
            "file_size": len(file_bytes),
            "ocr_status": "completed" if aggregated_ocr_text else "skipped",
            "ocr_text": aggregated_ocr_text,
        },
        "pages": pages_data,
        "markdown_insertion": markdown_card,
    }


@handle_errors
def reprocess_single_page_ocr(
    page_identifier: str,
    custom_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Re-runs local Ollama GLM-OCR on an individual page image with optional custom prompt.
    """
    record = get_media_record(page_identifier)
    if not record:
        record = get_media_record_by_filename(page_identifier)

    if not record:
        raise ValueError(f"Media record '{page_identifier}' not found.")

    file_path = get_media_file_path(record["filename"])
    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"Physical file '{record['filename']}' not found on disk.")

    with open(file_path, "rb") as f:
        image_bytes = f.read()

    ocr_text = extract_text_with_ollama_ocr(
        image_bytes=image_bytes,
        prompt=custom_prompt,
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
        "filename": record["filename"],
        "ocr_status": "completed",
        "ocr_text": ocr_text,
        "ocr_model": constants.OLLAMA_OCR_MODEL,
    }
