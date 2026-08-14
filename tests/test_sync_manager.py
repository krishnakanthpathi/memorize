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


import config.constants as constants


class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        self.orig_data_dir = constants.DATA_DIR
        self.orig_db_path = constants.DB_PATH
        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_backup_dir = constants.BACKUP_DIR

        constants.DATA_DIR = self.tmp_path / "data"
        constants.DB_PATH = constants.DATA_DIR / "test_sync.db"
        constants.MEMORIES_DIR = self.tmp_path / "memories"
        constants.BACKUP_DIR = self.tmp_path / "backups"

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

    def test_get_memory_file_status_nonexistent(self):
        result = get_memory_file_status("nonexistent_id")
        self.assertEqual(result["status"], "error")


    def test_orphan_detection_and_audit(self):
        # Create an orphan file on disk
        orphan_path = constants.MEMORIES_DIR / "orphan_test.md"
        orphan_path.write_text("---\ntitle: Orphan Test\n---\nOrphan content", encoding="utf-8")

        orphans = find_orphan_files()
        self.assertGreaterEqual(len(orphans), 1)

        report = audit_storage_integrity(auto_fix=False)
        self.assertIn("summary", report)
        self.assertGreaterEqual(report["summary"]["orphan_files_count"], 1)

    def test_recover_orphaned_documents(self):
        orphan_path = constants.MEMORIES_DIR / "recover_test.md"
        orphan_path.write_text("Unindexed memory content to recover", encoding="utf-8")

        rec_res = recover_orphaned_documents()
        self.assertEqual(rec_res["status"], "success")
        self.assertGreaterEqual(rec_res["recovered_count"], 1)


if __name__ == "__main__":
    unittest.main()


