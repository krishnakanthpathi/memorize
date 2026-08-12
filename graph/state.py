from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage


class GraphRAGState(TypedDict, total=False):
    """
    State definition for Memorize LangGraph GraphRAG workflow.
    """

    messages: List[BaseMessage]
    query: str
    intent: str  # "retrieve" | "store" | "update" | "delete" | "chat"
    category: str
    title: Optional[str]
    entities: List[str]
    triples: List[List[str]]
    documents: List[Dict[str, Any]]
    action_result: Optional[Dict[str, Any]]
    generation: str
    is_offline_mode: bool
    metrics: Dict[str, Any]
