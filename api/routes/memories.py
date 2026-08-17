from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    MemoryCreateRequest,
    MemoryMergeRequest,
    MemoryOrganizeRequest,
    RevertRequest,
)
from core.memory_merger import (
    find_correlated_memories,
    merge_memories_service,
    organize_single_memory_service,
)
from core.memory_service import (
    execute_revert_memory,
    execute_upsert_memory,
    handle_delete_memory,
)
from storage.db_manager import get_all_memories, get_memory_by_id
from storage.sync_manager import get_memory_file_status
from storage.version_manager import get_version_history

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("")
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


@router.post("")
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


@router.get("/{memory_id}")
def get_memory_detail_endpoint(memory_id: str):
    res = get_memory_file_status(memory_id)
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return res


@router.delete("/{memory_id}")
def delete_memory_endpoint(memory_id: str):
    res = handle_delete_memory(norm_title="", category="", memory_id=memory_id)
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message", "Memory not found."))
    return res


@router.get("/{memory_id}/versions")
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


@router.post("/merge")
def merge_memories_endpoint(req: MemoryMergeRequest):
    res = merge_memories_service(
        memory_ids=req.memory_ids,
        target_title=req.target_title,
        target_category=req.target_category,
        target_tags=req.target_tags,
        delete_sources=req.delete_sources,
        instruction=req.instruction,
        use_ai=req.use_ai,
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Error merging memories."))
    return res


@router.post("/{memory_id}/organize")
def organize_memory_endpoint(memory_id: str, req: Optional[MemoryOrganizeRequest] = None):
    instruction = req.instruction if req else None
    use_ai = req.use_ai if req is not None else True
    res = organize_single_memory_service(
        memory_id=memory_id,
        instruction=instruction,
        use_ai=use_ai,
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Error organizing memory."))
    return res


@router.get("/{memory_id}/correlations")
def get_memory_correlations_endpoint(
    memory_id: str,
    top_k: int = Query(5, ge=1, le=20),
):
    target = get_memory_by_id(memory_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    correlations = find_correlated_memories(memory_id=memory_id, top_k=top_k)
    return {
        "status": "success",
        "memory_id": memory_id,
        "total_correlated": len(correlations),
        "correlations": correlations,
    }


@router.post("/{memory_id}/revert")
def revert_memory_endpoint(memory_id: str, req: Optional[RevertRequest] = None):
    ver_num = req.version_number if req else None
    res = execute_revert_memory(memory_id=memory_id, version_number=ver_num)
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Error reverting memory."))
    return res
