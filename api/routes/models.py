from fastapi import APIRouter, HTTPException

from api.schemas import AutoOrganizeRequest, AutoSuggestRequest, ModelSelectRequest, PromptUpdateRequest
from config.prompts import load_prompts, reset_prompts_to_defaults, save_prompts
from core.memory_service import auto_organize_note, generate_auto_suggestions
from utils.llm_client import get_active_model, set_active_model
from utils.model_fetcher import fetch_and_bifurcate_models

router = APIRouter(tags=["Models & Generation"])


@router.get("/api/models")
def get_available_models_endpoint():
    """Fetches available LLM models bifurcated into embedding and generative models."""
    try:
        data = fetch_and_bifurcate_models()
        return {
            "status": "success",
            "active_model": get_active_model(),
            "data": data,
        }
    except Exception as e:
        return {
            "status": "warning",
            "active_model": get_active_model(),
            "message": str(e),
            "data": {
                "generative_models": [{"id": get_active_model(), "status": "active"}],
                "embedding_models": [],
            },
        }


@router.get("/api/models/active")
def get_active_model_endpoint():
    """Returns currently active LLM model."""
    return {
        "status": "success",
        "active_model": get_active_model(),
    }


@router.post("/api/models/active")
def set_active_model_endpoint(req: ModelSelectRequest):
    """Sets the active LLM model."""
    new_model = set_active_model(req.model)
    return {
        "status": "success",
        "active_model": new_model,
        "message": f"Active model updated to '{new_model}'.",
    }


@router.post("/api/auto-organize")
def auto_organize_note_endpoint(req: AutoOrganizeRequest):
    """
    Analyzes raw note content and uses active LLM to generate title, category,
    tags, summary, and clean markdown content.
    """
    res = auto_organize_note(
        content=req.content,
        title=req.title,
        model=req.model,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Auto-organize failed."))
    return res


@router.post("/api/suggest")
def auto_suggest_endpoint(req: AutoSuggestRequest):
    """
    Generates AI writing continuation & key point suggestions using the active LLM model.
    """
    res = generate_auto_suggestions(
        content=req.content,
        title=req.title or "",
        model=req.model,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Auto-suggest failed."))
    return res


@router.get("/api/prompts")
def get_prompts_endpoint():
    """Returns current system prompt templates."""
    return {
        "status": "success",
        "prompts": load_prompts(),
    }


@router.post("/api/prompts")
def update_prompts_endpoint(req: PromptUpdateRequest):
    """Updates custom system prompt templates."""
    updates = {k: v for k, v in req.dict().items() if v is not None}
    updated = save_prompts(updates)
    return {
        "status": "success",
        "message": "Prompt configurations successfully updated.",
        "prompts": updated,
    }


@router.post("/api/prompts/reset")
def reset_prompts_endpoint():
    """Resets system prompt templates to factory defaults."""
    res = reset_prompts_to_defaults()
    return {
        "status": "success",
        "message": "Prompt configurations reset to factory defaults.",
        "prompts": res,
    }
