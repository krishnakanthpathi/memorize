import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from core.logger import handle_errors, logger
from core.memory_service import execute_upsert_memory, handle_delete_memory
from storage.db_manager import get_all_memories, get_memory_by_id
from storage.markdown_handler import read_markdown_file
from storage.sync_manager import sync_markdown_files
from utils import get_available_categories
from utils.llm_client import generate_llm_response


def calculate_jaccard_similarity(str1: str, str2: str) -> float:
    """Calculates word-level Jaccard similarity between two text strings."""
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


@handle_errors
def detect_duplicate_clusters(
    category_filter: Optional[str] = None,
    min_similarity: float = 0.40,
) -> Dict[str, Any]:
    """
    Scans stored memories within a category or across all categories,
    calculating pairwise title/content similarity to discover clusters of potential duplicates.
    """
    all_mems = get_all_memories(category_filter=category_filter)
    if len(all_mems) < 2:
        return {
            "status": "success",
            "total_memories_checked": len(all_mems),
            "clusters_found": 0,
            "clusters": [],
        }

    clusters = []
    visited_ids = set()

    for i in range(len(all_mems)):
        mem_a = all_mems[i]
        id_a = mem_a["id"]
        if id_a in visited_ids:
            continue

        cluster_members = [mem_a]
        title_a = mem_a.get("title", "")
        tags_a = set(mem_a.get("tags", []))

        for j in range(i + 1, len(all_mems)):
            mem_b = all_mems[j]
            id_b = mem_b["id"]
            if id_b in visited_ids:
                continue

            title_b = mem_b.get("title", "")
            tags_b = set(mem_b.get("tags", []))

            title_sim = calculate_jaccard_similarity(title_a, title_b)
            
            # Check tag overlap
            tag_sim = 0.0
            if tags_a and tags_b:
                tags_a_lower = {t.lower().replace("_", " ") for t in tags_a}
                tags_b_lower = {t.lower().replace("_", " ") for t in tags_b}
                overlap = tags_a_lower.intersection(tags_b_lower)
                if overlap:
                    tag_sim = len(overlap) / max(len(tags_a_lower), len(tags_b_lower))

            # Entity matching: Check if both titles/tags mention the exact same person/subject
            entity_match = False
            words_a = set(re.findall(r'\b[a-zA-Z]{3,}\b', title_a.lower()))
            words_b = set(re.findall(r'\b[a-zA-Z]{3,}\b', title_b.lower()))
            shared_words = words_a.intersection(words_b) - {"details", "summary", "information", "and", "the", "for"}
            if len(shared_words) >= 2:
                entity_match = True

            # Match criteria: high title similarity OR entity match + tag/word overlap
            if title_sim >= min_similarity or entity_match or (title_sim >= 0.20 and tag_sim > 0.0):
                cluster_members.append(mem_b)
                visited_ids.add(id_b)

        if len(cluster_members) > 1:
            visited_ids.add(id_a)
            clusters.append({
                "category": mem_a.get("category", "personal"),
                "memory_count": len(cluster_members),
                "suggested_target_title": title_a,
                "memories": [
                    {
                        "id": m["id"],
                        "title": m["title"],
                        "category": m["category"],
                        "tags": m.get("tags", []),
                        "file_path": m.get("file_path", ""),
                    }
                    for m in cluster_members
                ],
            })

    return {
        "status": "success",
        "total_memories_checked": len(all_mems),
        "clusters_found": len(clusters),
        "clusters": clusters,
    }


@handle_errors
def merge_duplicate_memories(
    memory_ids: List[str],
    target_title: Optional[str] = None,
    target_category: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Intelligently merges multiple duplicate/overlapping memories into a single consolidated memory file
    using LLM synthesis. Purges secondary duplicate files and updates SQLite + ChromaDB index.
    """
    if not memory_ids or len(memory_ids) < 2:
        return {
            "status": "error",
            "message": "At least two memory IDs are required to perform a merge.",
        }

    records = []
    combined_tags = set()
    source_contents = []

    for mid in memory_ids:
        target = get_memory_by_id(mid)
        if not target:
            return {"status": "error", "message": f"Memory with ID '{mid}' not found."}

        file_path = target.get("file_path")
        read_result = read_markdown_file(file_path)
        if isinstance(read_result, dict) and read_result.get("status") == "error":
            return {"status": "error", "message": f"Could not read file for memory '{mid}'."}

        frontmatter, raw_content = read_result
        records.append({
            "id": mid,
            "title": target.get("title"),
            "category": target.get("category"),
            "tags": target.get("tags", []),
            "content": raw_content,
        })
        for tag in target.get("tags", []):
            combined_tags.add(tag)
        source_contents.append(f"--- Document ID: {mid} | Title: {target.get('title')} ---\n{raw_content}")

    primary_record = records[0]
    primary_id = primary_record["id"]
    secondary_ids = [r["id"] for r in records[1:]]

    final_title = target_title or primary_record["title"]
    final_category = target_category or primary_record["category"]

    # Synthesize content using LLM
    system_prompt = (
        "You are an expert memory synthesis assistant. Your goal is to consolidate multiple duplicate "
        "or overlapping memory documents into a single, clean, highly structured Markdown memory document.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. Retain ALL facts, numbers, phone numbers, emails, addresses, ID numbers, dates, technical skills, "
        "and experience details. Absolute zero loss of factual data is allowed.\n"
        "2. Eliminate exact duplicates, repetitive phrasing, and redundant summaries.\n"
        "3. Format cleanly with clear Markdown headers (### level) and concise bullet points.\n"
        "4. Do NOT wrap output in ```markdown block backticks. Return pure markdown text."
    )

    combined_text_prompt = "\n\n".join(source_contents)
    prompt = (
        f"Consolidate and merge the following {len(records)} memory documents into a unified master memory file for '{final_title}':\n\n"
        f"{combined_text_prompt}"
    )

    logger.info(f"Merging {len(memory_ids)} memories into primary memory '{primary_id}' using LLM...")
    merged_content = generate_llm_response(
        prompt=prompt,
        system_prompt=system_prompt,
        model=llm_model,
        temperature=0.1,
    )

    # Clean backticks if LLM included them
    if merged_content.startswith("```"):
        lines = merged_content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        merged_content = "\n".join(lines).strip()

    # Update primary memory with synthesized content
    update_res = execute_upsert_memory(
        title=final_title,
        content=merged_content,
        action="update",
        category=final_category,
        tags=list(combined_tags),
        memory_id=primary_id,
    )

    # Safely purge secondary redundant memories
    deleted_ids = []
    for sec_id in secondary_ids:
        del_res = handle_delete_memory(norm_title="", category="", memory_id=sec_id)
        if del_res.get("status") == "success":
            deleted_ids.append(sec_id)

    # Force full synchronization refresh
    sync_markdown_files()

    return {
        "status": "success",
        "action": "merge",
        "primary_memory_id": primary_id,
        "deleted_memory_ids": deleted_ids,
        "target_title": final_title,
        "target_category": final_category,
        "file_path": update_res.get("file_path"),
        "tags": list(combined_tags),
    }
