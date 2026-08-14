import os
from pathlib import Path
from dotenv import load_dotenv

# Base Repository Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Server Ports
PORT = int(os.getenv("PORT", os.getenv("API_PORT", "7777")))
API_PORT = PORT
MCP_PORT = int(os.getenv("MCP_PORT", str(PORT)))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", os.getenv("VITE_PORT", "8888")))

# Storage Data Directory

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "memorize.db"
CHROMA_DIR = DATA_DIR / "chroma_db"
MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MEMORIES_DIR = DATA_DIR / "memories"
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

BACKUP_DIR = DATA_DIR / "backups"
BACKUP_MEMORIES_DIR = BACKUP_DIR / "memories"
BACKUP_MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CATEGORIES = [
    "achievements",
    "development",
    "education",
    "finance",
    "gaming",
    "integration",
    "job",
    "media",
    "others",
    "personal",
    "projects",
]

# RAG & Embedding Settings
DEFAULT_CHUNK_SIZE = 500  # tokens
DEFAULT_CHUNK_OVERLAP = 50  # tokens
# Embedding Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", os.getenv("ACTIVE_EMBEDDING_MODEL", os.getenv("OLLAMA_EMBEDDING_MODEL", "all-MiniLM-L6-v2")))
FALLBACK_EMBEDDING_MODEL = os.getenv("FALLBACK_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Backward-compatible aliases
ACTIVE_EMBEDDING_MODEL = EMBEDDING_MODEL
OLLAMA_EMBEDDING_MODEL = EMBEDDING_MODEL
EMBEDDING_MODEL_NAME = EMBEDDING_MODEL

# LLM Generation & Chat Engine Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("DEFAULT_LLM_MODEL", "gpt-oss:120b-cloud"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("OLLAMA_CLASSIFICATION_MODEL", "gpt-oss:120b-cloud"))

# Provider endpoints
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://bedrock-mantle.ap-southeast-2.api.aws/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# Remote ChromaDB Container Settings
CHROMA_MODE = os.getenv("CHROMA_MODE", "local").lower()
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Hybrid Search Relevance Weights
WEIGHT_VECTOR_SIMILARITY = 0.50
WEIGHT_TAG_MATCH = 0.30
WEIGHT_CATEGORY_MATCH = 0.20
RELEVANCE_SCORE_THRESHOLD = 0.15


# Model-Specific Chunk Sizes & Overlaps
MODEL_CHUNK_CONFIGS = {
    # OpenAI Models
    "text-embedding-3-small": {"chunk_size": 500, "overlap": 50},
    "text-embedding-3-large": {"chunk_size": 800, "overlap": 80},
    
    # Ollama Models
    "nomic-embed-text": {"chunk_size": 500, "overlap": 50},
    "nomic-embed-text:latest": {"chunk_size": 500, "overlap": 50},
    "bge-m3": {"chunk_size": 512, "overlap": 50},
    "bge-m3:latest": {"chunk_size": 512, "overlap": 50},
    "mxbai-embed-large": {"chunk_size": 512, "overlap": 50},
    
    # Local HuggingFace Models
    "all-MiniLM-L6-v2": {"chunk_size": 256, "overlap": 30},
    "bge-small-en-v1.5": {"chunk_size": 512, "overlap": 50},
    
    # Gemini / Grok / xAI
    "embedding-001": {"chunk_size": 500, "overlap": 50},
}


CHROMA_CLIENT = None
LOCAL_MODEL_CACHE = {}

# LLM Integration Toggle (True: AI smart merge & classification, False: offline rule-based)
USE_LLM = os.getenv("USE_LLM", "false").lower() in ("true", "1", "yes")

# Ollama Classification Model & Classifier Mode ("rules" fast local default, "llm", or "auto")
CLASSIFIER_MODE = os.getenv("CLASSIFIER_MODE", "rules").lower()
OLLAMA_CLASSIFICATION_MODEL = os.getenv("OLLAMA_CLASSIFICATION_MODEL", "gpt-oss:120b-cloud")