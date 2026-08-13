import json
import os
from typing import Optional
import requests

from config.constants import (
    OLLAMA_BASE_URL,
    OLLAMA_CLASSIFICATION_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from core.logger import logger

DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")


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
    chosen_model = model or DEFAULT_LLM_MODEL
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
    ollama_model = model or OLLAMA_CLASSIFICATION_MODEL or "gpt-oss:120b-cloud"
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
    prov_lower = (provider or "").strip().lower()

    if prov_lower == "openai":
        return generate_openai_response(prompt, system_prompt, model, temperature)
    elif prov_lower == "ollama":
        return generate_ollama_response(prompt, system_prompt, model, temperature, base_url=base_url)

    # Automatic fallback: Try OpenAI first if configured, then Ollama
    if OPENAI_API_KEY:
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
    Executes tool calls requested by the LLM (e.g. search_memories, create_memory).
    """
    from core.memory_service import execute_upsert_memory
    from search.relevance_scorer import search_hybrid_relevance

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
    else:
        return {"tool": tool_clean, "status": "error", "message": f"Unknown tool: {tool_name}"}


def parse_and_execute_tool(raw_response: str) -> tuple[Optional[dict], str]:
    """
    Parses LLM output for structured JSON tool invocation.
    Returns (tool_execution_result, final_or_raw_response).
    """
    cleaned = raw_response.strip()
    # Try parsing direct JSON or JSON enclosed in ```json ```
    json_str = None
    if cleaned.startswith("```json") and cleaned.endswith("```"):
        json_str = cleaned[7:-3].strip()
    elif cleaned.startswith("```") and cleaned.endswith("```"):
        json_str = cleaned[3:-3].strip()
    elif cleaned.startswith("{") and cleaned.endswith("}"):
        json_str = cleaned

    if json_str:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "tool" in data:
                tool_name = data.get("tool")
                params = data.get("parameters") or data.get("args") or {}
                exec_result = execute_tool_call(tool_name, params)
                return exec_result, raw_response
        except Exception:
            pass

    return None, raw_response


