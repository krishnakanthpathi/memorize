import io
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import config.constants as constants
from api.server import app
from storage.db_manager import (
    delete_media_record,
    get_media_record,
    get_media_record_by_filename,
    get_media_record_by_hash,
    list_all_media_records,
    update_media_ocr_result,
)
from storage.media_store_manager import (
    compute_bytes_hash,
    delete_media_item,
    get_media_file_path,
    list_orphan_media_files,
    save_raw_image,
)
from utils.llm_client import extract_text_with_ollama_ocr


import tempfile
import shutil

class TestMediaStoreAndOCR(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.temp_dir = tempfile.mkdtemp()
        self.orig_media_dir = constants.MEDIA_DIR
        constants.MEDIA_DIR = Path(self.temp_dir)
        constants.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        # Dummy uncompressed image payload
        self.sample_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        self.created_media_ids = []

    def tearDown(self):
        for mid in self.created_media_ids:
            delete_media_item(mid)
        constants.MEDIA_DIR = self.orig_media_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)


    def test_save_raw_image_uncompressed(self):
        """Verify images are saved uncompressed with exact byte match and SHA-256 hash."""
        record = save_raw_image(
            file_bytes=self.sample_bytes,
            filename="architecture_diagram.png",
            mime_type="image/png",
        )
        self.created_media_ids.append(record["id"])

        self.assertIn("id", record)
        self.assertEqual(record["file_size"], len(self.sample_bytes))
        self.assertEqual(record["content_hash"], compute_bytes_hash(self.sample_bytes))
        self.assertTrue(record["url"].startswith("/api/media/"))

        # Verify disk file is 100% byte-for-byte identical
        stored_path = Path(record["file_path"])
        self.assertTrue(stored_path.exists())
        with open(stored_path, "rb") as f:
            disk_bytes = f.read()
        self.assertEqual(disk_bytes, self.sample_bytes)

    def test_image_deduplication(self):
        """Verify uploading the exact same image content reuses the existing record."""
        record1 = save_raw_image(self.sample_bytes, "original_1.png")
        self.created_media_ids.append(record1["id"])

        record2 = save_raw_image(self.sample_bytes, "duplicate_copy.png")
        self.assertEqual(record1["id"], record2["id"])
        self.assertEqual(record1["file_path"], record2["file_path"])
        self.assertTrue(record2.get("is_duplicate", False))

    def test_sqlite_media_tracking(self):
        """Verify DB queries and OCR updates."""
        record = save_raw_image(self.sample_bytes, "test_ocr.png")
        self.created_media_ids.append(record["id"])

        db_rec = get_media_record(record["id"])
        self.assertIsNotNone(db_rec)
        self.assertEqual(db_rec["filename"], record["filename"])

        # Update OCR result
        update_media_ocr_result(
            media_id=record["id"],
            ocr_text="Architecture: FastAPI + SQLite + ChromaDB",
            ocr_status="completed",
            ocr_model="glm-ocr",
        )

        updated_rec = get_media_record(record["id"])
        self.assertEqual(updated_rec["ocr_status"], "completed")
        self.assertIn("FastAPI", updated_rec["ocr_text"])

    @patch("utils.llm_client.requests.post")
    def test_ollama_ocr_client(self, mock_post):
        """Verify extract_text_with_ollama_ocr formats payload correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "# Extracted Heading\n- Item 1\n- Item 2\n$$E = mc^2$$"
        }
        mock_post.return_value = mock_response

        extracted = extract_text_with_ollama_ocr(
            image_bytes=self.sample_bytes,
            prompt="Extract text",
            model="glm-ocr",
        )

        self.assertIn("# Extracted Heading", extracted)
        self.assertIn("E = mc^2", extracted)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["model"], "glm-ocr")
        self.assertEqual(len(kwargs["json"]["images"]), 1)

    @patch("api.routes.media.extract_text_with_ollama_ocr")
    def test_api_upload_and_serve(self, mock_ocr):
        """Verify /api/media/upload and /api/media/{filename} endpoints."""
        mock_ocr.return_value = "Extracted OCR text from sample"

        # Upload multipart file
        response = self.client.post(
            "/api/media/upload",
            files={"file": ("test_upload.png", io.BytesIO(self.sample_bytes), "image/png")},
            data={"run_ocr": "true"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        media = data["media"]
        self.created_media_ids.append(media["id"])
        self.assertEqual(data["ocr"]["text"], "Extracted OCR text from sample")

        # Fetch served file
        filename = media["filename"]
        serve_resp = self.client.get(f"/api/media/{filename}")
        self.assertEqual(serve_resp.status_code, 200)
        self.assertEqual(serve_resp.content, self.sample_bytes)
        self.assertIn("public", serve_resp.headers.get("cache-control", ""))

    def test_api_media_list_and_delete(self):
        """Verify list and delete endpoints."""
        record = save_raw_image(self.sample_bytes, "to_delete.png")
        mid = record["id"]

        # List
        list_resp = self.client.get("/api/media/list")
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(m["id"] == mid for m in list_resp.json()["media"]))

        # Delete
        del_resp = self.client.delete(f"/api/media/{mid}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertTrue(del_resp.json()["deleted"])
        self.assertIsNone(get_media_record(mid))


if __name__ == "__main__":
    unittest.main()
