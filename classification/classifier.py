import json
import re
from typing import Any, Dict, List, Tuple
import requests

from config.constants import (
    MEMORIES_DIR,
    OLLAMA_CLASSIFICATION_MODEL,
    OLLAMA_OLLAMA_BASE_URL,
)
from core.logger import handle_errors, logger, time_execution
from storage.index_manager import add_category_to_index
from utils import get_available_categories, get_category_dir


# Fallback keyword mapping for fast offline rule classification
RULE_CATEGORY_KEYWORDS = {
    "personal": ["journal", "sleep", "dream", "health", "habit", "mood", "family", "friend", "home", "diary", "woke", "waking"],
    "job": ["resume", "interview", "career", "salary", "boss", "company", "client", "project", "work", "meeting", "deadline"],
    "study": ["python", "code", "algorithm", "rag", "mcp", "quantum", "physics", "docker", "chroma", "ollama", "math", "course", "lecture"],
    "routine": ["schedule", "alarm", "calendar", "todo", "task", "reminder", "daily", "groceries", "checklist"],
    "media": ["transcript", "ocr", "audio", "video", "pdf", "image", "document", "scan", "youtube"],
    "finance": ["stock", "investment", "budget", "crypto", "tax", "bank", "money", "savings", "expense"],
}


def rule_based_classify(text: str) -> Tuple[str, List[str]]:
    """
    Fast keyword rule classifier that scans text and returns best category and extracted tags.
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    category_scores = {}
    matched_tags = set()

    for cat, keywords in RULE_CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in words or kw in text_lower:
                score += 1
                matched_tags.add(kw)
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        best_cat = max(category_scores, key=category_scores.get)
        return best_cat, list(matched_tags)[:5]

    return "personal", list(words)[:5]


def classify_text_llm(text: str) -> Dict[str, Any]:
    """
    Sends zero-shot prompt to Ollama endpoint to classify text into existing or new category.
    """
    available_categories = get_available_categories()
    prompt = f"""You are an expert AI memory classifier. Analyze the following text and determine the single best category and 3-5 concise tags.
If the text fits one of the existing categories {available_categories}, use it.
If the text does NOT fit existing categories, dynamically create a new lowercase one-word category (e.g. 'finance', 'travel', 'cooking', 'gaming').

Text:
"{text}"

Return ONLY valid JSON matching this exact structure:
{{
  "category": "category_name",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.95
}}
"""
    try:
        url = f"{OLLAMA_OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_CLASSIFICATION_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            result_json = json.loads(response.json().get("response", "{}"))
            cat = str(result_json.get("category", "personal")).strip().lower()
            tags = [str(t).strip().lower() for t in result_json.get("tags", [])]
            conf = float(result_json.get("confidence", 0.8))
            return {"category": cat, "tags": tags, "confidence": conf, "method": "llm"}
    except Exception as e:
        logger.warning(f"LLM classification failed ({e}), falling back to rule-based classifier.")

    cat, tags = rule_based_classify(text)
    return {"category": cat, "tags": tags, "confidence": 0.70, "method": "rules"}


@handle_errors
@time_execution
def classify_memory(text: str) -> Dict[str, Any]:
    """
    Primary auto-classification entry point.
    Determines category, extracts tags, creates category folder on disk if new,
    and updates index.json category registry.
    """
    if not text or not text.strip():
        return {"category": "personal", "tags": [], "confidence": 1.0, "is_new_category": False}

    result = classify_text_llm(text)
    cat = result["category"]

    cat_dir = get_category_dir(cat)
    is_new = False
    gitkeep_file = cat_dir / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.touch()
        add_category_to_index(cat)
        is_new = True
        logger.info(f"Dynamically created new category directory: {cat_dir}")

    result["is_new_category"] = is_new
    return result
