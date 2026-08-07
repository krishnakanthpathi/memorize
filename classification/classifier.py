import json
import re
from typing import Any, Dict, List, Tuple
import requests

from config.constants import (
    CLASSIFIER_MODE,
    MEMORIES_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_CLASSIFICATION_MODEL,
)
from core.logger import handle_errors, logger, time_execution
from utils import get_available_categories, get_category_dir


# Enhanced keyword mapping for fast, highly accurate offline rule classification
RULE_CATEGORY_KEYWORDS = {
    "achievements": ["jee", "percentile", "nta score", "score card", "rank", "ranking", "prize", "winner", "award", "certification", "milestone", "top 1%", "top 5%", "top 8%"],
    "development": ["react", "vue", "tailwind", "shadcn", "frontend", "backend", "typescript", "javascript", "python", "css", "html", "fastapi", "express", "node", "monochrome", "ui", "animation", "animejs", "motion", "framer", "code", "algorithm", "git", "refactor"],
    "projects": ["cms", "queryport", "discord bot", "nullpointer", "local share", "personal assistant", "project", "app", "application", "mern", "architecture", "headless"],
    "job": ["resume", "cartrade", "employed", "salary", "full-stack developer", "full stack", "work experience", "career", "settlement", "job", "company", "interview"],
    "education": ["b.tech", "cgpa", "pragati engineering", "degree", "college", "university", "computer science", "gpa", "school", "exam"],
    "integration": ["mcp", "mcp server", "tailscale", "wsl", "ubuntu", "ssh", "webhook", "api_key", "pipeline", "oauth", "rest_api"],
    "media": ["ocr", "audio", "video", "tts", "text-to-speech", "pdf", "image", "document", "scan", "youtube", "podcast"],
    "finance": ["stock", "investment", "budget", "crypto", "tax", "bank", "money", "savings", "expense"],
    "gaming": ["game", "steam", "playstation", "xbox", "fps", "rpg", "valorant", "nintendo", "score", "match"],
    "personal": ["phone", "email", "contact", "journal", "preference", "sleep", "family", "friend", "home", "diary", "woke", "waking"],
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
            if kw in text_lower:
                score += 2 if " " in kw else 1
                matched_tags.add(kw.replace(" ", "_"))
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        best_cat = max(category_scores, key=category_scores.get)
        return best_cat, list(matched_tags)[:5]

    return "personal", list(words)[:5]


def classify_text_llm(text: str) -> Dict[str, Any]:
    """
    Sends zero-shot prompt to Ollama endpoint to classify text strictly into available predefined categories.
    """
    available_categories = get_available_categories()
    prompt = f"""You are an expert AI memory classifier. Analyze the following text and determine the single best category and 3-5 concise tags.

CRITICAL INSTRUCTION: You MUST choose the category strictly from this predefined list of available categories:
{available_categories}

Do NOT invent, generate, or modify category names under any circumstances. If the text does not fit a specific category cleanly, select 'personal'.

Text:
"{text}"

Return ONLY valid JSON matching this exact structure:
{{
  "category": "one_of_allowed_categories",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.95
}}
"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/generate"
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
            if cat not in available_categories:
                cat = "personal"
            tags = [str(t).strip().lower() for t in result_json.get("tags", [])]
            conf = float(result_json.get("confidence", 0.8))
            return {"category": cat, "tags": tags, "confidence": conf, "method": "llm"}
    except Exception as e:
        logger.warning(f"LLM classification failed ({e}), falling back to rule-based classifier.")

    cat, tags = rule_based_classify(text)
    if cat not in available_categories:
        cat = "personal"
    return {"category": cat, "tags": tags, "confidence": 0.70, "method": "rules"}


@handle_errors
@time_execution
def classify_memory(text: str) -> Dict[str, Any]:
    """
    Primary auto-classification entry point.
    Determines category and extracts tags using predefined categories only.
    """
    if not text or not text.strip():
        return {"category": "personal", "tags": [], "confidence": 1.0, "is_new_category": False}

    if CLASSIFIER_MODE == "rules":
        cat, tags = rule_based_classify(text)
        available_categories = get_available_categories()
        if cat not in available_categories:
            cat = "personal"
        return {"category": cat, "tags": tags, "confidence": 0.90, "method": "rules", "is_new_category": False}

    result = classify_text_llm(text)
    cat = result["category"]
    available_categories = get_available_categories()
    if cat not in available_categories:
        cat = "personal"
        result["category"] = cat

    result["is_new_category"] = False
    return result
