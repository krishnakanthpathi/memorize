from fastapi import APIRouter

from api.schemas import SearchRequest
from retrieval.hybrid_search import HybridSearchCoordinator

router = APIRouter(prefix="/api/search", tags=["Hybrid Search"])


@router.post("")
def search_memories_endpoint(req: SearchRequest):
    """Executes hybrid keyword + semantic search across memories."""
    coordinator = HybridSearchCoordinator(category_filter=req.category_filter)
    results = coordinator.search(
        query=req.query,
        category_filter=req.category_filter,
        top_k=req.top_k,
    )
    return {
        "status": "success",
        "query": req.query,
        "results_count": len(results),
        "results": results,
    }
