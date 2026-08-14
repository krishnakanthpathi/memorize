import argparse
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import requests

from config.constants import OPENAI_BASE_URL, OLLAMA_BASE_URL
from core.logger import logger

# Ensure environment variables from .env are loaded
load_dotenv()

# Keywords used to classify embedding vs generative models
EMBEDDING_KEYWORDS = [
    "embed",
    "embedding",
    "bge",
    "e5",
    "nomic-embed",
    "ada",
    "vector",
    "text-embedding",
    "sentence-transformer",
    "minilm",
]

GENERATIVE_KEYWORDS = [
    "gpt",
    "claude",
    "llama",
    "mistral",
    "gemma",
    "qwen",
    "deepseek",
    "titan-text",
    "instruct",
    "chat",
    "nova",
    "kimi",
    "glm",
    "nemotron",
    "minimax",
    "voxtral",
    "magistral",
    "devstral",
    "coder",
    "vision",
    "palmyra",
    "command",
    "gemini",
    "generate",
    "completion",
]

FAST_KEYWORDS = [
    "mini",
    "small",
    "flash",
    "nano",
    "3b",
    "4b",
    "7b",
    "8b",
    "12b",
    "14b",
    "20b",
    "24b",
    "30b",
    "32b",
    "haiku",
    "turbo",
]

REASONING_KEYWORDS = [
    "thinking",
    "reasoning",
    "deepseek",
    "r1",
    "large",
    "coder",
    "kimi",
    "120b",
    "235b",
    "480b",
    "675b",
    "opus",
    "pro",
]


def classify_model(model_id: str) -> str:
    """
    Classifies a model ID into 'embedding', 'generative', or 'other' based on model name patterns.
    """
    model_id_lower = model_id.lower()

    if any(keyword in model_id_lower for keyword in EMBEDDING_KEYWORDS):
        return "embedding"

    if any(keyword in model_id_lower for keyword in GENERATIVE_KEYWORDS):
        return "generative"

    return "generative"  # Default to generative for general LLM options


def get_available_models(
    base_url: Optional[str] = None, api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches raw model definitions from an OpenAI-compatible /v1/models endpoint.
    """
    url = (base_url or os.getenv("OPENAI_BASE_URL") or OPENAI_BASE_URL).rstrip("/")
    key = api_key or os.getenv("OPENAI_API_KEY") or ""

    if not url.endswith("/models"):
        models_endpoint = f"{url}/models"
    else:
        models_endpoint = url

    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    try:
        response = requests.get(models_endpoint, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "data" in data:
            return data["data"]
        elif isinstance(data, list):
            return data
        else:
            logger.warning(f"Unexpected response structure from {models_endpoint}")
            return []
    except Exception as e:
        logger.warning(f"Failed to fetch remote models from {models_endpoint}: {e}")
        return []


def get_ollama_models(ollama_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches local models from Ollama API (/api/tags).
    """
    base = (ollama_url or os.getenv("OLLAMA_BASE_URL") or OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
    tags_url = f"{base}/api/tags"
    try:
        resp = requests.get(tags_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("models", [])
            res = []
            for m in models:
                res.append({
                    "id": m.get("name") or m.get("model", ""),
                    "object": "model",
                    "owned_by": "ollama",
                    "status": "available",
                    "details": m.get("details", {}),
                })
            return res
    except Exception as e:
        logger.debug(f"Ollama not reachable at {tags_url}: {e}")
    return []


def _bifurcate_model_list(model_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Helper to classify a list of model items into fast, reasoning, generative, and embedding."""
    embedding_models: List[Dict[str, Any]] = []
    generative_models: List[Dict[str, Any]] = []
    fast_models: List[str] = []
    reasoning_models: List[str] = []
    all_models: List[str] = []

    seen = set()
    for item in model_items:
        model_id = item.get("id", "") if isinstance(item, dict) else str(item)
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        all_models.append(model_id)

        category = classify_model(model_id)
        if category == "embedding":
            embedding_models.append(item)
        else:
            generative_models.append(item)
            m_lower = model_id.lower()
            if any(k in m_lower for k in REASONING_KEYWORDS):
                reasoning_models.append(model_id)
            elif any(k in m_lower for k in FAST_KEYWORDS):
                fast_models.append(model_id)
            else:
                fast_models.append(model_id)

    default_model = ""
    if fast_models:
        default_model = fast_models[0]
    elif generative_models:
        default_model = generative_models[0].get("id", "")
    elif all_models:
        default_model = all_models[0]

    return {
        "total_count": len(all_models),
        "fast_models": fast_models,
        "reasoning_models": reasoning_models,
        "generative_models": generative_models,
        "embedding_models": embedding_models,
        "all_models": all_models,
        "current_default": default_model,
    }


def fetch_and_bifurcate_models(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetches available models bifurcated strictly by provider (Ollama vs OpenAI / Remote).
    """
    remote_models = get_available_models(base_url=base_url, api_key=api_key)
    ollama_models = get_ollama_models()

    ollama_bifurcated = _bifurcate_model_list(ollama_models)
    openai_bifurcated = _bifurcate_model_list(remote_models)

    providers = {
        "ollama": {
            "name": "Ollama (Local)",
            "available": len(ollama_models) > 0,
            "base_url": os.getenv("OLLAMA_BASE_URL") or OLLAMA_BASE_URL or "http://localhost:11434",
            **ollama_bifurcated,
        },
        "openai": {
            "name": "OpenAI Compatible (Remote API)",
            "available": len(remote_models) > 0,
            "base_url": base_url or os.getenv("OPENAI_BASE_URL") or OPENAI_BASE_URL,
            **openai_bifurcated,
        },
    }

    # Selected provider or default
    active_prov = provider if provider in providers else ("ollama" if len(ollama_models) > 0 else "openai")
    active_data = providers[active_prov]

    return {
        "status": "success",
        "selected_provider": active_prov,
        "providers": providers,
        "base_url": active_data.get("base_url", ""),
        "total_count": active_data.get("total_count", 0),
        "fast_models": active_data.get("fast_models", []),
        "reasoning_models": active_data.get("reasoning_models", []),
        "generative_models": active_data.get("generative_models", []),
        "embedding_models": active_data.get("embedding_models", []),
        "all_models": active_data.get("all_models", []),
        "current_default": active_data.get("current_default", ""),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and bifurcate available models strictly by provider."
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL for remote API",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API Key for authorization",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Filter by provider ('ollama' or 'openai')",
    )

    args = parser.parse_args()

    print("\nFetching bifurcated models...")
    try:
        result = fetch_and_bifurcate_models(base_url=args.base_url, api_key=args.api_key, provider=args.provider)
    except Exception as err:
        print(f"\n❌ Error: {err}")
        return

    print(f"\n=======================================================")
    print(f"  Model Discovery Summary (Provider: {result['selected_provider']})")
    print(f"  Total Models in Provider: {result['total_count']}")
    print(f"  Fast Models: {result['fast_models']}")
    print(f"  Reasoning Models: {result['reasoning_models']}")
    print(f"  Ollama Total: {result['providers']['ollama']['total_count']}")
    print(f"  OpenAI Total: {result['providers']['openai']['total_count']}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    main()
