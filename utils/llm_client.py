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


def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Generates text response using OpenAI/Bedrock Mantle API or Ollama endpoints.
    Provides robust fallback handling.
    """
    chosen_model = model or DEFAULT_LLM_MODEL

    # Try OpenAI API Endpoint first if API Key is configured
    if OPENAI_API_KEY:
        try:
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
        except Exception as e:
            logger.warning(f"OpenAI LLM request failed with model '{chosen_model}': {e}. Falling back to Ollama.")

    # Fallback to Ollama endpoint
    try:
        ollama_model = OLLAMA_CLASSIFICATION_MODEL or "gpt-oss:120b-cloud"
        url = f"{OLLAMA_BASE_URL}/api/generate"
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
            return result.strip()
        else:
            logger.error(f"Ollama request failed with status code {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to generate LLM response from Ollama: {e}")

    raise RuntimeError("Failed to generate response from all configured LLM providers.")
