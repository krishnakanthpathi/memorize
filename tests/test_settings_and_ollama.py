import json
import os
from pathlib import Path

from config.settings import (
    get_all_settings,
    get_setting,
    load_settings,
    reset_settings,
    set_setting,
)


def test_settings_functions(tmp_path: Path):
    settings_file = tmp_path / "test_settings.json"

    # Load defaults
    load_settings(filepath=settings_file)
    assert get_setting("llm_provider") == "ollama"
    assert get_setting("auto_context") is True
    assert get_setting("search_top_k") == 4

    # Update settings
    assert set_setting("llm_provider", "openai", filepath=settings_file) is True
    assert set_setting("search_top_k", "8", filepath=settings_file) is True
    assert get_setting("llm_provider") == "openai"
    assert get_setting("search_top_k") == 8

    # Verify file content on disk
    with open(settings_file, "r") as f:
        data = json.load(f)
    assert data.get("llm_provider") == "openai"
    assert data.get("search_top_k") == 8

    # Test use_llm and model parameters
    assert set_setting("use_llm", "true", filepath=settings_file) is True
    assert get_setting("use_llm") is True
    assert set_setting("use_llm", False, filepath=settings_file) is True
    assert get_setting("use_llm") is False
    assert set_setting("embedding_model", "bge-m3", filepath=settings_file) is True
    assert get_setting("embedding_model") == "bge-m3"

    # Reset settings
    assert reset_settings(filepath=settings_file) is True
    assert get_setting("llm_provider") == "ollama"
    assert get_setting("search_top_k") == 4
