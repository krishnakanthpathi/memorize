from fastapi import APIRouter

from storage.backup_manager import (
    backup_all_memories,
    get_backup_readme,
)
from storage.db_manager import get_categories_stats
from storage.sync_manager import clear_all_memories

router = APIRouter(tags=["system"])


@router.get("/api/categories")
def get_categories():
    return {"categories": get_categories_stats()}


@router.get("/api/backup")
def get_backup_status_endpoint():
    readme_text = get_backup_readme()
    return {
        "status": "success",
        "readme_text": readme_text,
    }


@router.post("/api/backup")
def trigger_backup_endpoint():
    return backup_all_memories()


@router.delete("/api/purge")
def purge_all_memories_endpoint():
    return clear_all_memories(clear_backups=True)
