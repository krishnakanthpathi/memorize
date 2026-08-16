import os
import shutil
import tempfile
import unittest
from pathlib import Path

import config.constants as constants
from core.memory_merger import (
    deterministic_merge_memories,
    find_correlated_memories,
    merge_memories_service,
    progressive_llm_merge,
)
from core.memory_service import execute_upsert_memory
from storage.db_manager import get_all_memories, get_memory_by_id, init_db
from storage.markdown_handler import read_markdown_file


class TestMemoryMerger(unittest.TestCase):
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

    def test_merge_two_memories_deterministic(self):
        """Test merging two related memories deterministically with source cleanup."""
        # 1. Create two memories
        res1 = execute_upsert_memory(
            title="FastAPI Routing Guide",
            content="FastAPI uses APIRouter to organize endpoints into modular files.",
            category="development",
            tags=["fastapi", "python", "backend"],
        )
        mem1_id = res1["memory_id"]

        res2 = execute_upsert_memory(
            title="FastAPI Dependency Injection",
            content="FastAPI provides Depends() for modular authentication and database sessions.",
            category="development",
            tags=["fastapi", "dependencies", "architecture"],
        )
        mem2_id = res2["memory_id"]

        self.assertIsNotNone(get_memory_by_id(mem1_id))
        self.assertIsNotNone(get_memory_by_id(mem2_id))

        # 2. Merge memories
        merge_res = merge_memories_service(
            memory_ids=[mem1_id, mem2_id],
            target_title="Comprehensive FastAPI Architecture",
            target_category="development",
            target_tags=["fastapi", "production"],
            delete_sources=True,
        )

        self.assertEqual(merge_res["status"], "success")
        self.assertEqual(merge_res["title"], "Comprehensive FastAPI Architecture")
        self.assertEqual(merge_res["merged_memory_id"], mem1_id)
        self.assertEqual(merge_res["merged_source_count"], 2)
        self.assertIn(mem2_id, merge_res["deleted_source_ids"])

        # Check primary memory is updated and contains combined tags
        merged_mem = get_memory_by_id(mem1_id)
        self.assertIsNotNone(merged_mem)
        self.assertEqual(merged_mem["title"], "Comprehensive FastAPI Architecture")
        self.assertIn("fastapi", merged_mem["tags"])
        self.assertIn("dependencies", merged_mem["tags"])
        self.assertIn("production", merged_mem["tags"])

        # Check secondary memory is deleted
        self.assertIsNone(get_memory_by_id(mem2_id))

        # Check file content on disk
        file_path = Path(merged_mem["file_path"])
        self.assertTrue(file_path.exists())
        _, content = read_markdown_file(file_path)
        self.assertIn("APIRouter", content)
        self.assertIn("Depends()", content)

    def test_merge_with_keep_originals(self):
        """Test merging when delete_sources is False (keeps original source notes)."""
        res1 = execute_upsert_memory(
            title="Linear Algebra Basics",
            content="Vectors and matrices are fundamental building blocks of AI.",
            category="education",
            tags=["math", "linear-algebra"],
        )
        mem1_id = res1["memory_id"]

        res2 = execute_upsert_memory(
            title="Dot Product and Cosine Similarity",
            content="Cosine similarity measures the angle between two vectors.",
            category="education",
            tags=["math", "similarity"],
        )
        mem2_id = res2["memory_id"]

        merge_res = merge_memories_service(
            memory_ids=[mem1_id, mem2_id],
            target_title="Master Linear Algebra for Embeddings",
            delete_sources=False,
        )

        self.assertEqual(merge_res["status"], "success")
        self.assertEqual(len(merge_res["deleted_source_ids"]), 0)

        # Both records must still exist in SQLite
        self.assertIsNotNone(get_memory_by_id(mem1_id))
        self.assertIsNotNone(get_memory_by_id(mem2_id))

    def test_find_correlated_memories(self):
        """Test finding correlated memories based on tags and category matches."""
        res1 = execute_upsert_memory(
            title="Ollama Setup Guide",
            content="Running local LLMs with Ollama CLI and Modelfile configurations.",
            category="development",
            tags=["ollama", "llm", "local-ai"],
        )
        mem1_id = res1["memory_id"]

        res2 = execute_upsert_memory(
            title="GLM-OCR Ollama Debugging",
            content="Fixing loop issues and context window overflows in Ollama OCR.",
            category="development",
            tags=["ollama", "ocr", "debugging"],
        )
        mem2_id = res2["memory_id"]

        res3 = execute_upsert_memory(
            title="Weekend Grocery List",
            content="Milk, eggs, coffee beans, and bread.",
            category="personal",
            tags=["groceries", "home"],
        )

        correlations = find_correlated_memories(mem1_id, top_k=5)
        self.assertTrue(len(correlations) >= 1)

        # The GLM-OCR note should be the top correlated candidate due to shared 'ollama' tag and 'development' category
        top_cand = correlations[0]
        self.assertEqual(top_cand["id"], mem2_id)
        self.assertIn("ollama", top_cand["shared_tags"])
        self.assertTrue(top_cand["same_category"])
        self.assertTrue(top_cand["similarity_percent"] > 0)

    def test_merge_validation_errors(self):
        """Test error handling when fewer than 2 memories are provided."""
        res = merge_memories_service(memory_ids=["single_id_only"])
        self.assertEqual(res["status"], "error")
        self.assertIn("At least 2 memory IDs", res["message"])

        res_invalid = merge_memories_service(memory_ids=["non_existent_1", "non_existent_2"])
        self.assertEqual(res_invalid["status"], "error")


if __name__ == "__main__":
    unittest.main()
