import json
import os
from typing import Optional
from dotenv import load_dotenv
import requests

# Ensure environment variables are loaded
load_dotenv()

from config.constants import (
    OLLAMA_BASE_URL,
    OLLAMA_CLASSIFICATION_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from core.logger import logger

_ACTIVE_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud"))



def get_active_model() -> str:
    """Returns the currently active LLM model."""
    global _ACTIVE_MODEL
    return _ACTIVE_MODEL


def set_active_model(model_name: str) -> str:
    """Sets the active LLM model and returns it."""
    global _ACTIVE_MODEL
    if model_name and isinstance(model_name, str):
        _ACTIVE_MODEL = model_name.strip()
        logger.info(f"Active LLM model set to '{_ACTIVE_MODEL}'")
    return _ACTIVE_MODEL


def generate_openai_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Generates text response using OpenAI/Bedrock Mantle API endpoint.
    """
    chosen_model = model or get_active_model()
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured.")

    import openai
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

    raise RuntimeError(f"Empty response received from OpenAI with model '{chosen_model}'.")


def generate_ollama_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Generates text response using Ollama endpoint.
    """
    chosen_model = model or OLLAMA_CLASSIFICATION_MODEL or "gpt-oss:120b-cloud"
    url = f"{OLLAMA_BASE_URL}/api/generate"
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    payload = {
        "model": chosen_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
        result = resp.json().get("response", "")
        return result.strip()
    else:
        raise RuntimeError(
            f"Ollama request failed with status code {resp.status_code}: {resp.text}"
        )


def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Generates text response using OpenAI API or Ollama with fallback support.
    Accepts optional provider parameter ('openai' or 'ollama').
    """
    target_model = model or get_active_model()
    target_provider = (provider or "").strip().lower()

    if target_provider == "ollama":
        return generate_ollama_response(
            prompt=prompt,
            system_prompt=system_prompt,
            model=target_model,
            temperature=temperature,
        )
    elif target_provider == "openai":
        return generate_openai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            model=target_model,
            temperature=temperature,
        )

    # Auto mode with fallback
    if OPENAI_API_KEY:
        try:
            return generate_openai_response(
                prompt=prompt,
                system_prompt=system_prompt,
                model=target_model,
                temperature=temperature,
            )
        except Exception as e:
            logger.warning(
                f"OpenAI LLM request failed with model '{target_model}': {e}. Falling back to Ollama."
            )

    try:
        return generate_ollama_response(
            prompt=prompt,
            system_prompt=system_prompt,
            model=target_model,
            temperature=temperature,
        )
    except Exception as e:
        logger.error(f"Ollama fallback also failed: {e}")

    raise RuntimeError("Failed to generate response from all configured LLM providers.")

