from fastapi import APIRouter, HTTPException

from api.schemas import ChatRequest
from graph.workflow import MemorizeGraphRAGAgent

router = APIRouter(prefix="/api/chat", tags=["GraphRAG Companion"])

# Instantiate global GraphRAG agent
graph_agent = MemorizeGraphRAGAgent()


@router.post("")
def chat_companion_endpoint(req: ChatRequest):
    """
    Executes LangGraph GraphRAG Agent pipeline for stateful conversation,
    multi-hop entity linking, memory mutations, and RAG answer synthesis.
    """
    result = graph_agent.run(query=req.message, category=req.category)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Error in GraphRAG agent."))

    return {
        "status": "success",
        "message": req.message,
        "reply": result.get("reply"),
        "intent": result.get("intent"),
        "category": result.get("category"),
        "is_offline_mode": result.get("is_offline_mode", False),
        "documents_count": result.get("documents_count", 0),
        "entities": result.get("entities", []),
        "latency_ms": result.get("latency_ms", 0.0),
    }
