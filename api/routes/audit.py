from typing import Optional
from fastapi import APIRouter

from api.schemas import AuditActionRequest
from storage.sync_manager import (
    audit_storage_integrity,
    delete_orphan_chunks,
    delete_orphan_files,
    delete_orphan_indexes,
    find_orphan_chunks,
    find_orphan_files,
    find_orphan_indexes,
    recover_orphaned_documents,
)

router = APIRouter(prefix="/api/audit", tags=["storage_audit"])


@router.get("/summary")
def get_audit_summary_endpoint():
    return audit_storage_integrity(auto_fix=False)


@router.post("/summary")
def trigger_audit_action_endpoint(req: AuditActionRequest):
    return audit_storage_integrity(auto_fix=req.auto_fix)


@router.get("/orphan-files")
def get_orphan_files_endpoint():
    files = find_orphan_files()
    return {
        "status": "success",
        "orphan_files_count": len(files),
        "orphan_files": files,
    }


@router.get("/orphan-indexes")
def get_orphan_indexes_endpoint():
    indexes = find_orphan_indexes()
    return {
        "status": "success",
        "orphan_indexes_count": len(indexes),
        "orphan_indexes": indexes,
    }


@router.get("/orphan-chunks")
def get_orphan_chunks_endpoint():
    chunks = find_orphan_chunks()
    return {
        "status": "success",
        "orphan_chunks_count": len(chunks),
        "orphan_chunks": chunks,
    }


@router.delete("/orphan-files")
def delete_orphan_files_endpoint():
    return delete_orphan_files()


@router.delete("/orphan-indexes")
def delete_orphan_indexes_endpoint():
    return delete_orphan_indexes()


@router.delete("/orphan-chunks")
def delete_orphan_chunks_endpoint():
    return delete_orphan_chunks()


@router.post("/recover")
def recover_orphans_endpoint():
    return recover_orphaned_documents()
