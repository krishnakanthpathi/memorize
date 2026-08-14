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


import config.constants as constants


class TestMemoryService(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        
        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH
        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_backup_dir = constants.BACKUP_DIR

        constants.DATA_DIR = self.tmp_path / "data"
        constants.DB_PATH = constants.DATA_DIR / "test.db"
        constants.MEMORIES_DIR = constants.DATA_DIR / "memories"
        constants.BACKUP_DIR = constants.DATA_DIR / "backups"
        constants.DATA_DIR.mkdir(parents=True, exist_ok=True)
        constants.MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
        constants.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        import vector.vector_db
        self.orig_chroma_dir = vector.vector_db.CHROMA_DIR
        vector.vector_db.CHROMA_DIR = self.tmp_path / "chroma_db"
        vector.vector_db.CHROMA_CLIENT = None

        init_db()

    def tearDown(self):
        import vector.vector_db
        vector.vector_db.CHROMA_CLIENT = None
        vector.vector_db.CHROMA_DIR = self.orig_chroma_dir

        constants.DATA_DIR = self.orig_data_dir
        constants.DB_PATH = self.orig_db_path
        constants.MEMORIES_DIR = self.orig_memories_dir
        constants.BACKUP_DIR = self.orig_backup_dir

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
