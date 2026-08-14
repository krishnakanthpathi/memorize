import os
from pathlib import Path
import tempfile
import unittest

import config.constants as constants
from storage.backup_manager import (
    backup_all_memories,
    generate_backup_readme,
    get_backup_readme,
    restore_memories_from_backup,
)
from storage.db_manager import (
    get_all_memories,
    get_memory_by_id,
    init_db,
    upsert_memory_index,
)
from storage.markdown_handler import create_markdown_file


class TestDBPersistenceAndBackup(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH
        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_backup_dir = constants.BACKUP_DIR
        self.orig_backup_memories_dir = constants.BACKUP_MEMORIES_DIR

        constants.DATA_DIR = self.tmp_path / "data"
        constants.DB_PATH = constants.DATA_DIR / "test_backup.db"
        constants.MEMORIES_DIR = constants.DATA_DIR / "memories"
        constants.BACKUP_DIR = constants.DATA_DIR / "backups"
        constants.BACKUP_MEMORIES_DIR = constants.BACKUP_DIR / "memories"

        constants.DATA_DIR.mkdir(parents=True, exist_ok=True)
        constants.MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
        constants.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        constants.BACKUP_MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

        init_db()

    def tearDown(self):
        constants.DATA_DIR = self.orig_data_dir
        constants.DB_PATH = self.orig_db_path
        constants.MEMORIES_DIR = self.orig_memories_dir
        constants.BACKUP_DIR = self.orig_backup_dir
        constants.BACKUP_MEMORIES_DIR = self.orig_backup_memories_dir

        self.tmp_dir.cleanup()

    def test_full_content_storage_in_sqlite(self):
        test_id = "mem_test_content_123"
        test_title = "Database Content Persistence Test"
        test_content = "This is a full content test body stored directly inside SQLite database."

        mem_entry = {
            "id": test_id,
            "title": test_title,
            "category": "development",
            "tags": ["test", "sqlite"],
            "file_path": str(self.tmp_path / "test_content_123.md"),
            "content": test_content,
            "content_hash": "dummyhash123",
        }

        upsert_memory_index(mem_entry)
        fetched = get_memory_by_id(test_id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], test_id)
        self.assertEqual(fetched["content"], test_content)

    def test_backup_and_restore_memories(self):
        test_id = "mem_test_restore_456"
        test_title = "Vanished Memory File Recovery Test"
        test_content = "# Auto Rematerialize\nThis file was backed up."

        # Create file in isolated test memories dir
        created_path = create_markdown_file(
            memory_id=test_id,
            title=test_title,
            category="personal",
            tags=["rematerialize"],
            content=test_content,
        )
        backup_all_memories()

        # Simulate accidental disk file deletion ("vanished file")
        self.assertTrue(created_path.exists())
        created_path.unlink()
        self.assertFalse(created_path.exists())

        # Restore from backup
        res = restore_memories_from_backup()
        self.assertEqual(res["status"], "success")
        self.assertTrue(created_path.exists())

        # Verify content restored on disk matches
        with open(created_path, "r", encoding="utf-8") as f:
            restored_text = f.read()
        self.assertIn(test_content, restored_text)

    def test_backup_and_readme_generation(self):
        # Create sample memories
        p1 = create_markdown_file(
            memory_id="mem_bkp_1",
            title="Backup Test Achievement",
            category="achievements",
            tags=["award"],
            content="Won first place hackathon.",
        )
        upsert_memory_index({
            "id": "mem_bkp_1",
            "title": "Backup Test Achievement",
            "category": "achievements",
            "tags": ["award"],
            "file_path": str(p1),
            "content": "Won first place hackathon.",
            "content_hash": "hash1",
        })

        p2 = create_markdown_file(
            memory_id="mem_bkp_2",
            title="Backup Test Dev Project",
            category="development",
            tags=["python"],
            content="Built high-performance async queue system.",
        )
        upsert_memory_index({
            "id": "mem_bkp_2",
            "title": "Backup Test Dev Project",
            "category": "development",
            "tags": ["python"],
            "file_path": str(p2),
            "content": "Built high-performance async queue system.",
            "content_hash": "hash2",
        })

        backup_res = backup_all_memories()
        self.assertEqual(backup_res["status"], "success")
        self.assertGreaterEqual(backup_res["backed_up_count"], 2)
        self.assertTrue(backup_res["database_snapshot"])
        self.assertTrue(backup_res["readme_generated"])

        readme_text = get_backup_readme()
        self.assertIn("MEMORIZE BACKUP REPOSITORY INDEX", readme_text)


if __name__ == "__main__":
    unittest.main()


