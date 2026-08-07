import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from storage.db_manager import get_all_memories, init_db
from storage.sync_manager import sync_markdown_files


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

    def test_manual_markdown_file_sync(self):
        study_dir = self.test_memories_dir / "personal"
        study_dir.mkdir(parents=True, exist_ok=True)
        test_file = study_dir / "manual_test_note.md"

        raw_content = "---\ntitle: Manual Note\ntags: [unit_test, sync]\n---\n\nThis is a manual markdown note created directly on disk to test auto-chunking and sync."
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(raw_content)

        # Run sync
        result = sync_markdown_files()
        self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()
