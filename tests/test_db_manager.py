from pathlib import Path
import tempfile
import unittest

from storage.db_manager import (
    clear_all_index_memories,
    delete_memory_from_index,
    find_memory_by_title_or_slug,
    get_all_memories,
    get_memory_by_id,
    init_db,
    upsert_memory_index,
)


import config.constants as constants


class TestDBManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        
        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH

        constants.DATA_DIR = self.tmp_path / "data"
        constants.DB_PATH = constants.DATA_DIR / "test_db_manager.db"
        constants.DATA_DIR.mkdir(parents=True, exist_ok=True)

        init_db()

    def tearDown(self):
        constants.DATA_DIR = self.orig_data_dir
        constants.DB_PATH = self.orig_db_path
        self.tmp_dir.cleanup()


    def test_upsert_and_get_memory(self):
        """Test inserting, updating, and querying memory entries in SQLite."""
        memory_entry = {
            "id": "mem_test123",
            "title": "User Profile",
            "category": "personal",
            "tags": ["user", "profile"],
            "file_path": "/tmp/memories/personal/user_profile.md",
            "content": "User Krishnakanth profile notes.",
            "created_at": "2026-08-05T10:00:00Z",
        }

        # Insert
        upserted = upsert_memory_index(memory_entry)
        self.assertEqual(upserted["id"], "mem_test123")
        self.assertEqual(upserted["title"], "User Profile")
        self.assertIn("user", upserted["tags"])

        # Query by ID
        fetched = get_memory_by_id("mem_test123")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["title"], "User Profile")

        # Query by Title / Slug
        by_slug = find_memory_by_title_or_slug("User Profile", "personal")
        self.assertIsNotNone(by_slug)
        self.assertEqual(by_slug["id"], "mem_test123")

        # Update
        memory_entry["content"] = "Updated User Krishnakanth profile notes with more details."
        updated = upsert_memory_index(memory_entry)
        self.assertIn("more details", updated["snippet"])

        # Delete
        deleted = delete_memory_from_index("mem_test123")
        self.assertTrue(deleted)
        self.assertIsNone(get_memory_by_id("mem_test123"))


if __name__ == "__main__":
    unittest.main()
