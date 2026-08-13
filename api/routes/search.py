from fastapi import APIRouter

from api.schemas import SearchRequest
from search.relevance_scorer import search_hybrid_relevance as hybrid_search_memories

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("")
def search_memories_endpoint(req: SearchRequest):
    results = hybrid_search_memories(
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
