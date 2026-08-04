from pathlib import Path
import shutil
import tempfile
import unittest

from storage.markdown_handler import (
    create_markdown_file,
    delete_markdown_file,
    read_markdown_file,
    title_to_filename,
)


class TestMarkdownHandler(unittest.TestCase):

    def test_title_to_filename(self):
        """Test converting titles to clean filenames."""
        self.assertEqual(title_to_filename("Family Birthdays 2026!"), "family_birthdays_2026.md")
        self.assertEqual(title_to_filename("  My Job & Notes  "), "my_job_notes.md")
        self.assertEqual(title_to_filename("!!!"), "untitled_memory.md")

    def test_create_read_delete_markdown_file(self):
        """Test creating, reading, and deleting markdown memory files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_personal_dir = Path(tmp_dir) / "personal"
            test_personal_dir.mkdir(parents=True, exist_ok=True)

            memory_id = "mem_test123456"
            title = "Test Family Memory"
            category = "personal"
            tags = ["family", "birthday"]
            content = "Remember to buy birthday cake for Sarah."
            content_hash = "abc123hash"
            created_at = "2026-08-02T10:00:00Z"
            updated_at = "2026-08-02T10:00:00Z"

            # 1. Test creation
            file_path = create_markdown_file(
                memory_id=memory_id,
                title=title,
                category=category,
                tags=tags,
                content=content,
                content_hash=content_hash,
                created_at=created_at,
                updated_at=updated_at,
            )

            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.name, "test_family_memory.md")

            # 2. Test reading back
            frontmatter, read_content = read_markdown_file(file_path)

            self.assertEqual(frontmatter["id"], memory_id)
            self.assertEqual(frontmatter["title"], title)
            self.assertEqual(frontmatter["tags"], tags)
            self.assertEqual(read_content, content)

            # 3. Test deletion
            deleted = delete_markdown_file(file_path)
            self.assertTrue(deleted)
            self.assertFalse(file_path.exists())



if __name__ == "__main__":
    unittest.main()
