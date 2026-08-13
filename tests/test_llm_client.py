import unittest
from unittest.mock import MagicMock, patch

from utils.llm_client import (
    generate_llm_response,
    generate_ollama_response,
    generate_openai_response,
)


class TestLLMClientFunctions(unittest.TestCase):
    @patch("requests.post")
    def test_generate_ollama_response_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Hello from Ollama!"}
        mock_post.return_value = mock_resp

        res = generate_ollama_response(prompt="Hello")
        self.assertEqual(res, "Hello from Ollama!")

    @patch("openai.OpenAI")
    @patch("utils.llm_client.OPENAI_API_KEY", "test-api-key")
    def test_generate_openai_response_success(self, mock_openai):
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from OpenAI!"
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        res = generate_openai_response(prompt="Hello")
        self.assertEqual(res, "Hello from OpenAI!")

    @patch("utils.llm_client.generate_ollama_response")
    def test_generate_llm_response_routing_ollama(self, mock_ollama):
        mock_ollama.return_value = "Routed response"
        res = generate_llm_response(prompt="Test", provider="ollama")
        self.assertEqual(res, "Routed response")
        mock_ollama.assert_called_once()


if __name__ == "__main__":
    unittest.main()
