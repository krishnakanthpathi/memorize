import unittest
from vector.embedder import (
    generate_embeddings,
    generate_single_embedding,
    generate_local_embeddings,
)


class TestEmbedder(unittest.TestCase):

    def test_local_sentence_transformer_embedding(self):
        """
        Loads local sentence-transformers (all-MiniLM-L6-v2)
        and verifies embedding output dimension (384 floats).
        """
        text = "Hello world! Testing local sentence-transformers embedding."
        embeddings = generate_local_embeddings([text])

        self.assertEqual(len(embeddings), 1)
        self.assertEqual(len(embeddings[0]), 384)  # all-MiniLM-L6-v2 is 384-dimensional
        self.assertIsInstance(embeddings[0][0], float)

    def test_generate_embeddings_wrapper(self):
        """Test general generate_embeddings fallback wrapper."""
        texts = ["Memory note 1", "Memory note 2"]
        embeddings = generate_embeddings(texts)

        self.assertEqual(len(embeddings), 2)
        self.assertGreater(len(embeddings[0]), 0)

    def test_semantic_similarity(self):
        """
        Tests semantic similarity: 'woke up early' should be closer
        to 'woke up at 6AM' than to 'python code syntax'.
        """
        import numpy as np

        emb1 = np.array(generate_single_embedding("woke up early morning"))
        emb2 = np.array(generate_single_embedding("woke up at 6AM today"))
        emb3 = np.array(generate_single_embedding("python code function definition"))

        def cosine_similarity(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        sim_related = cosine_similarity(emb1, emb2)
        sim_unrelated = cosine_similarity(emb1, emb3)

        self.assertGreater(sim_related, sim_unrelated)


if __name__ == "__main__":
    unittest.main()
