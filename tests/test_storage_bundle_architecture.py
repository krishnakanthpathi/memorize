import shutil
import tempfile
import unittest
from pathlib import Path

import config.constants as constants
from config.settings import (
    get_memories_dir,
    get_storage_layout,
    set_setting,
    validate_storage_path,
)
from storage.db_manager import (
    get_memory_by_id,
    init_db,
    list_all_media_records,
)
from storage.markdown_handler import (
    create_markdown_file,
    delete_markdown_file,
    read_markdown_file,
)
from storage.media_store_manager import (
    get_media_file_path,
    save_raw_image,
)
from storage.organization_manager import reorganize_memories
from utils.category_utils import get_memory_bundle_dir


class TestStorageBundleArchitecture(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="memorize_bundle_test_"))
        self.patch_memories = self.test_dir / "memories"
        self.patch_memories.mkdir(parents=True, exist_ok=True)
        self.patch_media = self.test_dir / "media"
        self.patch_media.mkdir(parents=True, exist_ok=True)
        self.patch_db = self.test_dir / "memorize_test.db"

        self.orig_memories_dir = constants.MEMORIES_DIR
        self.orig_media_dir = constants.MEDIA_DIR
        self.orig_db_path = constants.DB_PATH

        self.patch_settings_file = self.test_dir / "settings.json"
        import config.settings as settings_mod
        self.orig_settings_file = settings_mod.SETTINGS_FILE
        settings_mod.SETTINGS_FILE = self.patch_settings_file

        constants.MEMORIES_DIR = self.patch_memories
        constants.MEDIA_DIR = self.patch_media
        constants.DB_PATH = self.patch_db
        init_db()

        set_setting("memories_dir", str(self.patch_memories), filepath=self.patch_settings_file)
        set_setting("storage_layout", "bundle", filepath=self.patch_settings_file)

    def tearDown(self):
        import config.settings as settings_mod
        settings_mod.SETTINGS_FILE = self.orig_settings_file
        settings_mod.load_settings(self.orig_settings_file)
        constants.MEMORIES_DIR = self.orig_memories_dir
        constants.MEDIA_DIR = self.orig_media_dir
        constants.DB_PATH = self.orig_db_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_bundle_creation_and_structure(self):
        """Verify create_markdown_file creates dedicated folder with media/ and thumbnails/ subdirs."""
        created_path = create_markdown_file(
            memory_id="mem_bundle_001",
            title="Stanford University Transcript",
            category="education",
            tags=["stanford", "grades"],
            content="Transcripts for B.S. degree.",
        )

        self.assertTrue(created_path.exists())
        bundle_dir = created_path.parent
        self.assertEqual(bundle_dir.name, "stanford_university_transcript")
        self.assertEqual(created_path.name, "stanford_university_transcript.md")
        self.assertTrue((bundle_dir / "media").is_dir())
        self.assertTrue((bundle_dir / "thumbnails").is_dir())

        fm, body = read_markdown_file(created_path)
        self.assertEqual(fm["id"], "mem_bundle_001")
        self.assertEqual(fm["category"], "education")
        self.assertIn("Transcripts for B.S. degree.", body)

    def test_media_and_thumbnails_routing(self):
        """Verify raw media and thumbnails route into bundle subdirectories when memory_id is provided."""
        # Create memory first
        created_path = create_markdown_file(
            memory_id="mem_bundle_002",
            title="Passport Document",
            category="personal",
            tags=["passport", "id"],
            content="Passport copy.",
        )
        # Register in DB
        from storage.db_manager import upsert_memory_index
        upsert_memory_index({
            "id": "mem_bundle_002",
            "title": "Passport Document",
            "category": "personal",
            "file_path": str(created_path),
            "tags": ["passport"],
            "created_at": "2026-08-22T00:00:00Z",
            "updated_at": "2026-08-22T00:00:00Z",
        })

        # Save raw attachment (PDF)
        pdf_rec = save_raw_image(
            file_bytes=b"%PDF-1.4 dummy pdf bytes",
            filename="passport.pdf",
            mime_type="application/pdf",
            memory_id="mem_bundle_002",
        )

        # Save thumbnail
        thumb_rec = save_raw_image(
            file_bytes=b"dummy png thumbnail bytes",
            filename="passport_thumb.png",
            mime_type="image/png",
            memory_id="mem_bundle_002",
            is_thumbnail=True,
        )

        bundle_dir = created_path.parent
        pdf_path = Path(pdf_rec["file_path"])
        thumb_path = Path(thumb_rec["file_path"])

        self.assertTrue(pdf_path.exists())
        self.assertEqual(pdf_path.parent, bundle_dir / "media")

        self.assertTrue(thumb_path.exists())
        self.assertEqual(thumb_path.parent, bundle_dir / "thumbnails")

        # Test path resolution
        resolved_pdf = get_media_file_path(pdf_rec["filename"])
        resolved_thumb = get_media_file_path(thumb_rec["filename"])
        self.assertIsNotNone(resolved_pdf)
        self.assertIsNotNone(resolved_thumb)
        self.assertEqual(resolved_pdf.resolve(), pdf_path.resolve())
        self.assertEqual(resolved_thumb.resolve(), thumb_path.resolve())

    def test_bundle_clean_deletion(self):
        """Verify delete_markdown_file purges the entire bundle folder."""
        created_path = create_markdown_file(
            memory_id="mem_bundle_003",
            title="Temporary Note To Delete",
            category="personal",
            tags=[],
            content="This note will be deleted.",
        )
        bundle_dir = created_path.parent
        self.assertTrue(bundle_dir.exists())

        deleted = delete_markdown_file(created_path)
        self.assertTrue(deleted)
        self.assertFalse(bundle_dir.exists())

    def test_migration_from_flat_to_bundle(self):
        """Verify reorganize_memories migrates flat notes and media into bundles."""
        # 1. Create a flat note in category dir
        cat_dir = self.patch_memories / "personal"
        cat_dir.mkdir(parents=True, exist_ok=True)
        flat_note = cat_dir / "bank_statement.md"

        # Create dummy media in global media dir
        dummy_media_file = self.patch_media / "abc1234567_bank_statement.pdf"
        dummy_media_file.write_bytes(b"dummy bank pdf")
        dummy_thumb_file = self.patch_media / "def1234567_bank_statement_thumb.png"
        dummy_thumb_file.write_bytes(b"dummy bank thumb")

        # Write flat note referencing the media
        flat_note.write_text(
            f"---\nid: mem_flat_001\ntitle: Bank Statement\ncategory: personal\n---\n\n"
            f"[Download](/api/media/{dummy_media_file.name}) [![Thumb](/api/media/{dummy_thumb_file.name})](/api/media/{dummy_media_file.name})",
            encoding="utf-8"
        )

        from storage.db_manager import upsert_memory_index, upsert_media_record
        upsert_memory_index({
            "id": "mem_flat_001",
            "title": "Bank Statement",
            "category": "personal",
            "file_path": str(flat_note),
            "created_at": "2026-08-22T00:00:00Z",
            "updated_at": "2026-08-22T00:00:00Z",
        })
        upsert_media_record({
            "id": "med_1",
            "filename": dummy_media_file.name,
            "original_filename": "bank_statement.pdf",
            "file_path": str(dummy_media_file),
            "mime_type": "application/pdf",
            "file_size": 14,
            "content_hash": "abc1234567",
        })
        upsert_media_record({
            "id": "med_2",
            "filename": dummy_thumb_file.name,
            "original_filename": "bank_statement_thumb.png",
            "file_path": str(dummy_thumb_file),
            "mime_type": "image/png",
            "file_size": 16,
            "content_hash": "def1234567",
        })

        # Run migration
        res = reorganize_memories(auto_fix=True, convert_to_bundle=True)
        self.assertEqual(res["status"], "success")

        # Verify bundle was created
        expected_bundle = cat_dir / "bank_statement"
        self.assertTrue(expected_bundle.exists())
        self.assertTrue((expected_bundle / "bank_statement.md").exists())
        self.assertTrue((expected_bundle / "media" / dummy_media_file.name).exists())
        self.assertTrue((expected_bundle / "thumbnails" / dummy_thumb_file.name).exists())
        self.assertFalse(flat_note.exists())

    def test_validate_storage_path(self):
        """Verify storage path validation handles invalid vs valid directory targets."""
        res_valid = validate_storage_path(str(self.patch_memories))
        self.assertTrue(res_valid["valid"])
        self.assertGreater(res_valid["free_gb"], 0)

        res_empty = validate_storage_path("")
        self.assertFalse(res_empty["valid"])


if __name__ == "__main__":
    unittest.main()
