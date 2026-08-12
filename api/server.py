from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ChatRequest, MemoryCreateRequest, RevertRequest, SearchRequest
from core.memory_service import execute_revert_memory, execute_upsert_memory, handle_delete_memory
from core.metrics import metrics_collector
from graph.workflow import MemorizeGraphRAGAgent
from retrieval.hybrid_search import HybridSearchCoordinator
from storage.backup_manager import (
    backup_all_memories,
    get_backup_readme,
)
from storage.db_manager import (
    get_all_memories,
    get_categories_stats,
    get_memory_by_id,
)
from storage.sync_manager import clear_all_memories, get_memory_file_status
from storage.version_manager import get_version_history


app = FastAPI(
    title="Memorize API Service",
    description="REST API Service powered by LangChain & LangGraph GraphRAG Engine",
    version="2.0.0",
)

# Enable CORS for local web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate global GraphRAG agent
graph_agent = MemorizeGraphRAGAgent()


@app.get("/")
def read_root():
    return {
        "service": "Memorize LangGraph REST API Service",
        "status": "online",
        "version": "2.0.0",
    }


@app.get("/api/metrics")
def get_metrics_endpoint():
    """Returns observability latency, token, and node timing statistics."""
    return {
        "status": "success",
        "metrics": metrics_collector.get_summary(),
    }


@app.get("/api/categories")
def get_categories():
    return {"categories": get_categories_stats()}


@app.get("/api/memories")
def list_memories_endpoint(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    memories = get_all_memories(category_filter=category, tag_filter=tag)
    return {
        "status": "success",
        "count": len(memories),
        "memories": memories,
    }


@app.post("/api/memories")
def create_or_update_memory_endpoint(req: MemoryCreateRequest):
    res = execute_upsert_memory(
        title=req.title,
        content=req.content,
        action=req.action,
        category=req.category,
        tags=req.tags,
        memory_id=req.memory_id,
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Error storing memory."))
    return res


@app.get("/api/memories/{memory_id}")
def get_memory_detail_endpoint(memory_id: str):
    res = get_memory_file_status(memory_id)
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return res


@app.delete("/api/memories/{memory_id}")
def delete_memory_endpoint(memory_id: str):
    res = handle_delete_memory(norm_title="", category="", memory_id=memory_id)
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message", "Memory not found."))
    return res


@app.get("/api/memories/{memory_id}/versions")
def get_memory_versions_endpoint(memory_id: str):
    target = get_memory_by_id(memory_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    history = get_version_history(memory_id)
    return {
        "status": "success",
        "memory_id": memory_id,
        "title": target.get("title"),
        "total_versions": len(history),
        "versions": history,
    }


@app.post("/api/memories/{memory_id}/revert")
def revert_memory_endpoint(memory_id: str, req: Optional[RevertRequest] = None):
    ver_num = req.version_number if req else None
    res = execute_revert_memory(memory_id=memory_id, version_number=ver_num)
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Error reverting memory."))
    return res


@app.post("/api/search")
def search_memories_endpoint(req: SearchRequest):
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


@app.get("/api/backup")
def get_backup_status_endpoint():
    readme_text = get_backup_readme()
    return {
        "status": "success",
        "readme_text": readme_text,
    }


@app.post("/api/backup")
def trigger_backup_endpoint():
    res = backup_all_memories()
    return res


@app.delete("/api/purge")
def purge_all_memories_endpoint():
    res = clear_all_memories(clear_backups=True)
    return res


@app.post("/api/chat")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=6999, reload=True)
