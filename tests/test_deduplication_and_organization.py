import unittest
from unittest.mock import patch

from core.deduplication_service import detect_duplicate_clusters
from storage.organization_manager import reorganize_memories
from utils import slugify_title


class TestDeduplicationAndOrganization(unittest.TestCase):

    def test_slugify_title(self):
        title = "Krishna Kanth's Contact & Identification Details!"
        slug = slugify_title(title)
        self.assertEqual(slug, "krishna_kanth_s_contact_identification_details")

    def test_detect_duplicate_clusters_empty(self):
        result = detect_duplicate_clusters(category_filter="non_existent_category")
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("clusters_found"), 0)

    def test_reorganize_memories_structure(self):
        result = reorganize_memories(auto_fix=False, reclassify=False)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("files_checked", result)


if __name__ == "__main__":
    unittest.main()
