import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from storage.db_manager import init_db
from storage.sync_manager import clear_all_memories, get_memory_file_status


class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_memories_dir = Path(self.tmp_dir.name) / "memories"
        self.test_memories_dir.mkdir(parents=True, exist_ok=True)
        self.patcher = patch("storage.sync_manager.MEMORIES_DIR", self.test_memories_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tmp_dir.cleanup()

    def test_clear_all_memories(self):
        result = clear_all_memories(clear_backups=False)
        self.assertEqual(result["status"], "success")

    def test_get_memory_file_status_nonexistent(self):
        result = get_memory_file_status("nonexistent_id")
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
