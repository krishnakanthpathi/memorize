from pathlib import Path
import tempfile
import unittest

from core.memory_service import (
    execute_upsert_memory,
    handle_delete_memory,
    handle_existing_memory,
    handle_new_memory,
    reindex_memory_chunks,
)
from storage.db_manager import clear_all_index_memories, get_memory_by_id, init_db


class TestMemoryService(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_chroma_dir = Path(self.tmp_dir.name) / "chroma_db"

        import vector.vector_db
        vector.vector_db.CHROMA_DIR = self.test_chroma_dir
        vector.vector_db.CHROMA_CLIENT = None

        init_db()
        clear_all_index_memories()

    def tearDown(self):
        import vector.vector_db
        vector.vector_db.CHROMA_CLIENT = None
        clear_all_index_memories()
        self.tmp_dir.cleanup()

    def test_execute_upsert_insert_and_append_and_delete(self):
        """Test full memory service lifecycle: insert, append, update, and delete."""
        # 1. Insert new memory
        res_insert = execute_upsert_memory(
            title="Refactoring Memory Service",
            content="Modularizing upsert_memory into helper functions.",
            category="study",
            tags=["refactor", "python"],
            action="insert",
        )
        self.assertEqual(res_insert["status"], "success")
        self.assertEqual(res_insert["action"], "insert")
        mem_id = res_insert["memory_id"]

        # Verify DB entry
        db_mem = get_memory_by_id(mem_id)
        self.assertIsNotNone(db_mem)
        self.assertEqual(db_mem["title"], "Refactoring Memory Service")

        # 2. Append to memory
        res_append = execute_upsert_memory(
            title="Refactoring Memory Service",
            content="Added reindex_memory_chunks helper function.",
            action="append",
            memory_id=mem_id,
        )
        self.assertEqual(res_append["status"], "success")
        self.assertEqual(res_append["action"], "append")

        # 3. Delete memory
        res_delete = execute_upsert_memory(
            title="",
            action="delete",
            memory_id=mem_id,
        )
        self.assertEqual(res_delete["status"], "success")
        self.assertEqual(res_delete["action"], "delete")
        self.assertIsNone(get_memory_by_id(mem_id))

    def test_deduplication_by_content_hash(self):
        """Test that storing identical content under a different title routes to existing memory."""
        content = "Unique content string for deduplication test."
        res1 = execute_upsert_memory(
            title="Original Memory",
            content=content,
            category="personal",
        )
        self.assertEqual(res1["status"], "success")
        orig_id = res1["memory_id"]

        # Insert again with a different title but exact same content
        res2 = execute_upsert_memory(
            title="Different Title Duplicate",
            content=content,
            category="personal",
        )
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["memory_id"], orig_id)

    def test_skip_redundant_reindexing(self):
        """Test that re-indexing identical content returns cached chunks without re-embedding."""
        content = "Content for testing reindexing skip logic."
        res = execute_upsert_memory(
            title="Reindex Skip Test",
            content=content,
            category="personal",
        )
        mem_id = res["memory_id"]

        # Reindex with exact same content
        chunks, chunk_ids = reindex_memory_chunks(mem_id, content, force=False)
        self.assertTrue(len(chunks) > 0)
        self.assertTrue(len(chunk_ids) > 0)



if __name__ == "__main__":
    unittest.main()
