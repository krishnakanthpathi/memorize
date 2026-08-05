from typing import Any, Dict, List, Optional

from config.constants import (
    RELEVANCE_SCORE_THRESHOLD,
    WEIGHT_CATEGORY_MATCH,
    WEIGHT_TAG_MATCH,
    WEIGHT_VECTOR_SIMILARITY,
)
from core.logger import handle_errors, logger, time_execution
from search.filter_extractor import extract_keywords_and_snippet
from storage.db_manager import get_all_memories, get_memory_by_id
from vector.embedder import generate_embeddings
from vector.vector_db import query_vector_db


def calculate_tag_match_score(
    query_keywords: List[str], memory_tags: List[str]
) -> float:
    """
    Calculates normalized tag match score (0.0 to 1.0) based on keyword overlaps.
    """
    if not query_keywords or not memory_tags:
        return 0.0

    query_set = set(k.lower() for k in query_keywords)
    tags_set = set(t.lower() for t in memory_tags)

    matches = query_set.intersection(tags_set)
    if not matches:
        return 0.0

    return min(1.0, len(matches) / max(len(query_set), 1))


def calculate_hybrid_score(
    vector_similarity: float,
    query_keywords: List[str],
    memory_tags: List[str],
    memory_category: str,
    target_category: Optional[str] = None,
) -> float:
    """
    Computes weighted hybrid relevance score combining:
    - Vector similarity (50%)
    - Tag match score (30%)
    - Category match score (20%)
    """
    tag_score = calculate_tag_match_score(query_keywords, memory_tags)

    if target_category:
        category_score = 1.0 if memory_category.lower() == target_category.lower() else 0.0
    else:
        category_score = 1.0

    hybrid_score = (
        (WEIGHT_VECTOR_SIMILARITY * vector_similarity)
        + (WEIGHT_TAG_MATCH * tag_score)
        + (WEIGHT_CATEGORY_MATCH * category_score)
    )

    return round(min(1.0, max(0.0, hybrid_score)), 4)


@handle_errors
@time_execution
def search_hybrid_relevance(
    query: str,
    category_filter: Optional[str] = None,
    top_k: int = 5,
    threshold: float = RELEVANCE_SCORE_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Performs hybrid relevance search across ChromaDB vector embeddings and SQLite metadata.
    Returns ranked memory matches with scores exceeding threshold.
    """
    if not query or not query.strip():
        return []

    # 1. Extract query keywords
    query_keywords, _ = extract_keywords_and_snippet(query)

    # 2. Generate vector embedding for query
    query_embeddings = generate_embeddings([query])
    if not query_embeddings:
        logger.warning(f"Could not generate query embedding for '{query}'")
        return []

    # 3. Query ChromaDB for vector matches across memory space
    vector_results = query_vector_db(
        query_embedding=query_embeddings[0],
        n_results=top_k * 3,
        category_filter=None,
    )

    # 4. Load SQLite metadata to enrich memories
    all_indexed = get_all_memories()
    memories_map = {m["id"]: m for m in all_indexed}

    scored_results = []
    seen_memory_ids = set()

    for item in vector_results:
        memory_id = item.get("memory_id", "")
        if not memory_id or memory_id in seen_memory_ids:
            continue
        seen_memory_ids.add(memory_id)

        db_entry = memories_map.get(memory_id) or get_memory_by_id(memory_id) or {}
        memory_tags = item.get("tags", []) or db_entry.get("tags", [])
        memory_category = item.get("category", "") or db_entry.get("category", "personal")
        vector_sim = item.get("similarity_score", 0.0)

        h_score = calculate_hybrid_score(
            vector_similarity=vector_sim,
            query_keywords=query_keywords,
            memory_tags=memory_tags,
            memory_category=memory_category,
            target_category=category_filter,
        )

        if h_score >= threshold:
            scored_results.append({
                "memory_id": memory_id,
                "title": db_entry.get("title", item.get("chunk_id", "")),
                "category": memory_category,
                "tags": memory_tags,
                "snippet": db_entry.get("snippet", item.get("text", "")[:150]),
                "text": item.get("text", ""),
                "vector_similarity": vector_sim,
                "hybrid_score": h_score,
            })

    scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

    logger.info(
        f"Hybrid search for '{query}' returned {len(scored_results[:top_k])} results (threshold={threshold})."
    )
    return scored_results[:top_k]


@handle_errors
@time_execution
def search_vector_similarity(
    query: str,
    category_filter: Optional[str] = None,
    top_k: int = 5,
    threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Performs pure vector similarity search using embeddings in ChromaDB.
    Returns ranked memory matches based solely on vector similarity score.
    """
    if not query or not query.strip():
        return []

    # 1. Generate vector embedding for query
    query_embeddings = generate_embeddings([query])
    if not query_embeddings:
        logger.warning(f"Could not generate query embedding for '{query}'")
        return []

    # 2. Query ChromaDB for vector similarity matches
    vector_results = query_vector_db(
        query_embedding=query_embeddings[0],
        n_results=top_k * 3,
        category_filter=category_filter if category_filter else None,
    )

    # 3. Load SQLite metadata to enrich memories
    all_indexed = get_all_memories()
    memories_map = {m["id"]: m for m in all_indexed}

    scored_results = []
    seen_memory_ids = set()

    for item in vector_results:
        memory_id = item.get("memory_id", "")
        if not memory_id or memory_id in seen_memory_ids:
            continue
        seen_memory_ids.add(memory_id)

        db_entry = memories_map.get(memory_id) or get_memory_by_id(memory_id) or {}
        memory_tags = item.get("tags", []) or db_entry.get("tags", [])
        memory_category = item.get("category", "") or db_entry.get("category", "personal")
        vector_sim = item.get("similarity_score", 0.0)

        if vector_sim >= threshold:
            scored_results.append({
                "memory_id": memory_id,
                "title": db_entry.get("title", item.get("chunk_id", "")),
                "category": memory_category,
                "tags": memory_tags,
                "snippet": db_entry.get("snippet", item.get("text", "")[:150]),
                "text": item.get("text", ""),
                "similarity_score": vector_sim,
            })

    scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    logger.info(
        f"Vector similarity search for '{query}' returned {len(scored_results[:top_k])} results (threshold={threshold})."
    )
    return scored_results[:top_k]

