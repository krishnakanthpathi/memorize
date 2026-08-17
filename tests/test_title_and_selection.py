import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import config.constants as constants
from core.memory_merger import (
    clean_generated_title,
    generate_title_service,
    organize_selection_service,
    organize_single_memory_service,
)
from core.memory_service import execute_upsert_memory
from storage.db_manager import get_memory_by_id, init_db


class TestTitleAndSelection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patch_data_dir = Path(self.temp_dir) / "data"
        self.patch_db_path = self.patch_data_dir / "memorize_test.db"

        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH
        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_backup_dir = constants.BACKUP_DIR
        self.orig_use_llm = constants.USE_LLM

        constants.DATA_DIR = self.patch_data_dir
        constants.DB_PATH = self.patch_db_path
        constants.MEMORIES_DIR = self.patch_data_dir / "memories"
        constants.BACKUP_DIR = self.patch_data_dir / "backups"
        constants.USE_LLM = False

        constants.DATA_DIR.mkdir(parents=True, exist_ok=True)
        constants.MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
        constants.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        import vector.vector_db
        self.orig_chroma_dir = vector.vector_db.CHROMA_DIR
        vector.vector_db.CHROMA_DIR = Path(self.temp_dir) / "chroma_db"
        vector.vector_db.CHROMA_CLIENT = None

        init_db()

    def tearDown(self):
        import vector.vector_db
        constants.DATA_DIR = self.orig_data_dir
        constants.MEMORIES_DIR = self.orig_memories_dir
        constants.BACKUP_DIR = self.orig_backup_dir
        constants.DB_PATH = self.orig_db_path
        constants.USE_LLM = self.orig_use_llm
        vector.vector_db.CHROMA_DIR = self.orig_chroma_dir
        vector.vector_db.CHROMA_CLIENT = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_generated_title(self):
        self.assertEqual(clean_generated_title('"Modern React Architecture"'), "Modern React Architecture")
        self.assertEqual(clean_generated_title('Title: Modern React Architecture'), "Modern React Architecture")
        self.assertEqual(clean_generated_title('# Modern React Architecture'), "Modern React Architecture")
        self.assertEqual(clean_generated_title('**Modern React Architecture**'), "Modern React Architecture")
        self.assertEqual(clean_generated_title('1. Modern React Architecture'), "Modern React Architecture")

    def test_generate_title_heuristic(self):
        content = "# Distributed Consensus in Raft\nRaft is a consensus algorithm designed for fault tolerance."
        title = generate_title_service(content, use_ai=False)
        self.assertEqual(title, "Distributed Consensus in Raft")

        raw_content = "Docker multi-stage builds reduce container image sizes significantly."
        title2 = generate_title_service(raw_content, use_ai=False)
        self.assertTrue(len(title2) > 0)
        self.assertIn("Docker", title2)

    def test_organize_selection_service(self):
        snippet = "some unformatted text here with typo"
        res = organize_selection_service(
            selected_text=snippet,
            mode="polish",
            use_ai=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["action"], "transformed")
        self.assertEqual(res["transformed_text"], snippet)

        title_res = organize_selection_service(
            selected_text="# Advanced Vector Indexing with HNSW",
            mode="title",
            use_ai=False,
        )
        self.assertEqual(title_res["status"], "success")
        self.assertEqual(title_res["title"], "Advanced Vector Indexing with HNSW")

    def test_organize_single_memory_with_title_generation(self):
        created = execute_upsert_memory(
            title="Untitled Note",
            content="# Redis Caching Best Practices\nRedis provides ultra-fast in-memory key-value caching.",
            category="development",
            tags=["redis", "cache"],
        )
        mem_id = created["memory_id"]

        org_res = organize_single_memory_service(
            memory_id=mem_id,
            use_ai=False,
            generate_title=True,
        )
        self.assertEqual(org_res["status"], "success")
        self.assertEqual(org_res["action"], "organized")
        self.assertEqual(org_res["title"], "Redis Caching Best Practices")

        # Verify in database
        updated = get_memory_by_id(mem_id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["title"], "Redis Caching Best Practices")

    def test_api_generate_title_and_transform_selection(self):
        from api.server import app
        client = TestClient(app)

        # 1. Test POST /api/memories/generate-title
        resp = client.post(
            "/api/memories/generate-title",
            json={
                "content": "# GraphQL API Design Guide\nGraphQL provides declarative data fetching.",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(len(data["title"]) > 0)

        # 2. Test POST /api/memories/transform-selection
        resp2 = client.post(
            "/api/memories/transform-selection",
            json={
                "selected_text": "def calculate_hash(data):\n    return hashlib.sha256(data).hexdigest()",
                "mode": "technical",
            },
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["status"], "success")
        self.assertIn("calculate_hash", data2["transformed_text"])


if __name__ == "__main__":
    unittest.main()
