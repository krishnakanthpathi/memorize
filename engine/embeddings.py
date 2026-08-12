from typing import List
from langchain_core.embeddings import Embeddings

from config.constants import FALLBACK_EMBEDDING_MODEL
from vector.embedder import generate_embeddings, generate_single_embedding


class MemorizeEmbeddings(Embeddings):
    """
    LangChain compatible Embeddings wrapper integrating Memorize local HuggingFace / OpenAI / Ollama embedder.
    """

    def __init__(self, model_name: str = FALLBACK_EMBEDDING_MODEL):
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return generate_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return []
        return generate_single_embedding(text)
