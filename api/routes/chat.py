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

    system_prompt = (
        "You are Memorize AI Companion — a helpful, highly knowledgeable personal friend and assistant. "
        "You have direct access to the user's stored personal, technical, and project memories. "
        "Use the retrieved memory context below to answer the user's questions accurately and concisely.\n\n"
        f"RETRIEVED MEMORY CONTEXT:\n{context_str}\n\n"
        "Guidelines: Be friendly, direct, clear, and professional. Reference memories naturally when applicable."
    )

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
