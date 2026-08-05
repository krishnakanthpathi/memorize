from pathlib import Path
import tempfile
import unittest

from search.relevance_scorer import (
    search_hybrid_relevance,
    search_vector_similarity,
)
from storage.db_manager import clear_all_index_memories, init_db, upsert_memory_index
from vector.vector_db import add_chunks_to_vector_db


class TestSearchEngine(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_chroma_dir = Path(self.tmp_dir.name) / "chroma_db"

        import vector.vector_db
        vector.vector_db.CHROMA_DIR = self.test_chroma_dir
        vector.vector_db.CHROMA_CLIENT = None

        init_db()
        clear_all_index_memories()

        # Seed sample memories into SQLite & Vector DB
        mem1 = {
            "id": "mem_search_1",
            "title": "Machine Learning Notes",
            "category": "study",
            "tags": ["ai", "ml", "python"],
            "file_path": "/tmp/ml.md",
            "content": "Deep learning and neural networks fundamentals in Python.",
            "snippet": "Deep learning and neural networks fundamentals in Python.",
        }
        mem2 = {
            "id": "mem_search_2",
            "title": "Grocery Shopping List",
            "category": "routine",
            "tags": ["shopping", "food"],
            "file_path": "/tmp/grocery.md",
            "content": "Buy apples, milk, bread, and coffee beans.",
            "snippet": "Buy apples, milk, bread, and coffee beans.",
        }
        upsert_memory_index(mem1)
        upsert_memory_index(mem2)

        # Mock vector chunks
        chunks = [
            {
                "chunk_id": "mem_search_1_c0",
                "memory_id": "mem_search_1",
                "chunk_index": 0,
                "text": "Deep learning and neural networks fundamentals in Python.",
                "category": "study",
                "tags": ["ai", "ml", "python"],
            },
            {
                "chunk_id": "mem_search_2_c0",
                "memory_id": "mem_search_2",
                "chunk_index": 0,
                "text": "Buy apples, milk, bread, and coffee beans.",
                "category": "routine",
                "tags": ["shopping", "food"],
            },
        ]
        emb1 = [0.2] * 384
        emb2 = [-0.2] * 384
        add_chunks_to_vector_db(chunks, [emb1, emb2])

    def tearDown(self):
        import vector.vector_db
        vector.vector_db.CHROMA_CLIENT = None
        clear_all_index_memories()
        self.tmp_dir.cleanup()

    def test_search_vector_similarity(self):
        """Test pure vector similarity search returning ranked results."""
        results = search_vector_similarity("neural networks python", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["memory_id"], "mem_search_1")
        self.assertIn("similarity_score", results[0])

    def test_search_vector_similarity_category_filter(self):
        """Test vector similarity search with category filter."""
        results = search_vector_similarity("milk bread", category_filter="routine", top_k=2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["memory_id"], "mem_search_2")


if __name__ == "__main__":
    unittest.main()
