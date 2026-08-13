import json
from pathlib import Path
from typing import Any, Dict, Optional

from config.constants import (
    DATA_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_CLASSIFICATION_MODEL,
)

SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "llm_provider": "ollama",
    "ollama_base_url": OLLAMA_BASE_URL,
    "ollama_model": OLLAMA_CLASSIFICATION_MODEL or "gpt-oss:120b-cloud",
    "search_top_k": 4,
    "auto_context": True,
    "tool_execution": True,
    "temperature": 0.3,
}

_SETTINGS: Dict[str, Any] = {}


def load_settings(filepath: Path = SETTINGS_FILE) -> Dict[str, Any]:
    """
    Loads settings from data/settings.json into memory, falling back to defaults.
    """
    global _SETTINGS
    settings = DEFAULT_SETTINGS.copy()
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception:
            pass
    _SETTINGS = settings
    return _SETTINGS


def save_settings(filepath: Path = SETTINGS_FILE) -> bool:
    """
    Saves the current in-memory settings to data/settings.json.
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(_SETTINGS, f, indent=2)
        return True
    except Exception:
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """
    Retrieves a setting value by key.
    """
    if not _SETTINGS:
        load_settings()
    return _SETTINGS.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))


def set_setting(key: str, value: Any, filepath: Path = SETTINGS_FILE) -> bool:
    """
    Updates a setting key with automatic type casting and persists to file.
    """
    if not _SETTINGS:
        load_settings(filepath)

    # Clean type conversion and validation
    if key in ("search_top_k",) and isinstance(value, str) and value.isdigit():
        value = int(value)
    elif key in ("temperature",) and isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            pass
    elif key in ("auto_context", "tool_execution") and isinstance(value, str):
        value = value.lower() in ("true", "1", "yes", "on")

    _SETTINGS[key] = value
    return save_settings(filepath)


def get_all_settings() -> Dict[str, Any]:
    """
    Returns a copy of all current configuration settings.
    """
    if not _SETTINGS:
        load_settings()
    return _SETTINGS.copy()


def reset_settings(filepath: Path = SETTINGS_FILE) -> bool:
    """
    Resets settings back to default values.
    """
    global _SETTINGS
    _SETTINGS = DEFAULT_SETTINGS.copy()
    return save_settings(filepath)


# Initialize settings on module load
load_settings()
