import base64
import json
import os
import re
from typing import Any, Dict, Optional
import requests

from config.constants import (
    LLM_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_OCR_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from core.logger import logger


def clean_llm_markdown_output(output: str) -> str:
    """Strips outer markdown code fences from LLM responses if wrapped."""
    if not output:
        return ""
    cleaned = output.strip()
    cleaned = re.sub(r"^```(?:markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def generate_openai_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    json_mode: bool = False,
) -> str:
    """
    Generates text or JSON response using the OpenAI client API endpoint.
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

    kwargs: Dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
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
    json_mode: bool = False,
) -> str:
    """
    Generates text or JSON response using the Ollama REST API endpoint.
    """
    ollama_model = model or OLLAMA_MODEL or LLM_MODEL or "gpt-oss:120b-cloud"
    effective_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
    url = f"{effective_url}/api/generate"
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    payload: Dict[str, Any] = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"

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
    json_mode: bool = False,
) -> str:
    """
    Generates text response with provider routing and automatic fallback between OpenAI and Ollama.
    """
    prov_lower = (provider or LLM_PROVIDER or "ollama").strip().lower()

    if prov_lower == "openai":
        return generate_openai_response(prompt, system_prompt, model, temperature, json_mode=json_mode)
    elif prov_lower == "ollama":
        return generate_ollama_response(prompt, system_prompt, model, temperature, base_url=base_url, json_mode=json_mode)

    # Automatic fallback: Try OpenAI first if configured, then Ollama
    if OPENAI_API_KEY and OPENAI_BASE_URL:
        try:
            return generate_openai_response(prompt, system_prompt, model, temperature, json_mode=json_mode)
        except Exception as e:
            logger.warning(f"OpenAI LLM request failed: {e}. Falling back to Ollama.")

    try:
        return generate_ollama_response(prompt, system_prompt, model, temperature, base_url=base_url, json_mode=json_mode)
    except Exception as e:
        logger.error(f"Failed to generate LLM response from Ollama: {e}")
        raise RuntimeError(f"Failed to generate response from configured LLM providers. Details: {e}")


def generate_json_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates structured JSON output from LLM, parsing response and stripping code fences.
    """
    raw = generate_llm_response(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        provider=provider,
        base_url=base_url,
        json_mode=True,
    )
    cleaned = raw.strip()
    # Strip json markdown code fence if present
    match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1)
    else:
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    return json.loads(cleaned.strip())


def test_llm_connection(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tests connectivity to the specified LLM provider with a fast lightweight ping prompt.
    """
    try:
        reply = generate_llm_response(
            prompt="Respond in 5 words or fewer confirming you are online.",
            system_prompt="You are a health check assistant.",
            model=model,
            temperature=0.1,
            provider=provider,
            base_url=base_url,
        )
        return {
            "status": "success",
            "provider": provider or LLM_PROVIDER or "ollama",
            "model": model or LLM_MODEL or "default",
            "reply": reply,
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": provider or LLM_PROVIDER or "ollama",
            "model": model or LLM_MODEL or "default",
            "error": str(e),
        }


DEFAULT_OCR_PROMPT = """Text Recognition:
Extract all visible text, numbers, dates, addresses, tables, formulas, and labels from this image accurately in clean markdown format. Preserve the structural layout and details accurately."""


def extract_text_with_ollama_ocr(
    image_bytes: bytes,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 120,
) -> str:
    """
    Extracts text, formulas, and structured content from an uncompressed image using local Ollama GLM-OCR model.
    """
    if not image_bytes:
        return ""

    ocr_model = model or OLLAMA_OCR_MODEL or "glm-ocr"
    effective_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
    url = f"{effective_url}/api/generate"
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    ocr_prompt = prompt or DEFAULT_OCR_PROMPT

    payload = {
        "model": ocr_model,
        "prompt": ocr_prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "num_ctx": 16384,
            "temperature": 0.1,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        if resp.status_code == 200:
            result = resp.json().get("response", "")
            return clean_llm_markdown_output(result)
        else:
            logger.warning(
                f"Ollama OCR request to '{ocr_model}' failed with status {resp.status_code}: {resp.text}"
            )
            raise RuntimeError(f"Ollama OCR failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Error during Ollama OCR extraction with model '{ocr_model}': {e}")
        raise



