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
from utils.llm_client import parse_and_execute_tool, execute_tool_call
from cli.commands import handle_create, handle_settings


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


def test_parse_and_execute_tool_store():
    raw_llm_json = '```json\n{"tool": "store", "parameters": {"title": "Test Lean Tool Memory", "content": "Sample content from tool", "category": "projects", "tags": ["lean", "test"]}}\n```'
    exec_result, _ = parse_and_execute_tool(raw_llm_json)
    
    assert exec_result is not None
    assert exec_result.get("tool") == "store"
    assert exec_result.get("status") == "success"
    result_data = exec_result.get("result", {})
    assert result_data.get("status") == "success"
    assert result_data.get("title") == "Test Lean Tool Memory"


def test_parse_and_execute_tool_hybrid_fetch():
    raw_llm_json = '{"tool": "hybrid_fetch", "parameters": {"query": "test"}}'
    exec_result, _ = parse_and_execute_tool(raw_llm_json)
    
    assert exec_result is not None
    assert exec_result.get("tool") == "hybrid_fetch"
    assert exec_result.get("status") == "success"
    assert isinstance(exec_result.get("result"), list)

