import json
import os
import re
from typing import Optional
import requests

from config.constants import (
    LLM_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from core.logger import logger


def generate_openai_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Generates text response using the OpenAI client API endpoint.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured.")

    import openai
    chosen_model = model or OPENAI_MODEL or LLM_MODEL or "gpt-4o-mini"
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=chosen_model,
        messages=messages,
        temperature=temperature,
    )
    if response.choices and len(response.choices) > 0:
        content = response.choices[0].message.content
        if content:
            return content.strip()
    raise RuntimeError("OpenAI API returned an empty response.")


def generate_ollama_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    base_url: Optional[str] = None,
) -> str:
    """
    Generates text response using the Ollama REST API endpoint.
    """
    ollama_model = model or OLLAMA_MODEL or LLM_MODEL or "gpt-oss:120b-cloud"
    effective_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
    url = f"{effective_url}/api/generate"
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    payload = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
        result = resp.json().get("response", "")
        if result:
            return result.strip()
        raise RuntimeError("Ollama API returned an empty response.")
    else:
        raise RuntimeError(f"Ollama request failed with status code {resp.status_code}: {resp.text}")


def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Generates text response with optional provider routing or automatic fallback between OpenAI and Ollama.
    """
    prov_lower = (provider or LLM_PROVIDER or "ollama").strip().lower()

    if prov_lower == "openai":
        return generate_openai_response(prompt, system_prompt, model, temperature)
    elif prov_lower == "ollama":
        return generate_ollama_response(prompt, system_prompt, model, temperature, base_url=base_url)

    # Automatic fallback: Try OpenAI first if configured, then Ollama
    if OPENAI_API_KEY and OPENAI_BASE_URL:
        try:
            return generate_openai_response(prompt, system_prompt, model, temperature)
        except Exception as e:
            logger.warning(f"OpenAI LLM request failed: {e}. Falling back to Ollama.")

    try:
        return generate_ollama_response(prompt, system_prompt, model, temperature, base_url=base_url)
    except Exception as e:
        logger.error(f"Failed to generate LLM response from Ollama: {e}")
        raise RuntimeError(f"Failed to generate response from all configured LLM providers. Details: {e}")


def execute_tool_call(tool_name: str, params: dict) -> dict:
    """
    Executes tool calls requested by the LLM (e.g. search_memories, create_memory, read_memory, delete_memory, list_memories).
    """
    from core.memory_service import execute_upsert_memory, handle_delete_memory
    from search.relevance_scorer import search_hybrid_relevance
    from storage.db_manager import get_all_memories
    from storage.sync_manager import get_memory_file_status

    tool_clean = tool_name.strip().lower()
    if tool_clean in ("create_memory", "store_memory", "upsert_memory"):
        res = execute_upsert_memory(
            title=params.get("title", "Untitled Note"),
            content=params.get("content", ""),
            category=params.get("category", "personal"),
            tags=params.get("tags", []),
            action="auto",
        )
        return {"tool": tool_clean, "status": "success", "result": res}
    elif tool_clean in ("search_memories", "search"):
        results = search_hybrid_relevance(
            query=params.get("query", ""),
            category_filter=params.get("category"),
            top_k=params.get("top_k", 4),
        )
        return {"tool": tool_clean, "status": "success", "result": results}
    elif tool_clean in ("read_memory", "get_memory", "read"):
        mem_id = params.get("memory_id") or params.get("id") or params.get("title", "")
        res = get_memory_file_status(mem_id)
        return {"tool": tool_clean, "status": "success" if res.get("status") != "error" else "error", "result": res}
    elif tool_clean in ("delete_memory", "delete"):
        mem_id = params.get("memory_id") or params.get("id", "")
        res = handle_delete_memory(norm_title="", category="", memory_id=mem_id)
        return {"tool": tool_clean, "status": "success" if res.get("status") == "success" else "error", "result": res}
    elif tool_clean in ("list_memories", "list"):
        cat = params.get("category")
        tag = params.get("tag")
        mems = get_all_memories(category_filter=cat, tag_filter=tag)
        return {"tool": tool_clean, "status": "success", "result": mems}
    elif tool_clean in ("clear_all_memories", "clear_all", "reset_memories", "purge_all", "delete_all"):
        from storage.sync_manager import clear_all_memories
        res = clear_all_memories()
        return {"tool": "clear_all_memories", "status": "success", "result": res}
    else:
        return {"tool": tool_clean, "status": "error", "message": f"Unknown tool: {tool_name}"}


def parse_and_execute_tool(raw_response: str) -> tuple[Optional[dict], str]:
    """
    Parses LLM output for structured JSON tool invocation.
    Robustly extracts embedded JSON objects even if accompanied by explanation text.
    Returns (tool_execution_result, final_or_raw_response).
    """
    cleaned = raw_response.strip()

    # 1. Try stripping markdown code fences
    fence_pattern = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_pattern:
        try:
            data = json.loads(fence_pattern.group(1))
            if isinstance(data, dict) and "tool" in data:
                tool_name = data.get("tool")
                params = data.get("parameters") or data.get("args") or {}
                exec_result = execute_tool_call(tool_name, params)
                return exec_result, raw_response
        except Exception:
            pass

    # 2. Try streaming raw JSON decoding from any opening '{'
    idx = 0
    while True:
        start_idx = cleaned.find("{", idx)
        if start_idx == -1:
            break
        try:
            decoder = json.JSONDecoder()
            data, end_pos = decoder.raw_decode(cleaned[start_idx:])
            if isinstance(data, dict) and "tool" in data:
                tool_name = data.get("tool")
                params = data.get("parameters") or data.get("args") or {}
                exec_result = execute_tool_call(tool_name, params)
                return exec_result, raw_response
        except Exception:
            pass
        idx = start_idx + 1

    return None, raw_response


