from engine.llm_factory import LLMFactory
from engine.prompts import ANSWER_SYNTHESIS_PROMPT
from graph.state import GraphRAGState
from core.metrics import metrics_collector
from core.logger import logger


def answer_synthesizer_node(state: GraphRAGState) -> GraphRAGState:
    """
    Synthesizes the final answer using LLM response synthesis or structured offline markdown output.
    """
    with metrics_collector.time_node("answer_synthesizer"):
        query = state.get("query", "")
        documents = state.get("documents", [])
        action_result = state.get("action_result")
        intent = state.get("intent", "retrieve")

        # 1. Handle memory mutation action responses
        if action_result:
            status = action_result.get("status")
            action = action_result.get("action")
            mem_id = action_result.get("memory_id")
            title = action_result.get("title")
            if status == "success":
                state["generation"] = f"✅ Memory successfully updated ({action}): **{title}** (ID: `{mem_id}`)."
            else:
                state["generation"] = f"❌ Failed memory action: {action_result.get('message', 'Unknown error')}."
            return state

        # Format context snippets from retrieved documents
        context_snippets = []
        for idx, doc in enumerate(documents, start=1):
            if isinstance(doc, dict):
                t = doc.get("title", "Untitled")
                c = doc.get("category", "personal")
                snippet = doc.get("snippet") or doc.get("content", "")
            else:
                t = doc.metadata.get("title", "Untitled") if hasattr(doc, "metadata") else "Untitled"
                c = doc.metadata.get("category", "personal") if hasattr(doc, "metadata") else "personal"
                snippet = doc.page_content if hasattr(doc, "page_content") else str(doc)
            context_snippets.append(f"[{idx}] Title: {t} (Category: {c})\nExcerpt: {snippet}")

        context_str = "\n\n".join(context_snippets) if context_snippets else "No relevant memories found."

        # 2. LLM response synthesis if online
        if LLMFactory.is_llm_available():
            try:
                llm = LLMFactory.get_llm(temperature=0.3)
                chain = ANSWER_SYNTHESIS_PROMPT | llm
                res = chain.invoke({"context": context_str, "query": query})
                reply = res.content.strip() if hasattr(res, "content") else str(res).strip()

                # Track token usage if available
                if hasattr(res, "response_metadata"):
                    usage = res.response_metadata.get("token_usage", {})
                    metrics_collector.record_tokens(
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                    )

                state["generation"] = reply
                return state
            except Exception as e:
                logger.warning(f"LLM answer synthesis error ({e}), falling back to offline structured response.")

        # 3. Offline Zero-LLM Structured Markdown Response
        if not documents:
            state["generation"] = f"🔍 No memories found for query: *'{query}'*."
            return state

        lines = [f"### 🧠 Retrieved Memories for: *\"{query}\"*\n"]
        for idx, doc in enumerate(documents, start=1):
            if isinstance(doc, dict):
                t = doc.get("title", "Untitled")
                cat = doc.get("category", "personal")
                snip = doc.get("snippet") or doc.get("content", "")
                m_id = doc.get("id") or doc.get("memory_id", "")
            else:
                t = doc.metadata.get("title", "Untitled") if hasattr(doc, "metadata") else "Untitled"
                cat = doc.metadata.get("category", "personal") if hasattr(doc, "metadata") else "personal"
                snip = doc.page_content if hasattr(doc, "page_content") else str(doc)
                m_id = doc.metadata.get("memory_id", "") if hasattr(doc, "metadata") else ""

            lines.append(f"**{idx}. {t}** (`{cat}`) — ID: `{m_id}`")
            lines.append(f"> {snip.strip()}\n")

        lines.append("*Note: Output generated in Zero-LLM Offline Mode.*")
        state["generation"] = "\n".join(lines)
        return state
