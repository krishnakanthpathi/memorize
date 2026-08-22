from pathlib import Path
import shutil
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.schemas import TestLLMRequest
import config.constants as constants
from config.prompts import list_prompts
from config.settings import (
    get_all_settings,
    get_memories_dir,
    get_setting,
    get_storage_layout,
    reset_settings,
    set_setting,
    validate_storage_path,
)
from storage.db_manager import get_all_memories, list_all_media_records
from storage.organization_manager import reorganize_memories
from utils.llm_client import test_llm_connection

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdatePayload(BaseModel):
    settings: Dict[str, Any] = {}

    class Config:
        extra = "allow"


class StoragePathsUpdatePayload(BaseModel):
    memories_dir: Optional[str] = None
    storage_layout: Optional[str] = None
    migrate_existing: bool = True


@router.get("")
def get_settings_endpoint():
    """Retrieve all current system configuration settings."""
    return {
        "status": "success",
        "settings": get_all_settings(),
    }


@router.get("/prompts")
def get_prompts_endpoint():
    """Retrieve all registered AI system prompt templates and metadata."""
    return {
        "status": "success",
        "prompts": list_prompts(),
    }


@router.get("/storage-paths")
def get_storage_paths_endpoint():
    """Retrieve storage directory paths, storage layout, disk usage, and health stats."""
    current_mem_dir = get_memories_dir()
    validation = validate_storage_path(str(current_mem_dir))
    all_memories = get_all_memories()
    all_media = list_all_media_records()

    return {
        "status": "success",
        "memories_dir": str(current_mem_dir),
        "storage_layout": get_storage_layout(),
        "default_memories_dir": str(constants.DATA_DIR / "memories"),
        "media_dir": str(constants.MEDIA_DIR),
        "db_path": str(constants.DB_PATH),
        "validation": validation,
        "total_memories": len(all_memories),
        "total_media": len(all_media),
    }


@router.post("/storage-paths")
def update_storage_paths_endpoint(payload: StoragePathsUpdatePayload):
    """
    Update storage directory or storage layout.
    Optionally moves all existing memories and assets to the new target directory.
    """
    current_mem_dir = get_memories_dir()
    migration_summary = None

    if payload.memories_dir:
        val_res = validate_storage_path(payload.memories_dir)
        if not val_res.get("valid"):
            raise HTTPException(status_code=400, detail=f"Invalid storage path: {val_res.get('error')}")

        target_dir = Path(val_res["resolved_path"])
        if target_dir.resolve() != current_mem_dir.resolve() and payload.migrate_existing:
            # Move all existing contents from current to new directory
            try:
                if current_mem_dir.exists():
                    for item in current_mem_dir.iterdir():
                        dest_item = target_dir / item.name
                        if not dest_item.exists():
                            shutil.move(str(item), str(dest_item))
                # Update setting
                set_setting("memories_dir", str(target_dir))
                # Reorganize and update DB paths
                migration_summary = reorganize_memories(auto_fix=True, convert_to_bundle=(payload.storage_layout == "bundle" or get_storage_layout() == "bundle"))
            except Exception as err:
                raise HTTPException(status_code=500, detail=f"Failed to migrate files to new directory: {err}")
        else:
            set_setting("memories_dir", str(target_dir))

    if payload.storage_layout in ("bundle", "flat"):
        set_setting("storage_layout", payload.storage_layout)

    return {
        "status": "success",
        "memories_dir": str(get_memories_dir()),
        "storage_layout": get_storage_layout(),
        "migration_summary": migration_summary,
        "settings": get_all_settings(),
    }


@router.post("/migrate-storage")
def migrate_storage_layout_endpoint(payload: Dict[str, Any] = {}):
    """
    Reorganizes all memories on disk into the requested layout (default: 'bundle').
    Extracts media and thumbnails into dedicated subfolders per memory.
    """
    requested_layout = payload.get("storage_layout", get_storage_layout())
    convert_bundle = (requested_layout == "bundle")
    reclassify = bool(payload.get("reclassify", False))

    set_setting("storage_layout", requested_layout)
    result = reorganize_memories(
        auto_fix=True,
        reclassify=reclassify,
        convert_to_bundle=convert_bundle,
    )

    return {
        "status": "success",
        "storage_layout": requested_layout,
        "migration_result": result,
    }


@router.post("")
def update_settings_endpoint(payload: Dict[str, Any]):
    """
    Update configuration settings and persist them to data/settings.json.
    Supports toggling use_llm, changing embedding_model, classification_model, memories_dir, etc.
    """
    settings_dict = payload.get("settings", payload)
    updated = {}
    for key, value in settings_dict.items():
        if key != "settings":
            success = set_setting(key, value)
            if success:
                updated[key] = value

    return {
        "status": "success",
        "updated": updated,
        "settings": get_all_settings(),
    }


@router.post("/test-llm")
def test_llm_endpoint(payload: TestLLMRequest):
    """Test connectivity to configured LLM endpoint without chatbot."""
    res = test_llm_connection(
        model=payload.model,
        provider=payload.provider,
        base_url=payload.base_url,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=502, detail=res.get("error", "LLM connection test failed."))
    return res


@router.post("/reset")
def reset_settings_endpoint():
    """Reset configuration settings back to defaults."""
    success = reset_settings()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset settings.")
    return {
        "status": "success",
        "settings": get_all_settings(),
    }

