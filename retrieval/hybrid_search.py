from typing import Any, Dict, List, Optional

from retrieval.ensemble_retriever import MemorizeEnsembleRetriever
from search.relevance_scorer import search_hybrid_relevance
from core.metrics import metrics_collector
from core.logger import logger


class HybridSearchCoordinator:
    """
    Primary search coordinator coordinating BM25 + Vector Ensemble search
    with relevance scoring and observability metrics collection.
    """

    def __init__(self, category_filter: Optional[str] = None):
        self.category_filter = category_filter
        self.ensemble = MemorizeEnsembleRetriever(category_filter=category_filter)

    def search(
        self,
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        target_category = category_filter or self.category_filter

        try:
            # 1. Execute Ensemble Search (BM25 + Vector RRF)
            ensemble_docs = self.ensemble.retrieve(query, top_k=top_k)

            # 2. Execute Hybrid Relevance Scorer for fine-grained ranking
            hybrid_results = search_hybrid_relevance(
                query=query,
                category_filter=target_category,
                top_k=top_k,
            )

            # Record metrics
            hit_count = len(hybrid_results) if isinstance(hybrid_results, list) else len(ensemble_docs)
            metrics_collector.record_retrieval_hit(hit_count)

            if isinstance(hybrid_results, list) and hybrid_results:
                return hybrid_results

            # Format ensemble docs if hybrid_results returned empty
            formatted = []
            for doc in ensemble_docs:
                formatted.append({
                    "id": doc.metadata.get("memory_id", ""),
                    "title": doc.metadata.get("title", ""),
                    "category": doc.metadata.get("category", "personal"),
                    "tags": doc.metadata.get("tags", []),
                    "content": doc.page_content,
                    "snippet": doc.page_content[:150],
                    "final_score": 0.85,
                })
            return formatted
        except Exception as e:
            logger.error(f"HybridSearchCoordinator error: {e}")
            return []
