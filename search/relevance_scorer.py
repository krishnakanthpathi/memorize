import re
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


def calculate_text_match_score(
    query_keywords: List[str],
    db_entry: Dict[str, Any],
    memory_tags: List[str],
) -> float:
    """
    Calculates composite text match score (0.0 to 1.0) matching query terms against
    title, tags, keywords, snippet, and content.
    """
    if not query_keywords:
        return 0.0

    query_set = set(k.lower() for k in query_keywords)
    if not query_set:
        return 0.0

    title = (db_entry.get("title") or "").lower()
    snippet = (db_entry.get("snippet") or "").lower()
    content = (db_entry.get("content") or "").lower()
    db_keywords = [k.lower() for k in (db_entry.get("keywords") or [])]
    tags = [t.lower() for t in (memory_tags or db_entry.get("tags") or [])]

    total_score = 0.0
    for q in query_set:
        term_score = 0.0
        if any(q in t for t in tags):
            term_score += 0.5
        if q in title:
            term_score += 0.5
        if any(q in k for k in db_keywords):
            term_score += 0.4
        if q in snippet or q in content:
            term_score += 0.3
        total_score += min(1.0, term_score)

    return min(1.0, total_score / max(len(query_set), 1))


def calculate_hybrid_score(
    vector_similarity: float,
    query_keywords: List[str],
    memory_tags: List[str],
    memory_category: str,
    target_category: Optional[str] = None,
    db_entry: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Computes weighted hybrid relevance score combining:
    - Vector similarity (40%)
    - Text & Tag match score (40%)
    - Category match score (20%)
    """
    text_score = calculate_text_match_score(query_keywords, db_entry or {}, memory_tags)

    if target_category:
        category_score = 1.0 if memory_category.lower() == target_category.lower() else 0.0
    else:
        category_score = 1.0

    hybrid_score = (
        (0.40 * vector_similarity)
        + (0.40 * text_score)
        + (0.20 * category_score)
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

    # 1. Extract query keywords (extract_keywords_and_snippet returns snippet, keywords)
    _, query_keywords = extract_keywords_and_snippet(query)
    if not query_keywords:
        query_keywords = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]+\b", query) if len(w) > 1]

    # 2. Generate vector embedding for query
    query_embeddings = generate_embeddings([query])

    vector_results = []
    if query_embeddings:
        raw_res = query_vector_db(
            query_embedding=query_embeddings[0],
            n_results=top_k * 4,
            category_filter=None,
        )
        if isinstance(raw_res, list):
            vector_results = raw_res

    # 3. Load SQLite metadata to enrich candidate memories
    all_indexed = get_all_memories()
    memories_map = {m["id"]: m for m in all_indexed}

    vector_sim_map = {}
    vector_item_map = {}
    for item in vector_results:
        if isinstance(item, dict):
            mem_id = item.get("memory_id", "")
            if mem_id and mem_id not in vector_sim_map:
                vector_sim_map[mem_id] = item.get("similarity_score", 0.0)
                vector_item_map[mem_id] = item

    # 4. Gather candidate memory IDs (from vector search + direct SQLite keyword matches)
    candidate_ids = set(vector_sim_map.keys())
    query_lower = query.lower().strip()

    for m_id, m_data in memories_map.items():
        m_title = (m_data.get("title") or "").lower()
        m_content = (m_data.get("content") or "").lower()
        m_tags = [t.lower() for t in (m_data.get("tags") or [])]
        if query_lower in m_title or query_lower in m_content or any(query_lower in t for t in m_tags):
            candidate_ids.add(m_id)
        elif any(k in m_title or k in m_content for k in query_keywords if len(k) > 2):
            candidate_ids.add(m_id)

    scored_results = []

    for memory_id in candidate_ids:
        db_entry = memories_map.get(memory_id) or get_memory_by_id(memory_id) or {}
        item = vector_item_map.get(memory_id, {})

        memory_tags = item.get("tags", []) or db_entry.get("tags", [])
        memory_category = item.get("category", "") or db_entry.get("category", "personal")
        vector_sim = vector_sim_map.get(memory_id, 0.0)

        # Filter by category if requested
        if category_filter and memory_category.lower() != category_filter.lower():
            continue

        h_score = calculate_hybrid_score(
            vector_similarity=vector_sim,
            query_keywords=query_keywords,
            memory_tags=memory_tags,
            memory_category=memory_category,
            target_category=category_filter,
            db_entry=db_entry,
        )

        if h_score >= threshold:
            scored_results.append({
                "id": memory_id,
                "memory_id": memory_id,
                "title": db_entry.get("title") or item.get("chunk_id") or memory_id,
                "category": memory_category,
                "tags": memory_tags,
                "snippet": db_entry.get("snippet") or (item.get("text", "")[:150] if item else ""),
                "content": db_entry.get("content") or item.get("text", ""),
                "text": item.get("text") or db_entry.get("content", ""),
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
    vector_results = []
    raw_res = query_vector_db(
        query_embedding=query_embeddings[0],
        n_results=top_k * 3,
        category_filter=category_filter if category_filter else None,
    )
    if isinstance(raw_res, list):
        vector_results = raw_res

    # 3. Load SQLite metadata to enrich memories
    all_indexed = get_all_memories()
    memories_map = {m["id"]: m for m in all_indexed}

    scored_results = []
    seen_memory_ids = set()

    for item in vector_results:
        if not isinstance(item, dict):
            continue
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
                "id": memory_id,
                "memory_id": memory_id,
                "title": db_entry.get("title", item.get("chunk_id", "")),
                "category": memory_category,
                "tags": memory_tags,
                "snippet": db_entry.get("snippet", item.get("text", "")[:150]),
                "content": db_entry.get("content", item.get("text", "")),
                "text": item.get("text", ""),
                "similarity_score": vector_sim,
            })

    scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    logger.info(
        f"Vector similarity search for '{query}' returned {len(scored_results[:top_k])} results (threshold={threshold})."
    )
    return scored_results[:top_k]


