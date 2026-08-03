import os
from pathlib import Path

# Base Repository Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Storage Data Directory
DATA_DIR = BASE_DIR / "data"
INDEX_PATH = DATA_DIR / "index.json"
CHROMA_DIR = DATA_DIR / "chroma_db"
MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MEMORIES_DIR = DATA_DIR / "memories"
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CATEGORIES = ["personal", "job", "study", "routine", "media"]

MEDIA_STORE_DIR = DATA_DIR / "media_store"
MEDIA_STORE_SUBDIRS = {
    "images": MEDIA_STORE_DIR / "images",
    "videos": MEDIA_STORE_DIR / "videos",
    "audio": MEDIA_STORE_DIR / "audio",
    "documents": MEDIA_STORE_DIR / "documents",
}

# RAG & Embedding Settings
DEFAULT_CHUNK_SIZE = 500  # tokens
DEFAULT_CHUNK_OVERLAP = 50  # tokens
FALLBACK_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local HuggingFace model

# OpenAI primary model
OPENAI_BASE_URL = "https://bedrock-mantle.ap-southeast-2.api.aws/v1"
EMBEDDING_MODEL_NAME = "titan-embed-text-v2"

# Ollama embeddings model
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_OLLAMA_BASE_URL = "http://100.105.203.102:11434"

# Remote ChromaDB Container Settings
CHROMA_HOST = "100.105.203.102"
CHROMA_PORT = 8000

# Hybrid Search Relevance Weights
WEIGHT_VECTOR_SIMILARITY = 0.50
WEIGHT_TAG_MATCH = 0.30
WEIGHT_CATEGORY_MATCH = 0.20
RELEVANCE_SCORE_THRESHOLD = 0.50


# Model-Specific Chunk Sizes & Overlaps
MODEL_CHUNK_CONFIGS = {
    # OpenAI Models
    "text-embedding-3-small": {"chunk_size": 500, "overlap": 50},
    "text-embedding-3-large": {"chunk_size": 800, "overlap": 80},
    
    # Ollama Models
    "nomic-embed-text": {"chunk_size": 500, "overlap": 50},
    "mxbai-embed-large": {"chunk_size": 512, "overlap": 50},
    
    # Local HuggingFace Models
    "all-MiniLM-L6-v2": {"chunk_size": 256, "overlap": 30},
    "bge-small-en-v1.5": {"chunk_size": 512, "overlap": 50},
    
    # Gemini / Grok / xAI
    "embedding-001": {"chunk_size": 500, "overlap": 50},
}


CHROMA_CLIENT = None
LOCAL_MODEL_CACHE = {}

# Ollama Classification Model
OLLAMA_CLASSIFICATION_MODEL="gpt-oss:120b-cloud"