import unittest

from retrieval.contextual_retriever import ContextualChunker
from retrieval.ensemble_retriever import MemorizeEnsembleRetriever
from retrieval.hybrid_search import HybridSearchCoordinator
from storage.db_manager import init_db


class TestHybridSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_contextual_chunker_bypass(self):
        chunker = ContextualChunker()
        chunks = ["Chunk 1", "Chunk 2"]
        res = chunker.enrich_chunks("Full document text here", chunks)
        self.assertEqual(len(res), 2)

    def test_ensemble_retriever(self):
        retriever = MemorizeEnsembleRetriever()
        docs = retriever.retrieve("python development", top_k=2)
        self.assertIsInstance(docs, list)

    def test_hybrid_search_coordinator(self):
        coordinator = HybridSearchCoordinator()
        results = coordinator.search("test query", top_k=2)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
