"""
Media & Document MCP Tools for FastMCP.
Provides MCP AI agents with capabilities to attach documents/images with GLM-OCR,
generate file-sharing download links, and purge unlinked orphan media files.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from media.image_processor import process_image
from media.pdf_processor import process_pdf_document
from storage.media_store_manager import (
    delete_all_orphan_media,
    get_media_download_info,
    list_orphan_media_files,
)


def register_media_tools(mcp):
    """Register media, PDF, and file sharing MCP tools on the FastMCP server."""

    @mcp.tool()
    def attach_document_or_media(
        file_path: str,
        memory_id: Optional[str] = None,
        run_ocr: bool = True,
        custom_prompt: Optional[str] = None,
    ) -> dict:
        """
        Ingests an original local document (.pdf) or image (.png, .jpg, .webp, etc.),
        stores it uncompressed, renders PDF pages into images, executes local Ollama GLM-OCR,
        and returns the ready-to-insert Markdown badge/card and extracted text.
        """
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {
                "status": "error",
                "message": f"File '{file_path}' does not exist or is not a file.",
            }

        with open(p, "rb") as f:
            file_bytes = f.read()

        filename = p.name
        ext = p.suffix.lower()

        if ext == ".pdf":
            result = process_pdf_document(
                file_bytes=file_bytes,
                filename=filename,
                memory_id=memory_id,
                run_ocr=run_ocr,
                custom_prompt=custom_prompt,
            )
            return {
                "status": "success",
                "type": "pdf_document",
                "document": result["document"],
                "total_pages": len(result.get("pages", [])),
                "markdown_insertion": result["markdown_insertion"],
                "ocr_text": result["document"].get("ocr_text", ""),
            }
        else:
            # Standard image
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".bmp": "image/bmp",
            }
            mime_type = mime_map.get(ext, "image/png")
            result = process_image(
                file_bytes=file_bytes,
                filename=filename,
                mime_type=mime_type,
                memory_id=memory_id,
                run_ocr=run_ocr,
                custom_prompt=custom_prompt,
            )
            media_rec = result["media"]
            ocr_text = result["ocr"].get("text", "")
            download_url = f"/api/media/download/{media_rec['filename']}"
            view_url = f"/api/media/{media_rec['filename']}"

            markdown_card = f"![{filename}]({view_url})\n> 🖼️ **Image:** [{filename}]({view_url}) — [⬇️ Download]({download_url})\n"
            if ocr_text:
                markdown_card += f"\n### Extracted Content (GLM-OCR)\n{ocr_text}\n"

            return {
                "status": "success",
                "type": "image",
                "media": media_rec,
                "download_url": download_url,
                "markdown_insertion": markdown_card,
                "ocr_text": ocr_text,
            }

    @mcp.tool()
    def get_media_download_link(filename_or_id: str) -> dict:
        """
        Generates shareable direct download link and metadata for a stored media or document file.
        """
        info = get_media_download_info(filename_or_id)
        if not info:
            return {
                "status": "error",
                "message": f"Media file '{filename_or_id}' not found.",
            }
        return {
            "status": "success",
            "download_url": info["download_url"],
            "view_url": info["view_url"],
            "filename": info["filename"],
            "original_filename": info["original_filename"],
            "file_size": info["file_size"],
            "mime_type": info["mime_type"],
        }

    @mcp.tool()
    def list_unlinked_media_files() -> dict:
        """
        Scans data/media/ and lists all orphaned/unreferenced media and document files
        that are not linked to any active Markdown memory notes.
        """
        orphans = list_orphan_media_files()
        total_bytes = sum(o.get("file_size", 0) for o in orphans)
        return {
            "status": "success",
            "total_orphans": len(orphans),
            "total_bytes": total_bytes,
            "orphans": orphans,
        }

    @mcp.tool()
    def cleanup_unlinked_media(dry_run: bool = False) -> dict:
        """
        Safely removes unlinked orphan media and document files from data/media/
        and purges dangling database records.
        """
        if dry_run:
            orphans = list_orphan_media_files()
            total_bytes = sum(o.get("file_size", 0) for o in orphans)
            return {
                "status": "dry_run",
                "would_delete_count": len(orphans),
                "would_free_bytes": total_bytes,
                "orphans": [o["filename"] for o in orphans],
            }

        result = delete_all_orphan_media()
        return {
            "status": "success",
            **result,
        }

    return mcp
