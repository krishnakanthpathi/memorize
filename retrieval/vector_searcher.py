from typing import List, Optional
from langchain_core.documents import Document

from search.relevance_scorer import search_vector_similarity
from core.logger import logger


class VectorSearcher:
    """
    Vector searcher wrapping ChromaDB embeddings search into LangChain Document format.
    """

    def __init__(self, category_filter: Optional[str] = None):
        self.category_filter = category_filter

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        try:
            results = search_vector_similarity(
                query=query,
                category_filter=self.category_filter,
                top_k=top_k,
            )
            if not isinstance(results, list):
                return []

            documents = []
            for item in results:
                content = item.get("content") or item.get("text", "")
                doc = Document(
                    page_content=content,
                    metadata={
                        "memory_id": item.get("memory_id") or item.get("id"),
                        "title": item.get("title"),
                        "category": item.get("category"),
                        "similarity_score": item.get("similarity_score", 0.0),
                    },
                )
                documents.append(doc)

            return documents
        except Exception as e:
            logger.error(f"VectorSearcher error: {e}")
            return []
