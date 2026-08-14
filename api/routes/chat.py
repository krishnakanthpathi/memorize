from fastapi import APIRouter

from api.schemas import ChatRequest
from search.relevance_scorer import search_hybrid_relevance as hybrid_search_memories
from utils.llm_client import generate_llm_response

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

    reply = generate_llm_response(
        prompt=req.message,
        system_prompt=system_prompt,
        model=req.model,
        temperature=0.3,
        provider=req.provider,
    )

    return {
        "status": "success",
        "message": req.message,
        "reply": reply,
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
