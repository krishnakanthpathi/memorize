import unittest
from unittest.mock import MagicMock, patch

from core.llm_tasks import (
    clean_generated_title,
    llm_classify_text,
    llm_generate_title,
    llm_organize_note,
    llm_smart_update,
    llm_synthesize_memories,
    llm_transform_selection,
    progressive_llm_merge,
)


class TestLLMTasks(unittest.TestCase):
    def test_clean_generated_title(self):
        self.assertEqual(clean_generated_title('"My Awesome Title"'), "My Awesome Title")
        self.assertEqual(clean_generated_title('# Super Note Title'), "Super Note Title")
        self.assertEqual(clean_generated_title('Title: Backend Architecture'), "Backend Architecture")
        self.assertEqual(clean_generated_title('**Note on Kubernetes**'), "Note on Kubernetes")

    @patch("core.llm_tasks.generate_json_response")
    def test_llm_classify_text(self, mock_json):
        mock_json.return_value = {
            "category": "work",
            "tags": ["deployment", "docker"],
        }
        res = llm_classify_text("Deploying container to cluster", ["work", "personal"])
        self.assertEqual(res["category"], "work")
        self.assertIn("deployment", res["tags"])

    @patch("core.llm_tasks.generate_llm_response")
    def test_llm_synthesize_memories(self, mock_llm):
        mock_llm.return_value = "# Synthesized Note\n\nCombined knowledge content."
        res = llm_synthesize_memories(
            memories=[
                {"title": "Note 1", "content": "Note 1 content", "category": "work"},
                {"title": "Note 2", "content": "Note 2 content", "category": "work"},
            ],
            target_title="Synthesized Note",
            custom_instruction="Combine into overview",
        )
        self.assertIn("Synthesized Note", res)

    @patch("core.llm_tasks.generate_llm_response")
    def test_llm_organize_note(self, mock_llm):
        mock_llm.return_value = "# Organized Note\n\nPolished text with clean formatting."
        res = llm_organize_note(
            content="raw draft notes",
            title="Organized Note",
            category="personal",
            tags=["draft"],
            instruction="Polish grammar",
        )
        self.assertIn("Polished text", res)

    @patch("core.llm_tasks.generate_llm_response")
    def test_llm_generate_title(self, mock_llm):
        mock_llm.return_value = '"Calculus and Linear Algebra Notes"'
        res = llm_generate_title("Notes about derivatives and matrix multiplication")
        self.assertEqual(res, "Calculus and Linear Algebra Notes")

    @patch("core.llm_tasks.generate_llm_response")
    def test_llm_transform_selection(self, mock_llm):
        mock_llm.return_value = "- Key Point 1\n- Key Point 2"
        res = llm_transform_selection(
            selected_text="A lot of verbose paragraphs here...",
            mode="summarize",
        )
        self.assertIn("Key Point 1", res)

    @patch("core.llm_tasks.generate_llm_response")
    def test_llm_smart_update(self, mock_llm):
        mock_llm.return_value = "# Note\nUpdated content with appended details."
        res = llm_smart_update(
            existing_content="# Note\nExisting content",
            new_input="New details to append",
            title="Note",
        )
        self.assertIn("Updated content", res)


if __name__ == "__main__":
    unittest.main()
