from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import get_all_settings, reset_settings, set_setting

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdatePayload(BaseModel):
    settings: Dict[str, Any] = {}

    class Config:
        extra = "allow"


@router.get("")
def get_settings_endpoint():
    """Retrieve all current system configuration settings."""
    return {
        "status": "success",
        "settings": get_all_settings(),
    }


@router.post("")
def update_settings_endpoint(payload: Dict[str, Any]):
    """
    Update configuration settings and persist them to data/settings.json.
    Supports toggling use_llm, changing embedding_model, classification_model, etc.
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
