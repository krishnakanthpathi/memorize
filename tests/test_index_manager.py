import json
from pathlib import Path
import tempfile
import unittest

from storage.index_manager import (
    add_memory_to_index,
    get_initial_index_structure,
    load_index,
    save_index,
)


class TestIndexManager(unittest.TestCase):

    def test_load_and_save_index(self):
        """Test loading, saving, and atomic file replace for index.json."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_index_path = Path(tmp_dir) / "index.json"

            import storage.index_manager
            original_index_path = storage.index_manager.INDEX_PATH
            storage.index_manager.INDEX_PATH = test_index_path

            try:
                # 1. Load missing index -> seeds fresh structure
                index_data = load_index()
                self.assertEqual(index_data["total_memories"], 0)
                self.assertTrue(test_index_path.exists())

                # 2. Add memory entry
                memory_entry = {
                    "id": "mem_test123",
                    "title": "Test Memory",
                    "category": "personal",
                    "tags": ["test", "demo"],
                    "file_path": str(Path(tmp_dir) / "personal" / "test.md"),
                    "created_at": "2026-08-02T10:00:00Z",
                }

                updated_index = add_memory_to_index(memory_entry)
                self.assertEqual(updated_index["total_memories"], 1)
                self.assertEqual(updated_index["categories"]["personal"]["count"], 1)
                self.assertIn("mem_test123", updated_index["tag_index"]["test"])

            finally:
                storage.index_manager.INDEX_PATH = original_index_path


if __name__ == "__main__":
    unittest.main()
