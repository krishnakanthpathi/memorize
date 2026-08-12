import json
from typing import Dict, Any

from classification.classifier import rule_based_classify
from engine.llm_factory import LLMFactory
from engine.prompts import INTENT_CLASSIFICATION_PROMPT
from graph.state import GraphRAGState
from core.metrics import metrics_collector
from core.logger import logger


def intent_classifier_node(state: GraphRAGState) -> GraphRAGState:
    """
    Classifies the user's input into 'retrieve', 'store', 'update', 'delete', or 'chat'.
    Uses ChatOpenAI / ChatOllama if available, or fast rule-based fallback if offline.
    """
    with metrics_collector.time_node("intent_classifier"):
        query = state.get("query", "")
        if not query:
            state["intent"] = "chat"
            state["category"] = "personal"
            return state

        # Check for explicit store/update/delete phrases offline or online
        query_lower = query.lower()
        if any(w in query_lower for w in ["remember", "store", "save", "take note", "add memory", "create memory", "create a memory", "new memory", "write memory", "record"]):
            state["intent"] = "store"
            cat, _ = rule_based_classify(query)
            state["category"] = cat
            return state
        elif any(w in query_lower for w in ["delete memory", "forget", "remove memory"]):
            state["intent"] = "delete"
            cat, _ = rule_based_classify(query)
            state["category"] = cat
            return state
        elif any(w in query_lower for w in ["update memory", "edit memory", "modify memory"]):
            state["intent"] = "update"
            cat, _ = rule_based_classify(query)
            state["category"] = cat
            return state

        # Check if LLM is available for structured zero-shot classification
        if LLMFactory.is_llm_available():
            try:
                llm = LLMFactory.get_llm(temperature=0.0)
                chain = INTENT_CLASSIFICATION_PROMPT | llm
                res = chain.invoke({"query": query})
                content = res.content.strip() if hasattr(res, "content") else str(res).strip()
                
                # Parse JSON output
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                data = json.loads(content)

                intent = data.get("intent", "retrieve").lower()
                category = data.get("category", "personal").lower()
                title = data.get("title")

                state["intent"] = intent if intent in ("store", "update", "delete", "retrieve", "chat") else "retrieve"
                state["category"] = category
                if title:
                    state["title"] = title
                state["is_offline_mode"] = False
                return state
            except Exception as e:
                logger.warning(f"LLM intent classification failed ({e}), using offline rule classifier.")

        # Offline fallback rule classification
        cat, _ = rule_based_classify(query)
        if any(w in query_lower for w in ["create", "store", "save", "add", "remember", "write", "record"]):
            state["intent"] = "store"
        elif any(w in query_lower for w in ["delete", "remove", "forget"]):
            state["intent"] = "delete"
        elif any(w in query_lower for w in ["update", "edit", "modify"]):
            state["intent"] = "update"
        else:
            state["intent"] = "retrieve"
        state["category"] = cat
        state["is_offline_mode"] = True
        return state
