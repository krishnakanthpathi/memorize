import os
import requests

from typing import List, Union


from config.constants import (
    EMBEDDING_MODEL_NAME,
    FALLBACK_EMBEDDING_MODEL,
    LOCAL_MODEL_CACHE,
    MODELS_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL,
    OPENAI_BASE_URL,
)
from core.logger import handle_errors, logger, time_execution


@handle_errors
@time_execution
def generate_embeddings(
    texts: Union[str, List[str]],
    model_name: str = EMBEDDING_MODEL_NAME,
) -> List[List[float]]:
    """
    Generates vector embeddings for a list of text strings.
    Supports OpenAI, Ollama, and local sentence-transformers fallback.
    """
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        return []

    # 1. Try OpenAI-compatible endpoint
    res = generate_openai_embeddings(texts, model_name=model_name)
    if isinstance(res, list) and len(res) == len(texts) and isinstance(res[0], list):
        return res
    logger.warning(f"OpenAI embedding generation invalid ({res}). Trying Ollama ({OLLAMA_EMBEDDING_MODEL})...")

    # 2. Try Ollama endpoint
    res = generate_ollama_embeddings(texts, model_name=OLLAMA_EMBEDDING_MODEL)
    if isinstance(res, list) and len(res) == len(texts) and isinstance(res[0], list):
        return res
    logger.warning(f"Ollama embedding generation invalid ({res}). Falling back to local SentenceTransformer ({FALLBACK_EMBEDDING_MODEL})...")

    # 3. Fallback to local offline SentenceTransformer model
    return generate_local_embeddings(texts, model_name=FALLBACK_EMBEDDING_MODEL)


@handle_errors
def generate_openai_embeddings(
    texts: List[str],
    api_key: str = None,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> List[List[float]]:
    """Generates embeddings using OpenAI-compatible API."""
    from openai import OpenAI

    client = OpenAI(
        base_url=OPENAI_BASE_URL,
        api_key=api_key if api_key else "lm-studio",
    )
    response = client.embeddings.create(input=texts, model=model_name)
    logger.info(f"Generated {len(texts)} embeddings via OpenAI ({model_name}).")
    return [data.embedding for data in response.data]

@handle_errors
def generate_ollama_embeddings(
    texts: List[str], model_name: str
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
    text: str, model_name: str = EMBEDDING_MODEL_NAME
) -> List[float]:
    """Helper to generate a vector embedding for a single text query."""
    embeddings = generate_embeddings(text, model_name)
    return embeddings[0] if embeddings else []
