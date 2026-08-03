from pathlib import Path
import tempfile
import unittest

from vector.vector_db import (
    add_chunks_to_vector_db,
    delete_chunks_by_memory_id,
    query_vector_db,
)


class TestVectorDB(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_chroma_dir = Path(self.tmp_dir.name) / "chroma_db"

        import vector.vector_db
        vector.vector_db.CHROMA_DIR = self.test_chroma_dir
        vector.vector_db.CHROMA_CLIENT = None

    def tearDown(self):
        import vector.vector_db
        vector.vector_db.CHROMA_CLIENT = None
        self.tmp_dir.cleanup()

    def test_add_query_and_delete_chunks(self):
        """Test full vector DB lifecycle: adding chunks, querying similarity, filtering, and deleting."""
        chunks = [
            {
                "chunk_id": "mem_101_chunk_0",
                "memory_id": "mem_101",
                "chunk_index": 0,
                "text": "Naruto Uzumaki is a ninja from Konoha village.",
                "category": "personal",
                "tags": ["naruto", "ninja"],
            },
            {
                "chunk_id": "mem_102_chunk_0",
                "memory_id": "mem_102",
                "chunk_index": 0,
                "text": "Python 3.12 RAG architecture project setup.",
                "category": "study",
                "tags": ["python", "rag"],
            },
        ]

        emb1 = [0.1] * 384
        emb2 = [-0.1] * 384
        embeddings = [emb1, emb2]

        # 1. Add chunks
        add_result = add_chunks_to_vector_db(chunks, embeddings)
        self.assertEqual(add_result["status"], "success")
        self.assertEqual(add_result["added_count"], 2)

        # 2. Query vector DB
        query_emb = [0.09] * 384
        results = query_vector_db(query_emb, n_results=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["chunk_id"], "mem_101_chunk_0")
        self.assertGreater(results[0]["similarity_score"], 0.5)

        # 3. Category filter query
        study_results = query_vector_db(query_emb, n_results=2, category_filter="study")
        self.assertEqual(len(study_results), 1)
        self.assertEqual(study_results[0]["chunk_id"], "mem_102_chunk_0")

        # 4. Delete chunks by memory_id
        del_result = delete_chunks_by_memory_id("mem_101")
        self.assertEqual(del_result["status"], "success")

        # Verify deletion
        post_del_results = query_vector_db(query_emb, n_results=2)
        self.assertEqual(len(post_del_results), 1)
        self.assertEqual(post_del_results[0]["chunk_id"], "mem_102_chunk_0")


if __name__ == "__main__":
    unittest.main()
