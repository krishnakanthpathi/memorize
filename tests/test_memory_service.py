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


if __name__ == "__main__":
    unittest.main()
