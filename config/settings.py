import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from config.constants import BASE_DIR

load_dotenv(BASE_DIR / ".env")


class AppSettings:
    """Central configuration class for Memorize application settings."""

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").lower()  # "ollama", "openai", "anthropic", "auto", "none"
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-oss:120b-cloud")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", os.getenv("OLLAMA_CLASSIFICATION_MODEL", "gpt-oss:120b-cloud"))

    # Retrieval & RAG
    USE_CONTEXTUAL_RETRIEVAL: bool = os.getenv("USE_CONTEXTUAL_RETRIEVAL", "true").lower() in ("true", "1", "yes")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "0.5"))
    VECTOR_WEIGHT: float = float(os.getenv("VECTOR_WEIGHT", "0.5"))

    # Observability & Logging
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text").lower()  # "text" or "json"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def reload(cls):
        """Reload environment variables."""
        load_dotenv(BASE_DIR / ".env", override=True)
        cls.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
        cls.DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-oss:120b-cloud")
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        cls.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        cls.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        cls.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        cls.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("OLLAMA_CLASSIFICATION_MODEL", "gpt-oss:120b-cloud"))
        cls.USE_CONTEXTUAL_RETRIEVAL = os.getenv("USE_CONTEXTUAL_RETRIEVAL", "true").lower() in ("true", "1", "yes")


settings = AppSettings()
