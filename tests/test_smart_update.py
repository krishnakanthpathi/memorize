import unittest
from unittest.mock import patch

from core.smart_updater import smart_merge_memory_content


class TestSmartUpdate(unittest.TestCase):
    def test_smart_merge_fallback_on_empty(self):
        res = smart_merge_memory_content("", "New Info")
        self.assertEqual(res, "New Info")

        res2 = smart_merge_memory_content("Existing Info", "")
        self.assertEqual(res2, "Existing Info")

    @patch("core.smart_updater.generate_llm_response")
    def test_smart_merge_with_mocked_llm(self, mock_llm):
        mock_llm.return_value = "```markdown\n# User Profile\n\n- Name: Krishnakanth\n- Preferences: Dark Mode (Night), Light Mode (Day)\n```"

        merged = smart_merge_memory_content(
            existing_content="Name: Krishnakanth\nPreferences: Dark Mode",
            new_input="Update preferences: Light Mode during day, Dark Mode at night",
            title="User Profile",
        )

        self.assertNotIn("```markdown", merged)
        self.assertIn("Light Mode (Day)", merged)
        mock_llm.assert_called_once()


if __name__ == "__main__":
    unittest.main()
