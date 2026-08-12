from graph.state import GraphRAGState
from retrieval.hybrid_search import HybridSearchCoordinator
from core.metrics import metrics_collector
from core.logger import logger


def retriever_node(state: GraphRAGState) -> GraphRAGState:
    """
    Executes Hybrid Ensemble Search (BM25 + Vector RRF) to fetch top memories matching the query.
    """
    with metrics_collector.time_node("retriever"):
        query = state.get("query", "")
        category = state.get("category")

        if not query:
            state["documents"] = []
            return state

        coordinator = HybridSearchCoordinator(category_filter=category)
        docs = coordinator.search(query=query, top_k=5)

        logger.info(f"Retriever node fetched {len(docs)} memories for query '{query}'")
        state["documents"] = docs
        return state
