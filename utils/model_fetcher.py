import argparse
import os
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv

from config.constants import OPENAI_BASE_URL
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


def classify_model(model_id: str) -> str:
    """
    Classifies a model ID into 'embedding', 'generative', or 'other' based on model name patterns.
    """
    model_id_lower = model_id.lower()

    # Check for explicit embedding markers
    if any(keyword in model_id_lower for keyword in EMBEDDING_KEYWORDS):
        return "embedding"

    # Check for generative / chat markers
    if any(keyword in model_id_lower for keyword in GENERATIVE_KEYWORDS):
        return "generative"

    return "other"


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
        logger.error(f"Failed to fetch models from {models_endpoint}: {e}")
        raise RuntimeError(f"Could not fetch models from '{models_endpoint}': {e}") from e


def fetch_and_bifurcate_models(
    base_url: Optional[str] = None, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches available models from the specified base URL and API key,
    and bifurcates them into embedding models and generative models.

    :param base_url: OpenAI-compatible API base URL (e.g. https://bedrock-mantle.ap-southeast-2.api.aws/v1)
    :param api_key: API authorization key
    :return: Dictionary containing 'embedding_models', 'generative_models', 'other_models', and 'total_count'.
    """
    raw_models = get_available_models(base_url=base_url, api_key=api_key)

    embedding_models: List[Dict[str, Any]] = []
    generative_models: List[Dict[str, Any]] = []
    other_models: List[Dict[str, Any]] = []

    for item in raw_models:
        model_id = item.get("id", "") if isinstance(item, dict) else str(item)
        category = classify_model(model_id)

        model_info = {
            "id": model_id,
            "object": item.get("object", "model") if isinstance(item, dict) else "model",
            "owned_by": item.get("owned_by", "") if isinstance(item, dict) else "",
            "status": item.get("status", "available") if isinstance(item, dict) else "available",
        }

        if category == "embedding":
            embedding_models.append(model_info)
        elif category == "generative":
            generative_models.append(model_info)
        else:
            other_models.append(model_info)

    return {
        "base_url": base_url or os.getenv("OPENAI_BASE_URL") or OPENAI_BASE_URL,
        "total_count": len(raw_models),
        "embedding_models": embedding_models,
        "generative_models": generative_models,
        "other_models": other_models,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and bifurcate available models from an OpenAI-compatible endpoint."
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL for the API (default: OPENAI_BASE_URL constant or env)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API Key for authorization (default: OPENAI_API_KEY env)",
    )

    args = parser.parse_args()

    print("\nFetching models...")
    try:
        result = fetch_and_bifurcate_models(base_url=args.base_url, api_key=args.api_key)
    except Exception as err:
        print(f"\n❌ Error: {err}")
        return

    base_url_used = result["base_url"]
    embedding_models = result["embedding_models"]
    generative_models = result["generative_models"]
    other_models = result["other_models"]

    print(f"\n=======================================================")
    print(f"  Model Discovery Summary")
    print(f"  Base URL: {base_url_used}")
    print(f"  Total Models Found: {result['total_count']}")
    print(f"=======================================================\n")

    print(f"📌 EMBEDDING MODELS ({len(embedding_models)}):")
    if embedding_models:
        for idx, m in enumerate(embedding_models, 1):
            print(f"  {idx}. {m['id']} (Status: {m['status']})")
    else:
        print("  (None found)")

    print(f"\n💬 GENERATIVE / CHAT MODELS ({len(generative_models)}):")
    if generative_models:
        for idx, m in enumerate(generative_models, 1):
            print(f"  {idx}. {m['id']} (Status: {m['status']})")
    else:
        print("  (None found)")

    if other_models:
        print(f"\n❓ OTHER MODELS ({len(other_models)}):")
        for idx, m in enumerate(other_models, 1):
            print(f"  {idx}. {m['id']} (Status: {m['status']})")

    print(f"\n=======================================================\n")


if __name__ == "__main__":
    main()
