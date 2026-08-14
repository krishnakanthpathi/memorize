import os
from config.settings import get_setting

SERVER_NAME = "Memorize Server"
SERVER_VERSION = "2.0.0"
DEFAULT_TRANSPORT = "stdio"
DEFAULT_PORT = int(os.getenv("BACKEND_PORT", os.getenv("PORT", "7777")))




# ==========================================
# 🧠 MCP Model Configuration & LLM Settings
# ==========================================
# Toggle whether MCP operations utilize LLM (smart merge, AI classifier) or fast deterministic offline mode
USE_LLM: bool = bool(get_setting("use_llm", False))

# Active Embedding Model for Vector Search (e.g. "all-MiniLM-L6-v2", "nomic-embed-text", "bge-m3")
EMBEDDING_MODEL: str = str(get_setting("embedding_model", "all-MiniLM-L6-v2"))

# Active Classification Model (e.g. "gpt-oss:120b-cloud", "gpt-4o-mini")
CLASSIFICATION_MODEL: str = str(get_setting("classification_model", "gpt-oss:120b-cloud"))

# Fallback Embedding Model
FALLBACK_MODEL: str = str(get_setting("fallback_model", "all-MiniLM-L6-v2"))

# Embedding & LLM Provider Defaults
EMBEDDING_PROVIDER: str = str(get_setting("embedding_provider", "local"))
LLM_PROVIDER: str = str(get_setting("llm_provider", "ollama"))

# Search top_k default
SEARCH_TOP_K: int = int(get_setting("search_top_k", 5))

