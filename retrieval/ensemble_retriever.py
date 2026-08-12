from typing import Dict, List, Optional
from langchain_core.documents import Document

from config.settings import settings
from retrieval.bm25_searcher import BM25Searcher
from retrieval.vector_searcher import VectorSearcher
from core.logger import logger


class MemorizeEnsembleRetriever:
    """
    Reciprocal Rank Fusion (RRF) Ensemble Retriever merging BM25 (keyword matching)
    and Chroma Vector Similarity Search with weighted rank aggregation.
    """

    def __init__(
        self,
        category_filter: Optional[str] = None,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        c: int = 60,
    ):
        self.category_filter = category_filter
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.c = c
        self.bm25_searcher = BM25Searcher(category_filter=category_filter)
        self.vector_searcher = VectorSearcher(category_filter=category_filter)

    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        bm25_docs = self.bm25_searcher.search(query, top_k=top_k * 2)
        vector_docs = self.vector_searcher.search(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        # 1. Score BM25 results
        for rank, doc in enumerate(bm25_docs, start=1):
            mem_id = doc.metadata.get("memory_id") or doc.page_content[:50]
            doc_map[mem_id] = doc
            score = self.bm25_weight / (self.c + rank)
            rrf_scores[mem_id] = rrf_scores.get(mem_id, 0.0) + score

        # 2. Score Vector results
        for rank, doc in enumerate(vector_docs, start=1):
            mem_id = doc.metadata.get("memory_id") or doc.page_content[:50]
            doc_map[mem_id] = doc
            score = self.vector_weight / (self.c + rank)
            rrf_scores[mem_id] = rrf_scores.get(mem_id, 0.0) + score

        # 3. Sort by aggregated RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        ranked_docs = []
        for mem_id in sorted_ids[:top_k]:
            doc = doc_map[mem_id]
            doc.metadata["rrf_score"] = round(rrf_scores[mem_id], 4)
            ranked_docs.append(doc)

        return ranked_docs
