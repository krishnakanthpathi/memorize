from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, MODEL_CHUNK_CONFIGS


class MemorizeTextSplitter:
    """
    Model-aware text chunking splitter leveraging LangChain RecursiveCharacterTextSplitter.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        config = MODEL_CHUNK_CONFIGS.get(
            model_name,
            {"chunk_size": DEFAULT_CHUNK_SIZE, "overlap": DEFAULT_CHUNK_OVERLAP},
        )
        # Approximate characters per token (~4 chars per token)
        chunk_size_chars = config["chunk_size"] * 4
        chunk_overlap_chars = config["overlap"] * 4

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size_chars,
            chunk_overlap=chunk_overlap_chars,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)
