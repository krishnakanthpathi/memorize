import json
import re
from typing import List

from engine.llm_factory import LLMFactory
from engine.prompts import ENTITY_EXTRACTION_PROMPT
from graph.state import GraphRAGState
from core.metrics import metrics_collector
from core.logger import logger


def graph_rag_node(state: GraphRAGState) -> GraphRAGState:
    """
    Extracts key entity relationships from query and retrieved documents
    for GraphRAG multi-hop concept linking.
    """
    with metrics_collector.time_node("graph_rag"):
        query = state.get("query", "")
        documents = state.get("documents", [])

        # 1. Simple regex offline entity extraction fallback
        words = set(re.findall(r'\b[A-Z][a-z0-9]+\b|\b[a-z]{4,}\b', query))
        extracted_entities = list(words)[:5]
        extracted_triples = []

        # 2. LLM zero-shot entity & triple extraction if available
        if LLMFactory.is_llm_available() and query:
            try:
                llm = LLMFactory.get_llm(temperature=0.0)
                chain = ENTITY_EXTRACTION_PROMPT | llm
                res = chain.invoke({"text": query})
                content = res.content.strip() if hasattr(res, "content") else str(res).strip()

                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()

                data = json.loads(content)
                if isinstance(data, dict):
                    if data.get("entities"):
                        extracted_entities = data["entities"]
                    if data.get("triples"):
                        extracted_triples = data["triples"]
            except Exception as e:
                logger.warning(f"GraphRAG entity extraction error ({e}), using regex fallback.")

        state["entities"] = extracted_entities
        state["triples"] = extracted_triples
        return state
