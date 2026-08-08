import re
from typing import Optional

from core.logger import handle_errors, logger
from utils.llm_client import generate_llm_response

SMART_UPDATE_SYSTEM_PROMPT = (
    "You are an expert AI memory manager. Your task is to intelligently merge new information into an existing "
    "Markdown memory document.\n"
    "Rules:\n"
    "1. Preserve unchanged context and structure from the existing memory.\n"
    "2. Replace outdated or superseded details with the new facts.\n"
    "3. Seamlessly integrate new details into relevant existing sections or add new logical section headers if needed.\n"
    "4. Do NOT naively append '### Update' sections at the bottom unless it represents a distinct timeline event.\n"
    "5. Do NOT include conversation preambles, intros, or markdown block ticks (e.g. ```markdown ... ```).\n"
    "6. Output ONLY the complete, cleanly updated Markdown content body."
)


@handle_errors
def smart_merge_memory_content(
    existing_content: str,
    new_input: str,
    title: str = "Memory",
) -> str:
    """
    Intelligently merges new information or edit prompts into existing memory content using LLM.
    Provides robust fallback to section appending if LLM generation fails.
    """
    if not existing_content.strip():
        return new_input.strip()

    if not new_input.strip():
        return existing_content.strip()

    prompt = (
        f"Title: {title}\n\n"
        f"--- EXISTING MEMORY CONTENT ---\n"
        f"{existing_content.strip()}\n\n"
        f"--- NEW INFORMATION / EDIT REQUEST ---\n"
        f"{new_input.strip()}\n\n"
        f"Generate the updated Markdown body integrating all changes cleanly:"
    )

    try:
        merged_output = generate_llm_response(
            prompt=prompt,
            system_prompt=SMART_UPDATE_SYSTEM_PROMPT,
            temperature=0.2,
        )

        if merged_output:
            # Clean up markdown code fence if LLM wrapped output
            cleaned = re.sub(r"^```markdown\s*", "", merged_output.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"^```\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            if cleaned:
                logger.info(f"Successfully performed LLM smart memory merge for '{title}'.")
                return cleaned.strip()

    except Exception as e:
        logger.warning(f"Smart memory LLM merge failed for '{title}': {e}. Falling back to standard merge.")

    # Fallback if LLM fails
    return f"{existing_content.strip()}\n\n{new_input.strip()}"
