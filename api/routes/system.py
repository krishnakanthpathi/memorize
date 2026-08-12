from fastapi import APIRouter, Query

from core.metrics import metrics_collector
from storage.backup_manager import (
    backup_all_memories,
    get_backup_readme,
)
from storage.db_manager import get_categories_stats
from storage.sync_manager import audit_storage_integrity, clear_all_memories

router = APIRouter(prefix="/api", tags=["System & Audit"])


@router.get("/metrics")
def get_metrics_endpoint():
    """Returns observability latency, token, and node timing statistics."""
    return {
        "status": "success",
        "metrics": metrics_collector.get_summary(),
    }


@router.get("/categories")
def get_categories_endpoint():
    """Returns category breakdown and item counts."""
    return {"categories": get_categories_stats()}


@router.get("/audit")
def audit_integrity_endpoint(
    auto_fix: bool = Query(False),
    recover: bool = Query(False),
):
    """Three-way integrity audit across Markdown files, SQLite, and ChromaDB."""
    return audit_storage_integrity(auto_fix=auto_fix, recover=recover)


@router.get("/backup")
def get_backup_status_endpoint():
    """Get backup documentation and status."""
    readme_text = get_backup_readme()
    return {
        "status": "success",
        "readme_text": readme_text,
    }


@router.post("/backup")
def trigger_backup_endpoint():
    """Trigger system snapshot backup."""
    res = backup_all_memories()
    return res


@router.delete("/purge")
def purge_all_memories_endpoint():
    """Purge all memories across disk, SQLite, and ChromaDB."""
    res = clear_all_memories(clear_backups=True)
    return res
