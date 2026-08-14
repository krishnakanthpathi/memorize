import logging
import os
import warnings
from typing import List, Optional, Union

import requests

# Suppress HuggingFace / Transformers warnings and progress bars from polluting the CLI
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

for noisy_lib in ("transformers", "sentence_transformers", "huggingface_hub"):
    logging.getLogger(noisy_lib).setLevel(logging.ERROR)

from config.constants import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_PROVIDER,
    FALLBACK_EMBEDDING_MODEL,
    LOCAL_MODEL_CACHE,
    MODELS_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from core.logger import handle_errors, logger, time_execution


@handle_errors
@time_execution
def generate_embeddings(
    texts: Union[str, List[str]],
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> List[List[float]]:
    """
    Unified entry point for generating vector embeddings.
    Dispatches to the provider configured in .env (EMBEDDING_PROVIDER="local" | "openai" | "ollama" | "auto").
    Defaults to fast offline local embeddings ('local') to ensure instant performance.
    """
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        return []

    active_provider = (provider or EMBEDDING_PROVIDER).lower()

    if active_provider == "local":
        return generate_local_embeddings(texts, model_name=model_name or FALLBACK_EMBEDDING_MODEL)
    elif active_provider == "openai":
        return generate_openai_embeddings(texts, model_name=model_name or EMBEDDING_MODEL_NAME)
    elif active_provider == "ollama":
        return generate_ollama_embeddings(texts, model_name=model_name or OLLAMA_EMBEDDING_MODEL)
    elif active_provider == "auto":
        return generate_auto_fallback_embeddings(texts, model_name=model_name or EMBEDDING_MODEL_NAME)
    else:
        logger.warning(f"Unknown provider '{active_provider}'. Falling back to local embeddings.")
        return generate_local_embeddings(texts, model_name=model_name or FALLBACK_EMBEDDING_MODEL)


@handle_errors
def generate_auto_fallback_embeddings(
    texts: List[str],
    model_name: str = EMBEDDING_MODEL_NAME,
) -> List[List[float]]:
    """
    Automatic fallback pipeline: tries OpenAI endpoint, then Ollama, then local SentenceTransformer.
    """
    res = generate_openai_embeddings(texts, model_name=model_name)
    if isinstance(res, list) and len(res) == len(texts) and isinstance(res[0], list):
        return res
    logger.warning(f"OpenAI embedding generation invalid ({res}). Trying Ollama ({OLLAMA_EMBEDDING_MODEL})...")

    res = generate_ollama_embeddings(texts, model_name=OLLAMA_EMBEDDING_MODEL)
    if isinstance(res, list) and len(res) == len(texts) and isinstance(res[0], list):
        return res
    logger.warning(f"Ollama embedding generation invalid ({res}). Falling back to local SentenceTransformer ({FALLBACK_EMBEDDING_MODEL})...")

    return generate_local_embeddings(texts, model_name=FALLBACK_EMBEDDING_MODEL)


@handle_errors
def generate_openai_embeddings(
    texts: List[str],
    api_key: str = None,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> List[List[float]]:
    """Generates embeddings using OpenAI-compatible API."""
    from openai import OpenAI

    effective_api_key = api_key if api_key else (OPENAI_API_KEY if OPENAI_API_KEY else "lm-studio")
    client = OpenAI(
        base_url=OPENAI_BASE_URL,
        api_key=effective_api_key,
    )
    response = client.embeddings.create(input=texts, model=model_name)
    logger.info(f"Generated {len(texts)} embeddings via OpenAI ({model_name}).")
    return [data.embedding for data in response.data]


@handle_errors
def generate_ollama_embeddings(
    texts: List[str], model_name: str = OLLAMA_EMBEDDING_MODEL
) -> List[List[float]]:
    """Generates embeddings using local Ollama instance."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    embeddings = []

    for text in texts:
        payload = {"model": model_name, "prompt": text}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        embeddings.append(data["embedding"])

    logger.info(f"Generated {len(texts)} embeddings via Ollama ({model_name}).")    
    return embeddings


def get_local_model(model_name: str = FALLBACK_EMBEDDING_MODEL):
    """
    Lazy-loads and caches SentenceTransformer model instances in DATA_DIR/models
    to prevent re-downloading and re-instantiating on every call.
    """
    if model_name not in LOCAL_MODEL_CACHE:
        from sentence_transformers import SentenceTransformer

        logger.info(
            f"Initializing local SentenceTransformer '{model_name}' (cache_folder={MODELS_DIR})..."
        )
        try:
            LOCAL_MODEL_CACHE[model_name] = SentenceTransformer(
                model_name,
                cache_folder=str(MODELS_DIR),
                local_files_only=True,
            )
        except Exception:
            LOCAL_MODEL_CACHE[model_name] = SentenceTransformer(
                model_name,
                cache_folder=str(MODELS_DIR),
            )
    return LOCAL_MODEL_CACHE[model_name]


@handle_errors
@time_execution
def generate_local_embeddings(
    texts: List[str], model_name: str = FALLBACK_EMBEDDING_MODEL
) -> List[List[float]]:
    """Generates embeddings using local sentence-transformers (completely offline)."""
    model = get_local_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=False)
    logger.info(
        f"Generated {len(texts)} embeddings via local SentenceTransformer ({model_name})."
    )
    return embeddings.tolist()


@handle_errors
def generate_single_embedding(
    text: str, provider: Optional[str] = None, model_name: Optional[str] = None
) -> List[float]:
    """Helper to generate a vector embedding for a single text query."""
    embeddings = generate_embeddings(text, provider=provider, model_name=model_name)
    return embeddings[0] if embeddings else []
