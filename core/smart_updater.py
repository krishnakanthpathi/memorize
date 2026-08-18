from typing import Optional

from config.settings import get_setting
from core.llm_tasks import llm_smart_update
from core.logger import handle_errors, logger


@handle_errors
def smart_merge_memory_content(
    existing_content: str,
    new_input: str,
    title: str = "Memory",
) -> str:
    """
    Intelligently merges new information or edit prompts into existing memory content using LLM
    if use_llm is enabled; otherwise performs fast clean deterministic append/merge.
    Provides robust fallback to section appending if LLM generation fails.
    """
    if not existing_content.strip():
        return new_input.strip()

    if not new_input.strip() or existing_content.strip() == new_input.strip():
        return existing_content.strip()

    # If LLM is disabled via settings or mcp/config.py, perform fast deterministic merge
    if not get_setting("use_llm", False):
        if new_input.strip() in existing_content:
            return existing_content.strip()
        return f"{existing_content.strip()}\n\n{new_input.strip()}"

    try:
        cleaned = llm_smart_update(existing_content=existing_content, new_input=new_input, title=title)
        if cleaned:
            logger.info(f"Successfully performed LLM smart memory merge for '{title}'.")
            return cleaned.strip()
    except Exception as e:
        logger.warning(f"Smart memory LLM merge failed for '{title}': {e}. Falling back to standard merge.")

    # Fallback if LLM fails
    return f"{existing_content.strip()}\n\n{new_input.strip()}"
