import unittest
import tempfile
import shutil
from pathlib import Path
import config.constants as constants

from core.memory_service import execute_revert_memory, execute_upsert_memory
from storage.db_manager import (
    clear_all_index_memories,
    clear_all_memory_versions_from_db,
    get_memory_by_id,
    init_db,
)
from storage.version_manager import get_version_history


class TestVersionControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patch_data_dir = Path(self.temp_dir) / "data"
        self.patch_db_path = self.patch_data_dir / "memorize_test.db"

        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH
        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_backup_dir = constants.BACKUP_DIR

        constants.DATA_DIR = self.patch_data_dir
        constants.DB_PATH = self.patch_db_path
        constants.MEMORIES_DIR = self.patch_data_dir / "memories"
        constants.BACKUP_DIR = self.patch_data_dir / "backups"

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
        vector.vector_db.CHROMA_CLIENT = None
        vector.vector_db.CHROMA_DIR = self.orig_chroma_dir

        constants.DATA_DIR = self.orig_data_dir
        constants.DB_PATH = self.orig_db_path
        constants.MEMORIES_DIR = self.orig_memories_dir
        constants.BACKUP_DIR = self.orig_backup_dir

        shutil.rmtree(self.temp_dir, ignore_errors=True)


    def test_version_snapshots_and_reverting(self):
        # 1. Create initial memory
        res1 = execute_upsert_memory(
            title="User Profile",
            content="Name: Krishnakanth\nRole: Engineer\nTheme: Dark",
            category="personal",
            tags=["user"],
        )
        mem_id = res1["memory_id"]

        # 2. First update -> Version 1 snapshot created (snapshot of initial state)
        res2 = execute_upsert_memory(
            title="User Profile",
            content="Update 1: Likes Python and AI",
            action="update",
            category="personal",
            memory_id=mem_id,
        )

        history = get_version_history(mem_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["version_number"], 1)

        # 3. Second update -> Version 2 snapshot created
        res3 = execute_upsert_memory(
            title="User Profile",
            content="Update 2: Prefer Vite for frontend",
            action="update",
            category="personal",
            memory_id=mem_id,
        )

        history = get_version_history(mem_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["version_number"], 2)

        # 4. Third update -> Version 3 snapshot created
        res4 = execute_upsert_memory(
            title="User Profile",
            content="Update 3: Location updated to San Francisco",
            action="update",
            category="personal",
            memory_id=mem_id,
        )

        history = get_version_history(mem_id)
        self.assertEqual(len(history), 3)

        # 5. Fourth update -> Version 4 snapshot created, oldest version (1) pruned (max 3 retained)
        res5 = execute_upsert_memory(
            title="User Profile",
            content="Update 4: Switching back to Light Theme",
            action="update",
            category="personal",
            memory_id=mem_id,
        )

        history = get_version_history(mem_id)
        self.assertEqual(len(history), 3)  # Maximum 3 retained
        version_numbers = [h["version_number"] for h in history]
        self.assertEqual(version_numbers, [4, 3, 2])

        # 6. Revert memory to version 2
        revert_res = execute_revert_memory(memory_id=mem_id, version_number=2)
        self.assertEqual(revert_res["status"], "success")
        self.assertEqual(revert_res["restored_version"], 2)

        # Check DB memory content after revert
        reverted_mem = get_memory_by_id(mem_id)
        self.assertIsNotNone(reverted_mem)


if __name__ == "__main__":
    unittest.main()
