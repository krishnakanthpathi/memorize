from pathlib import Path
import tempfile
import unittest

from core.hashing import compute_file_hash, compute_string_hash


class TestHashing(unittest.TestCase):

    def test_compute_string_hash(self):
        """Test string hashing produces deterministic SHA-256 hex strings."""
        content = "hello world"
        expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

        hash_val = compute_string_hash(content)
        self.assertEqual(hash_val, expected_hash)
        self.assertEqual(len(hash_val), 64)  # SHA-256 hex length

    def test_compute_file_hash(self):
        """Test file hashing on a temporary test file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "sample.txt"
            test_file.write_text("hello world", encoding="utf-8")

            file_hash = compute_file_hash(test_file)
            string_hash = compute_string_hash("hello world")

            self.assertEqual(file_hash, string_hash)


if __name__ == "__main__":
    unittest.main()
