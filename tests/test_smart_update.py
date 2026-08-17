import unittest
from unittest.mock import patch

from core.smart_updater import smart_merge_memory_content


class TestSmartUpdate(unittest.TestCase):
    def test_smart_merge_fallback_on_empty(self):
        res = smart_merge_memory_content("", "New Info")
        self.assertEqual(res, "New Info")

        res2 = smart_merge_memory_content("Existing Info", "")
        self.assertEqual(res2, "Existing Info")

    @patch("core.smart_updater.get_setting")
    @patch("core.smart_updater.llm_smart_update")
    def test_smart_merge_with_mocked_llm(self, mock_llm, mock_setting):
        mock_setting.return_value = True
        mock_llm.return_value = "# User Profile\n\n- Name: Krishnakanth\n- Preferences: Dark Mode (Night), Light Mode (Day)"

        merged = smart_merge_memory_content(
            existing_content="Name: Krishnakanth\nPreferences: Dark Mode",
            new_input="Update preferences: Light Mode during day, Dark Mode at night",
            title="User Profile",
        )

        self.assertNotIn("```markdown", merged)
        self.assertIn("Light Mode (Day)", merged)
        mock_llm.assert_called_once()

    @patch("core.smart_updater.get_setting")
    def test_smart_merge_deterministic_offline_when_llm_disabled(self, mock_setting):
        mock_setting.return_value = False
        merged = smart_merge_memory_content(
            existing_content="Name: Krishnakanth\nPreferences: Dark Mode",
            new_input="Update preferences: Light Mode during day",
            title="User Profile",
        )
        self.assertEqual(
            merged,
            "Name: Krishnakanth\nPreferences: Dark Mode\n\nUpdate preferences: Light Mode during day",
        )


if __name__ == "__main__":
    unittest.main()
