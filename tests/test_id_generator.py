import unittest
from core.id_generator import generate_memory_id, generate_chunk_id


class TestIDGenerator(unittest.TestCase):

    def test_generate_memory_id(self):
        """Test that generated memory IDs start with 'mem_' and have valid length."""
        mem_id_1 = generate_memory_id()
        mem_id_2 = generate_memory_id()

        self.assertTrue(mem_id_1.startswith("mem_"))
        self.assertEqual(len(mem_id_1), 16)  # 'mem_' (4 chars) + 12 hex chars
        self.assertNotEqual(mem_id_1, mem_id_2)  # Must generate unique IDs

    def test_generate_chunk_id(self):
        """Test that chunk IDs format correctly with memory ID and chunk index."""
        mem_id = "mem_a3f89b12c4d5"
        chunk_id = generate_chunk_id(mem_id, 0)

        self.assertEqual(chunk_id, "mem_a3f89b12c4d5_chunk_0")
        self.assertEqual(generate_chunk_id(mem_id, 5), "mem_a3f89b12c4d5_chunk_5")


if __name__ == "__main__":
    unittest.main()
