import json
from pathlib import Path
from typing import Dict, Any
from config.constants import DATA_DIR
from core.logger import logger

PROMPTS_FILE = DATA_DIR / "prompts.json"

DEFAULT_PROMPTS = {
    "auto_suggest": (
        "You are an AI Copilot for intelligent note-taking.\n"
        "Analyze the user's current note draft and generate 2-4 concise bullet points suggesting logical next sections, key insights, or action items.\n\n"
        "Title: {title}\n"
        "Current Content:\n"
        "\"{content}\"\n\n"
        "FORMAT REQUIREMENTS:\n"
        "- Provide clean, direct bullet points or markdown items only.\n"
        "- Do NOT repeat the existing content.\n"
        "- Keep output concise (max 3-4 bullet points)."
    ),
    "auto_organize": (
        "You are an intelligent note organizer and memory manager assistant.\n"
        "Analyze the following raw note content and refine it into a structured, clean note.\n\n"
        "Input Content:\n\"{content}\"\n\n"
        "User Provided Title (if any): \"{title}\"\n"
        "Available System Categories: {available_categories}\n\n"
        "INSTRUCTIONS:\n"
        "1. Title: Generate a short, descriptive 3-6 word title.\n"
        "2. Category: Select the best fitting category strictly from Available System Categories.\n"
        "3. Tags: Provide 3-5 concise, relevant tags (lowercase, single-word or snake_case).\n"
        "4. Summary: Provide a 1-2 sentence executive summary.\n"
        "5. Organized Content: Clean up formatting, organize with bullet points or markdown headings.\n\n"
        "Return ONLY a valid JSON object:\n"
        "{{\n"
        "  \"title\": \"Clean Descriptive Title\",\n"
        "  \"category\": \"one_of_allowed_categories\",\n"
        "  \"tags\": [\"tag1\", \"tag2\"],\n"
        "  \"summary\": \"1-2 sentence summary\",\n"
        "  \"organized_content\": \"Full markdown cleaned text\"\n"
        "}}"
    ),
    "smart_merge": (
        "You are an AI Memory Modification Assistant.\n"
        "Contextually merge the new draft content into the existing memory note without losing existing facts.\n\n"
        "Existing Title: \"{title}\"\n"
        "Existing Content:\n\"{existing_content}\"\n\n"
        "New Incoming Content:\n\"{content}\"\n\n"
        "INSTRUCTIONS:\n"
        "Combine information cleanly into markdown format. Output valid JSON with 'title', 'category', 'tags', 'summary', and 'organized_content'."
    ),
    "graph_chat": (
        "You are GraphRAG Companion, an intelligent AI memory synthesis engine.\n"
        "Answer the user query using the retrieved notes context. Highlight key entity connections and provide concise responses."
    ),
}

_PROMPTS_CACHE: Dict[str, str] = {}


def load_prompts() -> Dict[str, str]:
    """Loads prompt templates from disk JSON store or defaults."""
    global _PROMPTS_CACHE
    if _PROMPTS_CACHE:
        return _PROMPTS_CACHE

    prompts = dict(DEFAULT_PROMPTS)
    if PROMPTS_FILE.exists():
        try:
            with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    prompts.update(saved)
        except Exception as e:
            logger.warning(f"Failed to read custom prompts from {PROMPTS_FILE}: {e}")

    _PROMPTS_CACHE = prompts
    return _PROMPTS_CACHE


def save_prompts(new_prompts: Dict[str, str]) -> Dict[str, str]:
    """Updates prompt templates and saves to disk JSON store."""
    global _PROMPTS_CACHE
    current = load_prompts()
    for key, val in new_prompts.items():
        if key in DEFAULT_PROMPTS and isinstance(val, str) and val.strip():
            current[key] = val.strip()

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        logger.info(f"Updated prompt configurations saved to {PROMPTS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save prompts to {PROMPTS_FILE}: {e}")

    _PROMPTS_CACHE = current
    return _PROMPTS_CACHE


def get_prompt(key: str) -> str:
    """Retrieves a specific prompt template by key."""
    prompts = load_prompts()
    return prompts.get(key, DEFAULT_PROMPTS.get(key, ""))


def reset_prompts_to_defaults() -> Dict[str, str]:
    """Resets prompt configurations back to factory defaults."""
    global _PROMPTS_CACHE
    _PROMPTS_CACHE = dict(DEFAULT_PROMPTS)
    if PROMPTS_FILE.exists():
        try:
            PROMPTS_FILE.unlink()
        except Exception as e:
            logger.warning(f"Error removing {PROMPTS_FILE}: {e}")
    return _PROMPTS_CACHE
