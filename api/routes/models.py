from typing import Optional
from fastapi import APIRouter, Query

from utils.model_fetcher import fetch_and_bifurcate_models

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_available_models_endpoint(
    base_url: Optional[str] = Query(None),
    api_key: Optional[str] = Query(None),
):
    return fetch_and_bifurcate_models(base_url=base_url, api_key=api_key)
