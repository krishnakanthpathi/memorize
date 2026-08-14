from fastapi import APIRouter

from api.schemas import ChatRequest
from search.relevance_scorer import search_hybrid_relevance as hybrid_search_memories
from utils.llm_client import generate_llm_response, parse_and_execute_tool

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat_companion_endpoint(req: ChatRequest):
    # Perform hybrid vector search for memory context retrieval
    search_results = hybrid_search_memories(query=req.message, top_k=4)

    context_snippets = []
    for idx, item in enumerate(search_results, start=1):
        context_snippets.append(
            f"[{idx}] Title: {item.get('title')}\nCategory: {item.get('category')}\nExcerpt: {item.get('snippet') or item.get('content', '')}"
        )

    context_str = "\n\n".join(context_snippets) if context_snippets else "No relevant memories found in database."

    from config.prompts import get_prompt

    system_prompt = get_prompt("companion", context_str=context_str)

    raw_reply = generate_llm_response(
        prompt=req.message,
        system_prompt=system_prompt,
        model=req.model,
        temperature=0.3,
        provider=req.provider,
    )

    # Parse and execute structured tool calls (create_memory, search_memories, read_memory, delete_memory, clear_all_memories)
    tool_res, _ = parse_and_execute_tool(raw_reply)
    reply = raw_reply

    if tool_res:
        t_name = tool_res.get("tool")
        res_data = tool_res.get("result", {})
        if t_name in ("create_memory", "store_memory", "upsert_memory"):
            title = res_data.get("title") if isinstance(res_data, dict) else "Note"
            cat = res_data.get("category", "personal") if isinstance(res_data, dict) else "personal"
            mem_id = res_data.get("memory_id") if isinstance(res_data, dict) else ""
            reply = f"Memory saved successfully!\n\n• **Title:** {title}\n• **Category:** `{cat}`\n• **ID:** `{mem_id}`"
        elif t_name in ("search_memories", "search"):
            res_list = res_data if isinstance(res_data, list) else []
            titles = [f"• {m.get('title')} ({m.get('category', 'general')})" for m in res_list]
            reply = f"Found {len(res_list)} matching memories:\n" + "\n".join(titles) if titles else "No matching memories found."
        elif t_name in ("read_memory", "get_memory", "read"):
            if isinstance(res_data, dict) and res_data.get("status") != "error":
                reply = f"### {res_data.get('title')}\n\n{res_data.get('content', '')}"
            else:
                msg = res_data.get("message") if isinstance(res_data, dict) else "Not found"
                reply = f"Could not find memory: {msg}."
        elif t_name in ("delete_memory", "delete"):
            reply = f"Memory deleted successfully."
        elif t_name in ("clear_all_memories", "clear_all", "reset_memories", "purge_all"):
            reply = "All stored memories, database records, and vector embeddings have been cleared."
        elif t_name in ("list_memories", "list"):
            res_list = res_data if isinstance(res_data, list) else []
            titles = [f"• {m.get('title')}" for m in res_list]
            reply = f"Stored memories ({len(titles)}):\n" + "\n".join(titles) if titles else "No memories found."

    return {
        "status": "success",
        "message": req.message,
        "reply": reply,
        "tool_executed": tool_res,
        "memories_used": [
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "category": m.get("category"),
                "score": m.get("final_score"),
            }
            for m in search_results
        ],
    }
