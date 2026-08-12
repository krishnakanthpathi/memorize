from typing import List, Optional

from config.settings import settings
from engine.llm_factory import LLMFactory
from engine.prompts import CONTEXTUAL_RAG_PROMPT
from core.logger import logger


class ContextualChunker:
    """
    Adds LLM-generated document-level context summaries to document chunks
    to enhance RAG retrieval accuracy when enabled via USE_CONTEXTUAL_RETRIEVAL env toggle.
    Bypasses gracefully when operating in Zero-LLM offline mode.
    """

    def __init__(self):
        self.enabled = settings.USE_CONTEXTUAL_RETRIEVAL

    def enrich_chunks(self, full_document: str, chunks: List[str]) -> List[str]:
        """
        Enriches a list of text chunks with context summaries if enabled and LLM is available.
        """
        if not self.enabled or not chunks:
            return chunks

        if not LLMFactory.is_llm_available():
            logger.info("Contextual Retrieval enabled but no LLM available. Bypassing context generation.")
            return chunks

        try:
            llm = LLMFactory.get_llm(temperature=0.1)
            enriched = []
            chain = CONTEXTUAL_RAG_PROMPT | llm

            for chunk in chunks:
                try:
                    res = chain.invoke({
                        "full_document": full_document[:1500],
                        "chunk_text": chunk,
                    })
                    context_summary = res.content.strip() if hasattr(res, "content") else str(res).strip()
                    contextualized_chunk = f"Context: {context_summary}\n\nChunk: {chunk}"
                    enriched.append(contextualized_chunk)
                except Exception as e:
                    logger.warning(f"Error enriching chunk: {e}. Using raw chunk.")
                    enriched.append(chunk)

            return enriched
        except Exception as e:
            logger.error(f"ContextualChunker error: {e}")
            return chunks
