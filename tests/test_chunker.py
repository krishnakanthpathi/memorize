import unittest
from vector.chunker import count_tokens, chunk_text, get_chunk_settings


class TestChunker(unittest.TestCase):

    def test_count_tokens(self):
        """Test token counting."""
        text = "Hello world! This is a test for token counting."
        token_cnt = count_tokens(text)
        self.assertGreater(token_cnt, 0)

    def test_chunk_text_small(self):
        """Test small text fits in a single chunk."""
        text = "Small memory text."
        chunks = chunk_text("mem_test1", text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "mem_test1_chunk_0")
        self.assertEqual(chunks[0]["text"], "Small memory text.")

    def test_chunk_text_large_html(self):
        """Test large HTML text (7,000+ tokens) gets split into multiple chunks under 500 tokens."""
        # Create large repetitive HTML text
        large_html = "<div><h1>Naruto Vice City</h1><p>Konoha Village Open World Game</p></div>\n" * 200
        
        chunks = chunk_text("naruto_mem", large_html)
        self.assertGreater(len(chunks), 1)
        
        # Verify NO chunk exceeds 500 tokens
        for chunk in chunks:
            self.assertLessEqual(chunk["token_count"], 500)
            self.assertTrue(chunk["chunk_id"].startswith("naruto_mem_chunk_"))


if __name__ == "__main__":
    unittest.main()
