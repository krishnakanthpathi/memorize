import os
from typing import Any, List, Optional
import requests

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from config.settings import settings
from core.logger import logger


class OfflineFallbackLLM(BaseChatModel):
    """
    Fallback ChatModel used when no external or local LLMs are available.
    Ensures complete Zero-LLM system execution without raising exceptions.
    """

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        content = "System running in Zero-LLM Offline Mode. No active LLM provider detected."
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "offline_fallback"


class LLMFactory:
    """
    Factory class providing instantiated LangChain Chat Models based on
    system environment settings (OpenAI, Anthropic, Ollama, or Offline Fallback).
    """

    @staticmethod
    def get_llm(
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
    ) -> BaseChatModel:
        chosen_provider = (provider or settings.LLM_PROVIDER).lower()

        def _is_valid_key(key: Optional[str]) -> bool:
            return bool(key and not key.startswith("your_") and "placeholder" not in key.lower() and key != "your_openai_api_key_here")

        # 1. Try OpenAI if explicitly chosen or in auto mode with API Key present
        if chosen_provider in ("openai", "auto") and _is_valid_key(settings.OPENAI_API_KEY):
            try:
                from langchain_openai import ChatOpenAI
                model = model_name or settings.DEFAULT_LLM_MODEL
                logger.info(f"Instantiating ChatOpenAI model: {model}")
                return ChatOpenAI(
                    model=model,
                    openai_api_key=settings.OPENAI_API_KEY,
                    openai_api_base=settings.OPENAI_BASE_URL,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize ChatOpenAI: {e}")

        # 2. Try Anthropic if requested and key is available
        if chosen_provider in ("anthropic", "auto") and _is_valid_key(settings.ANTHROPIC_API_KEY):
            try:
                from langchain_anthropic import ChatAnthropic
                model = model_name or "claude-3-5-sonnet-20240620"
                logger.info(f"Instantiating ChatAnthropic model: {model}")
                return ChatAnthropic(
                    model=model,
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize ChatAnthropic: {e}")

        # 3. Try Ollama if requested or auto fallback
        if chosen_provider in ("ollama", "auto"):
            try:
                # Check if Ollama endpoint responds
                resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
                if resp.status_code == 200:
                    from langchain_ollama import ChatOllama
                    model = model_name or settings.OLLAMA_MODEL
                    logger.info(f"Instantiating ChatOllama model: {model}")
                    return ChatOllama(
                        base_url=settings.OLLAMA_BASE_URL,
                        model=model,
                        temperature=temperature,
                    )
            except Exception as e:
                logger.warning(f"Ollama server unavailable at {settings.OLLAMA_BASE_URL}: {e}")

        # 4. Fallback to Offline Mode
        logger.info("Operating in Zero-LLM Offline Mode.")
        return OfflineFallbackLLM()

    @staticmethod
    def is_llm_available() -> bool:
        """Check if any real LLM provider is available."""
        llm = LLMFactory.get_llm()
        return not isinstance(llm, OfflineFallbackLLM)
