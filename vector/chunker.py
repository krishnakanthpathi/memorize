import re
from typing import List, Dict, Any

from config.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    EMBEDDING_MODEL_NAME,
    MODEL_CHUNK_CONFIGS,
)
from core.id_generator import generate_chunk_id
from core.logger import handle_errors, logger


def get_chunk_settings(model_name: str = EMBEDDING_MODEL_NAME) -> Dict[str, int]:
    """Returns optimal chunk_size and overlap for the selected model."""
    return MODEL_CHUNK_CONFIGS.get(
        model_name,
        {"chunk_size": DEFAULT_CHUNK_SIZE, "overlap": DEFAULT_CHUNK_OVERLAP},
    )


def count_tokens(text: str, model_name: str = EMBEDDING_MODEL_NAME) -> int:
    """Calculates token count for text using tiktoken or character ratio estimation."""
    if not text:
        return 0

    if "text-embedding" in model_name or "gpt" in model_name:
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except Exception:
            pass

    return max(1, int(len(text) / 4))


@handle_errors
def chunk_text(
    memory_id: str,
    text: str,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> List[Dict[str, Any]]:
    """
    Simple, clean text chunker.
    Splits any text into chunks strictly under model_name's max token limit with context overlap.
    """
    if not text or not text.strip():
        return []

    settings = get_chunk_settings(model_name)
    max_tokens = settings["chunk_size"]
    overlap_tokens = settings["overlap"]

    total_tokens = count_tokens(text, model_name)

    # Return immediately if total text fits in a single chunk
    if total_tokens <= max_tokens:
        return [
            {
                "chunk_id": generate_chunk_id(memory_id, 0),
                "memory_id": memory_id,
                "chunk_index": 0,
                "text": text.strip(),
                "token_count": total_tokens,
            }
        ]

    words = text.split()
    chunks = []
    chunk_index = 0
    start_idx = 0

    while start_idx < len(words):
        curr_words = []
        end_idx = start_idx

        while end_idx < len(words):
            candidate_words = curr_words + [words[end_idx]]
            candidate_text = " ".join(candidate_words)
            candidate_tokens = count_tokens(candidate_text, model_name)

            if candidate_tokens > max_tokens and curr_words:
                break

            curr_words.append(words[end_idx])
            end_idx += 1

        chunk_str = " ".join(curr_words)
        chunks.append(
            {
                "chunk_id": generate_chunk_id(memory_id, chunk_index),
                "memory_id": memory_id,
                "chunk_index": chunk_index,
                "text": chunk_str,
                "token_count": count_tokens(chunk_str, model_name),
            }
        )
        chunk_index += 1

        if end_idx >= len(words):
            break

        # Calculate overlap by stepping back words up to overlap_tokens
        overlap_w = 0
        overlap_tok = 0
        for w in reversed(curr_words):
            wt = count_tokens(w, model_name)
            if overlap_tok + wt <= overlap_tokens:
                overlap_tok += wt
                overlap_w += 1
            else:
                break

        step = max(1, len(curr_words) - overlap_w)
        start_idx += step

    logger.info(
        f"Chunked memory '{memory_id}' using model '{model_name}' "
        f"({total_tokens} tokens) -> {len(chunks)} chunks."
    )
    return chunks

