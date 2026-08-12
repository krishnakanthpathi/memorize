import time
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from graph.nodes.answer_synthesizer import answer_synthesizer_node
from graph.nodes.graph_rag_node import graph_rag_node
from graph.nodes.intent_classifier import intent_classifier_node
from graph.nodes.memory_action_node import memory_action_node
from graph.nodes.retriever_node import retriever_node
from graph.state import GraphRAGState
from core.metrics import metrics_collector
from core.logger import logger


def route_by_intent(state: GraphRAGState) -> str:
    """Conditional edge router based on classified intent."""
    intent = state.get("intent", "retrieve")
    if intent in ("store", "update", "delete"):
        return "memory_action"
    return "retriever"


def build_memorize_graph() -> StateGraph:
    """Constructs and compiles the StateGraph for Memorize GraphRAG workflow."""
    workflow = StateGraph(GraphRAGState)

    # Add Nodes
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("graph_rag", graph_rag_node)
    workflow.add_node("memory_action", memory_action_node)
    workflow.add_node("answer_synthesizer", answer_synthesizer_node)

    # Entry Point
    workflow.set_entry_point("intent_classifier")

    # Conditional Routing
    workflow.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "memory_action": "memory_action",
            "retriever": "retriever",
        },
    )

    # Retrieval Flow
    workflow.add_edge("retriever", "graph_rag")
    workflow.add_edge("graph_rag", "answer_synthesizer")

    # Action Flow
    workflow.add_edge("memory_action", "answer_synthesizer")

    # End Edge
    workflow.add_edge("answer_synthesizer", END)

    return workflow.compile()


# Global compiled graph instance
compiled_graph = build_memorize_graph()


class MemorizeGraphRAGAgent:
    """
    High-level entrypoint for executing the Memorize GraphRAG LangGraph StateMachine.
    """

    def __init__(self):
        self.graph = compiled_graph

    def run(self, query: str, category: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        initial_state: GraphRAGState = {
            "query": query,
            "category": category or "personal",
            "messages": [],
            "documents": [],
            "entities": [],
            "triples": [],
            "action_result": None,
            "generation": "",
            "is_offline_mode": False,
            "metrics": {},
        }

        try:
            final_state = self.graph.invoke(initial_state)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            is_offline = final_state.get("is_offline_mode", False)

            metrics_collector.record_query(
                latency_ms=elapsed_ms,
                success=True,
                offline=is_offline,
            )

            return {
                "status": "success",
                "query": query,
                "intent": final_state.get("intent"),
                "category": final_state.get("category"),
                "reply": final_state.get("generation"),
                "documents_count": len(final_state.get("documents", [])),
                "entities": final_state.get("entities", []),
                "is_offline_mode": is_offline,
                "latency_ms": elapsed_ms,
                "metrics_summary": metrics_collector.get_summary(),
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            metrics_collector.record_query(latency_ms=elapsed_ms, success=False)
            logger.error(f"Error in MemorizeGraphRAGAgent: {e}")
            return {
                "status": "error",
                "query": query,
                "message": str(e),
                "latency_ms": elapsed_ms,
            }
