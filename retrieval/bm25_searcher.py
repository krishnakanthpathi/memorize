from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

from storage.db_manager import get_all_memories
from core.logger import logger


class BM25Searcher:
    """
    BM25 keyword searcher leveraging LangChain BM25Retriever.
    Initializes from stored Markdown memory documents in SQLite.
    """

    def __init__(self, category_filter: Optional[str] = None):
        self.category_filter = category_filter
        self.retriever = self._build_retriever()

    def _build_retriever(self) -> Optional[BM25Retriever]:
        memories = get_all_memories(category_filter=self.category_filter)
        if not memories:
            logger.info("No memories found to initialize BM25Retriever.")
            return None

        documents = []
        for mem in memories:
            text = f"Title: {mem.get('title', '')}\nCategory: {mem.get('category', '')}\nTags: {', '.join(mem.get('tags', []))}\nContent: {mem.get('content', '')}"
            doc = Document(
                page_content=text,
                metadata={
                    "memory_id": mem.get("id"),
                    "title": mem.get("title"),
                    "category": mem.get("category"),
                    "tags": mem.get("tags", []),
                    "file_path": mem.get("file_path"),
                },
            )
            documents.append(doc)

        if not documents:
            return None

        try:
            retriever = BM25Retriever.from_documents(documents)
            retriever.k = 5
            return retriever
        except Exception as e:
            logger.error(f"Error building BM25Retriever: {e}")
            return None

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        if not self.retriever:
            return []
        self.retriever.k = top_k
        try:
            return self.retriever.invoke(query)
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return []
