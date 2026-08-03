from config.constants import OPENAI_BASE_URL
import os
import requests
from typing import List, Union

from config.constants import (
    EMBEDDING_MODEL_NAME,
    OLLAMA_EMBEDDING_MODEL,
    OLLAMA_OLLAMA_BASE_URL,
    FALLBACK_EMBEDDING_MODEL,
)
from core.logger import handle_errors, logger


@handle_errors
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

    # 1. Try OpenAI API if OPENAI_API_KEY is available
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and ("text-embedding" in model_name or "openai" in model_name.lower()):
        try:
            return generate_openai_embeddings(texts, model_name, openai_key)
        except Exception as e:
            logger.warning(f"OpenAI embedding failed ({e}). Trying fallback providers...")

    # 2. Try Ollama if Ollama model is requested or running
    if "nomic" in model_name or "ollama" in model_name.lower():
        try:
            return generate_ollama_embeddings(texts, OLLAMA_EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(f"Ollama embedding failed ({e}). Trying local fallback...")

    # 3. Fallback to local HuggingFace sentence-transformers (Offline)
    return generate_local_embeddings(texts)

@handle_errors
def generate_openai_embeddings(
    texts: List[str], 
    model_name: str, 
    api_key: str,
    base_url: str = OPENAI_BASE_URL
) -> List[List[float]]:
    """Generates embeddings using OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.embeddings.create(input=texts, model=model_name)
    logger.info(f"Generated {len(texts)} embeddings via OpenAI ({model_name}).")
    return [data.embedding for data in response.data]

@handle_errors
def generate_ollama_embeddings(
    texts: List[str], model_name: str
) -> List[List[float]]:
    """Generates embeddings using local Ollama instance."""
    url = f"{OLLAMA_OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    embeddings = []

    for text in texts:
        payload = {"model": model_name, "prompt": text}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        embeddings.append(data["embedding"])

    logger.info(f"Generated {len(texts)} embeddings via Ollama ({model_name}).")
    return embeddings

@handle_errors
def generate_local_embeddings(texts: List[str]) -> List[List[float]]:
    """Generates embeddings using local sentence-transformers (completely offline)."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(FALLBACK_EMBEDDING_MODEL)
    embeddings = model.encode(texts, show_progress_bar=False)
    logger.info(
        f"Generated {len(texts)} embeddings via local SentenceTransformer ({FALLBACK_EMBEDDING_MODEL})."
    )
    return embeddings.tolist()


@handle_errors
def generate_single_embedding(
    text: str, model_name: str = EMBEDDING_MODEL_NAME
) -> List[float]:
    """Helper to generate a vector embedding for a single text query."""
    embeddings = generate_embeddings(text, model_name)
    return embeddings[0] if embeddings else []
