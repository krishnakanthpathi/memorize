import re
from typing import Any, Dict, List, Tuple

from config.constants import CLASSIFIER_MODE
from config.settings import get_setting
from core.llm_tasks import llm_classify_text
from core.logger import handle_errors, logger, time_execution
from utils import get_available_categories


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
    "personal": ["phone", "email", "contact", "journal", "preference", "sleep", "family", "friend", "home", "diary", "woke", "waking", "habit", "food", "lifestyle"],
    "others": ["misc", "miscellaneous", "note", "temporary", "random", "other", "general"],
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
    Sends prompt to LLM to classify text strictly into available predefined categories.
    Falls back to rule-based classification on failure.
    """
    available_categories = get_available_categories()
    try:
        return llm_classify_text(text, available_categories)
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
    Honors use_llm setting (offline rules when use_llm is False).
    """
    if not text or not text.strip():
        return {"category": "personal", "tags": [], "confidence": 1.0, "is_new_category": False}

    use_llm = bool(get_setting("use_llm", False))
    if not use_llm or CLASSIFIER_MODE == "rules":
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
