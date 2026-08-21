import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pypdfium2

import config.constants as constants
from api.server import app
from media.pdf_processor import (
    generate_pdf_thumbnail,
    process_pdf_document,
    render_pdf_pages_to_images,
    reprocess_single_page_ocr,
)
from storage.media_store_manager import (
    delete_all_orphan_media,
    delete_media_item,
    get_media_download_info,
    list_orphan_media_files,
)
from mcp.tools.media_tools import register_media_tools


def create_sample_multipage_pdf(num_pages: int = 2) -> bytes:
    """Creates an in-memory valid multi-page PDF byte stream using pypdfium2."""
    pdf = pypdfium2.PdfDocument.new()
    for _ in range(num_pages):
        pdf.new_page(width=300, height=400)
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


class TestPdfProcessorAndMediaAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.temp_dir = tempfile.mkdtemp()
        self.orig_media_dir = constants.MEDIA_DIR
        constants.MEDIA_DIR = Path(self.temp_dir)
        constants.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.sample_pdf_bytes = create_sample_multipage_pdf(2)
        self.created_media_ids = []

    def tearDown(self):
        for mid in self.created_media_ids:
            delete_media_item(mid)
        constants.MEDIA_DIR = self.orig_media_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_render_pdf_pages_to_images(self):
        """Verify pypdfium2 renders each PDF page to a valid PNG image byte stream."""
        images = render_pdf_pages_to_images(self.sample_pdf_bytes, dpi=100)
        self.assertEqual(len(images), 2)
        # PNG signature check: \x89PNG\r\n\x1a\n
        for img_bytes in images:
            self.assertTrue(img_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_generate_pdf_thumbnail(self):
        """Verify thumbnail generation from first page image."""
        images = render_pdf_pages_to_images(self.sample_pdf_bytes, dpi=100)
        thumb = generate_pdf_thumbnail(images[0], max_size=(100, 100))
        self.assertTrue(thumb.startswith(b"\x89PNG\r\n\x1a\n"))

    @patch("media.pdf_processor.extract_text_with_ollama_ocr")
    def test_process_pdf_document_flow(self, mock_ocr):
        """Verify end-to-end PDF processing: storing PDF, rendering pages, and GLM-OCR aggregation."""
        mock_ocr.side_effect = [
            "Executive summary and introduction.",
            "Quarterly metrics and balance sheet table.",
        ]

        result = process_pdf_document(
            file_bytes=self.sample_pdf_bytes,
            filename="quarterly_report.pdf",
            run_ocr=True,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["document"]["page_count"], 2)
        self.assertIn("download_url", result["document"])
        self.assertEqual(len(result["pages"]), 2)
        self.created_media_ids.append(result["document"]["id"])
        for p in result["pages"]:
            self.created_media_ids.append(p["media_id"])

        # Check markdown structure
        md = result["markdown_insertion"]
        self.assertIn("quarterly_report.pdf", md)
        self.assertIn("Page 1", md)
        self.assertIn("Executive summary", md)
        self.assertIn("Quarterly metrics", md)

    @patch("media.pdf_processor.extract_text_with_ollama_ocr")
    def test_api_upload_pdf(self, mock_ocr):
        """Verify REST API /api/documents/upload-pdf endpoint."""
        mock_ocr.return_value = "API OCR text extracted from page."

        files = {
            "file": ("spec.pdf", self.sample_pdf_bytes, "application/pdf"),
        }
        resp = self.client.post("/api/documents/upload-pdf", files=files, data={"run_ocr": "true"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["document"]["page_count"], 2)
        self.created_media_ids.append(data["document"]["id"])

    def test_media_download_endpoint(self):
        """Verify GET /api/media/download/{filename} sets attachment header."""
        # Process without OCR
        result = process_pdf_document(
            file_bytes=self.sample_pdf_bytes,
            filename="my_doc.pdf",
            run_ocr=False,
        )
        self.created_media_ids.append(result["document"]["id"])
        doc_filename = result["document"]["filename"]

        resp = self.client.get(f"/api/media/download/{doc_filename}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp.headers.get("content-disposition", ""))
        self.assertEqual(resp.content, self.sample_pdf_bytes)

    def test_orphan_media_cleanup_api(self):
        """Verify orphan media detection and purge endpoints."""
        # Create an unreferenced dummy file on disk
        dummy_file = constants.MEDIA_DIR / "orphan_test_file.png"
        dummy_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"dummy")

        resp = self.client.get("/api/media/orphans")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_orphans"], 1)

        # Clean up
        clean_resp = self.client.post("/api/media/cleanup-orphans")
        self.assertEqual(clean_resp.status_code, 200)
        self.assertFalse(dummy_file.exists())

    def test_mcp_media_tools(self):
        """Verify MCP tools registration and link generation."""
        mock_mcp = MagicMock()
        registered_tools = {}

        def tool_decorator():
            def wrapper(fn):
                registered_tools[fn.__name__] = fn
                return fn
            return wrapper

        mock_mcp.tool = tool_decorator
        register_media_tools(mock_mcp)

        self.assertIn("attach_document_or_media", registered_tools)
        self.assertIn("get_media_download_link", registered_tools)
        self.assertIn("list_unlinked_media_files", registered_tools)
        self.assertIn("cleanup_unlinked_media", registered_tools)


if __name__ == "__main__":
    unittest.main()
