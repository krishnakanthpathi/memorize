import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from storage.db_manager import init_db
from storage.sync_manager import clear_all_memories, get_memory_file_status


from storage.sync_manager import (
    audit_storage_integrity,
    clear_all_memories,
    delete_orphan_chunks,
    delete_orphan_files,
    delete_orphan_indexes,
    find_orphan_chunks,
    find_orphan_files,
    find_orphan_indexes,
    get_memory_file_status,
    recover_orphaned_documents,
)


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

    def test_orphan_detection_and_audit(self):
        # Create an orphan file on disk
        orphan_path = self.test_memories_dir / "orphan_test.md"
        orphan_path.write_text("---\ntitle: Orphan Test\n---\nOrphan content", encoding="utf-8")

        orphans = find_orphan_files()
        self.assertGreaterEqual(len(orphans), 1)

        report = audit_storage_integrity(auto_fix=False)
        self.assertIn("summary", report)
        self.assertGreaterEqual(report["summary"]["orphan_files_count"], 1)

    def test_recover_orphaned_documents(self):
        orphan_path = self.test_memories_dir / "recover_test.md"
        orphan_path.write_text("Unindexed memory content to recover", encoding="utf-8")

        rec_res = recover_orphaned_documents()
        self.assertEqual(rec_res["status"], "success")
        self.assertGreaterEqual(rec_res["recovered_count"], 1)


if __name__ == "__main__":
    unittest.main()

