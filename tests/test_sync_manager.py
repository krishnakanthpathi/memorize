import os
from pathlib import Path
import unittest

from config.constants import MEMORIES_DIR
from storage.index_manager import load_index
from storage.sync_manager import (
    clear_all_memories,
    get_memory_file_status,
    sync_markdown_files,
)
from utils import get_category_dir


class TestSyncManager(unittest.TestCase):
    def setUp(self):
        # Clean state before each test
        clear_all_memories()

    def tearDown(self):
        clear_all_memories()

    def test_manual_markdown_file_sync(self):
        study_dir = get_category_dir("study")
        test_file = study_dir / "manual_test_note.md"

        # Create a raw markdown file directly on disk without frontmatter ID
        raw_content = "---\ntitle: Manual Note\ntags: [unit_test, sync]\n---\n\nThis is a manual markdown note created directly on disk to test auto-chunking and sync."
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(raw_content)

        # Run sync
        result = sync_markdown_files()
        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(result["added"], 1)

        # Verify index.json was updated
        index_data = load_index()
        self.assertEqual(index_data["total_memories"], 1)
        mem = index_data["memories"][0]
        self.assertEqual(mem["title"], "Manual Note")
        self.assertIn("unit_test", mem["tags"])

        # Verify status returner tool
        status = get_memory_file_status(mem["id"])
        self.assertEqual(status["status"], "success")
        self.assertTrue(status["exists"])
        self.assertTrue(status["is_indexed"])

    def test_clear_all_memories(self):
        study_dir = get_category_dir("study")
        test_file = study_dir / "note_to_clear.md"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Clear Test\n---\n\nNote content.")

        sync_markdown_files()
        self.assertEqual(load_index()["total_memories"], 1)

        # Clear memories
        clear_result = clear_all_memories()
        self.assertEqual(clear_result["status"], "success")
        self.assertEqual(load_index()["total_memories"], 0)


if __name__ == "__main__":
    unittest.main()
