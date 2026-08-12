from core.memory_service import execute_upsert_memory
from graph.state import GraphRAGState
from core.metrics import metrics_collector
from core.logger import logger


def memory_action_node(state: GraphRAGState) -> GraphRAGState:
    """
    Executes memory mutations (insert, update, delete) when user intent requires storing or removing memories.
    """
    with metrics_collector.time_node("memory_action"):
        intent = state.get("intent", "store")
        query = state.get("query", "")
        category = state.get("category", "personal")
        title = state.get("title") or (query[:30] if query else "Untitled Memory")

        if intent in ("store", "update"):
            res = execute_upsert_memory(
                title=title,
                content=query,
                action="auto",
                category=category,
            )
            state["action_result"] = res
            logger.info(f"Memory action '{intent}' result: {res.get('status')} (ID: {res.get('memory_id')})")
        elif intent == "delete":
            res = execute_upsert_memory(
                title=title,
                content="",
                action="delete",
                category=category,
            )
            state["action_result"] = res
            logger.info(f"Memory action delete result: {res.get('status')}")

        return state
