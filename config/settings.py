import json
from pathlib import Path
from typing import Any, Dict, Optional

from config.constants import (
    ACTIVE_EMBEDDING_MODEL,
    DATA_DIR,
    FALLBACK_EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_CLASSIFICATION_MODEL,
    USE_LLM,
)

SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "use_llm": USE_LLM,
    "embedding_model": ACTIVE_EMBEDDING_MODEL,
    "classification_model": OLLAMA_CLASSIFICATION_MODEL or "gpt-oss:120b-cloud",
    "fallback_model": FALLBACK_EMBEDDING_MODEL,
    "embedding_provider": "local",
    "llm_provider": "ollama",
    "ollama_base_url": OLLAMA_BASE_URL,
    "ollama_model": OLLAMA_CLASSIFICATION_MODEL or "gpt-oss:120b-cloud",
    "search_top_k": 4,
    "auto_context": True,
    "tool_execution": True,
    "temperature": 0.3,
    "memories_dir": str(DATA_DIR / "memories"),
    "storage_layout": "bundle",  # "bundle" (per-memory folder with thumbnails/ and media/) or "flat"
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
    elif key in ("auto_context", "tool_execution", "use_llm") and isinstance(value, str):
        value = value.lower() in ("true", "1", "yes", "on")
    elif key in ("auto_context", "tool_execution", "use_llm") and not isinstance(value, bool):
        value = bool(value)

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


def get_memories_dir() -> Path:
    """
    Returns the resolved Path for the configured memories storage directory.
    Expands ~ (user home) and ensures the directory exists.
    Respects runtime patched constants.MEMORIES_DIR in tests.
    """
    import config.constants as constants
    if constants.MEMORIES_DIR != DATA_DIR / "memories":
        p = Path(constants.MEMORIES_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    path_val = get_setting("memories_dir", str(DATA_DIR / "memories"))
    if not path_val:
        path_val = str(DATA_DIR / "memories")
    resolved = Path(path_val).expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def get_storage_layout() -> str:
    """
    Returns the configured storage layout strategy: 'bundle' (default) or 'flat'.
    """
    return str(get_setting("storage_layout", "bundle")).lower()


def validate_storage_path(path_str: str) -> Dict[str, Any]:
    """
    Validates a target directory path for accessibility, permissions, and available disk space.
    """
    import os
    import shutil

    if not path_str or not path_str.strip():
        return {"valid": False, "error": "Path cannot be empty."}

    try:
        target = Path(path_str).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = target / ".write_test.tmp"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)

        usage = shutil.disk_usage(str(target))
        return {
            "valid": True,
            "resolved_path": str(target),
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "free_gb": round(usage.free / (1024 ** 3), 2),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


# Initialize settings on module load
load_settings()

