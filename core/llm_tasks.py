"""
Dedicated LLM Task Implementations.
Separates prompt construction, token limits, and LLM completions from domain logic and persistence.
"""

import json
import re
from typing import Any, Dict, List, Optional

from config.constants import (
    OLLAMA_BASE_URL,
    OLLAMA_CLASSIFICATION_MODEL,
)
from config.prompts import (
    AUTO_CLASSIFY_SYSTEM_PROMPT,
    MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
    ORGANIZE_MEMORY_SYSTEM_PROMPT,
    ORGANIZE_SELECTION_SYSTEM_PROMPT,
    SMART_MERGE_SYSTEM_PROMPT,
    TITLE_GENERATION_PROMPT,
)
from config.settings import get_setting
from core.logger import logger
from storage.markdown_handler import normalize_title
from utils.llm_client import (
    clean_llm_markdown_output,
    generate_json_response,
    generate_llm_response,
)

DEFAULT_MAX_MERGE_CONTEXT_TOKENS = 3500


def clean_generated_title(raw_title: str) -> str:
    """Strips quotes, prefixes, markdown artifacts and normalizes a generated title."""
    if not raw_title:
        return "Untitled Note"
    clean = raw_title.strip()
    clean = re.sub(r"^[\"\'`]+|[\"\'`]+$", "", clean).strip()
    clean = re.sub(r"^(?:#+\s*|\*{1,2})?(?:title|summary|topic):\s*", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^#+\s*", "", clean).strip()
    clean = re.sub(r"^\*\*(.*?)\*\*$", r"\1", clean).strip()
    clean = re.sub(r"^\*(.*?)\*$", r"\1", clean).strip()
    clean = clean.split("\n")[0].strip()
    clean = re.sub(r"^\d+[\.\)]\s*", "", clean).strip()
    return normalize_title(clean) if clean else "Untitled Note"


def llm_classify_text(text: str, available_categories: List[str]) -> Dict[str, Any]:
    """
    Classifies text into available categories and extracts tags using the centralized LLM client.
    """
    model_name = str(get_setting("classification_model", OLLAMA_CLASSIFICATION_MODEL))
    base_url = str(get_setting("ollama_base_url", OLLAMA_BASE_URL))
    provider = str(get_setting("llm_provider", "ollama"))

    prompt = (
        f"Available categories: {available_categories}\n\n"
        f"Text to classify:\n\"{text[:2000]}\"\n\n"
        f"Return JSON with category (must be in available list) and 3-5 lowercase tags."
    )

    try:
        data = generate_json_response(
            prompt=prompt,
            system_prompt=AUTO_CLASSIFY_SYSTEM_PROMPT,
            model=model_name,
            temperature=0.1,
            provider=provider,
            base_url=base_url,
        )
        cat = str(data.get("category", "personal")).strip().lower()
        if cat not in available_categories:
            cat = "personal"
        tags = [str(t).strip().lower() for t in data.get("tags", [])]
        conf = float(data.get("confidence", 0.85))
        return {"category": cat, "tags": tags, "confidence": conf, "method": "llm"}
    except Exception as e:
        logger.warning(f"LLM classification failed ({e}).")
        raise e


def llm_synthesize_memories(
    memories: List[Dict[str, Any]],
    target_title: str,
    custom_instruction: Optional[str] = None,
) -> str:
    """
    Direct multi-memory synthesis prompt when total context comfortably fits single prompt.
    """
    instruction_note = f"\nUser Instruction / Goal: {custom_instruction.strip()}\n" if custom_instruction else ""

    sections = []
    for idx, mem in enumerate(memories, start=1):
        m_title = mem.get("title", f"Note {idx}")
        m_content = mem.get("content", "").strip()
        m_cat = mem.get("category", "general")
        sections.append(f"--- NOTE #{idx}: {m_title} (Category: {m_cat}) ---\n{m_content}\n")

    combined_notes = "\n".join(sections)
    prompt = (
        f"Target Unified Document Title: {target_title}\n"
        f"{instruction_note}\n"
        f"Source Notes to Consolidate:\n\n{combined_notes}\n\n"
        f"Consolidated Authoritative Markdown Document:"
    )

    res = generate_llm_response(
        prompt=prompt,
        system_prompt=MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
        temperature=0.2,
    )
    return clean_llm_markdown_output(res)


def progressive_llm_merge(
    memories: List[Dict[str, Any]],
    target_title: str,
    custom_instruction: Optional[str] = None,
    max_context_tokens: int = DEFAULT_MAX_MERGE_CONTEXT_TOKENS,
) -> str:
    """
    Progressively folds multiple memories chunk-by-chunk to stay strictly within token budgets.
    """
    if not memories:
        return ""

    current_merged = memories[0].get("content", "").strip()
    instruction_note = f"\nSpecial Instruction: {custom_instruction.strip()}" if custom_instruction else ""

    for idx in range(1, len(memories)):
        next_mem = memories[idx]
        next_title = next_mem.get("title", f"Note {idx + 1}")
        next_content = next_mem.get("content", "").strip()

        prompt = (
            f"Consolidated Title: {target_title}\n"
            f"{instruction_note}\n\n"
            f"--- EXISTING CONSOLIDATED KNOWLEDGE ---\n"
            f"{current_merged}\n\n"
            f"--- NEW NOTE TO INTEGRATE ({next_title}) ---\n"
            f"{next_content}\n\n"
            f"Synthesize all unique details, code snippets, and facts into the consolidated document:"
        )

        try:
            res = generate_llm_response(
                prompt=prompt,
                system_prompt=MULTI_MEMORY_MERGE_SYSTEM_PROMPT,
                temperature=0.2,
            )
            cleaned = clean_llm_markdown_output(res)
            if cleaned:
                current_merged = cleaned
            else:
                current_merged = f"{current_merged}\n\n## {next_title}\n{next_content}"
        except Exception as e:
            logger.warning(f"Step {idx} of progressive merge failed: {e}. Appending deterministically.")
            current_merged = f"{current_merged}\n\n## {next_title}\n{next_content}"

    return current_merged


def llm_organize_note(
    content: str,
    title: str,
    category: str,
    tags: List[str],
    instruction: Optional[str] = None,
) -> str:
    """
    Polishes, restructures, and cleans an individual memory note using LLM.
    """
    instruction_note = f"\nUser Instruction / Goal: {instruction.strip()}\n" if instruction else ""
    prompt = (
        f"Document Title: {title}\n"
        f"Category: {category}\n"
        f"Tags: {', '.join(tags) if tags else 'none'}\n"
        f"{instruction_note}\n"
        f"--- ORIGINAL CONTENT ---\n"
        f"{content}\n\n"
        f"Polished, well-structured, clean Markdown document:"
    )

    res = generate_llm_response(
        prompt=prompt,
        system_prompt=ORGANIZE_MEMORY_SYSTEM_PROMPT,
        temperature=0.2,
    )
    return clean_llm_markdown_output(res)


def llm_generate_title(
    content: str,
    current_title: Optional[str] = None,
    instruction: Optional[str] = None,
) -> str:
    """
    Generates a concise, high-signal title (3-7 words) from note content.
    """
    prompt_parts = []
    if current_title and current_title not in ("Untitled Note", "Untitled Memory", "Untitled", "Note"):
        prompt_parts.append(f"Current Working Title: {current_title}")
    if instruction:
        prompt_parts.append(f"User Goal / Context: {instruction}")
    prompt_parts.append(f"Content Body:\n{content[:3500]}\n")
    prompt_parts.append("Generate concise descriptive title:")
    prompt = "\n".join(prompt_parts)

    res = generate_llm_response(
        prompt=prompt,
        system_prompt=TITLE_GENERATION_PROMPT,
        temperature=0.3,
    )
    return clean_generated_title(res)


def llm_transform_selection(
    selected_text: str,
    mode: str = "polish",
    instruction: Optional[str] = None,
    full_context: Optional[str] = None,
) -> str:
    """
    Transforms a selected passage or paragraph (polish, summarize, tech-doc format, etc.) using LLM.
    """
    mode_instructions = {
        "polish": "Polish grammar, improve sentence flow, fix indentation, and format cleanly as Markdown.",
        "summarize": "Summarize the core insights of this selection into concise, high-impact bullet points.",
        "technical": "Restructure and format as clean technical documentation with clear subheadings, code syntax blocks, equations ($...$), or parameter lists.",
        "simplify": "Simplify this passage for maximum clarity and quick readability while keeping all key facts.",
        "expand": "Elaborate on the key ideas with structured explanations and concrete details.",
    }

    effective_instruction = instruction if instruction else mode_instructions.get(mode, mode_instructions["polish"])

    prompt_parts = []
    if full_context:
        prompt_parts.append(f"Surrounding Document Context:\n{full_context[:1200]}\n")
    prompt_parts.append(f"Task / Goal: {effective_instruction}")
    prompt_parts.append(f"--- SELECTED TEXT TO TRANSFORM ---\n{selected_text}\n\nTransformed Markdown Replacement:")
    prompt = "\n".join(prompt_parts)

    res = generate_llm_response(
        prompt=prompt,
        system_prompt=ORGANIZE_SELECTION_SYSTEM_PROMPT,
        temperature=0.2,
    )
    return clean_llm_markdown_output(res)


def llm_smart_update(
    existing_content: str,
    new_input: str,
    title: str = "Memory",
) -> str:
    """
    Merges new information into existing memory content using LLM.
    """
    prompt = (
        f"Title: {title}\n\n"
        f"--- EXISTING MEMORY CONTENT ---\n"
        f"{existing_content.strip()}\n\n"
        f"--- NEW INFORMATION / EDIT REQUEST ---\n"
        f"{new_input.strip()}\n\n"
        f"Generate the updated Markdown body integrating all changes cleanly:"
    )

    merged_output = generate_llm_response(
        prompt=prompt,
        system_prompt=SMART_MERGE_SYSTEM_PROMPT,
        temperature=0.2,
    )
    return clean_llm_markdown_output(merged_output)
