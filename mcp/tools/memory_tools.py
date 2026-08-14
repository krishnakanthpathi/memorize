"""
Lean MCP Core Tools
Registers strictly the 5 primary tools for the Memorize MCP Server:
- store: Store a new memory or auto-update existing
- update: Update or append content to an existing memory
- delete: Delete memory from markdown, SQLite, and ChromaDB
- fetch: Retrieve single memory details or list memories
- hybrid_fetch: Hybrid relevance search combining vector similarity, tag matches, and categories
"""

from typing import List, Optional, Union

from classification.classifier import classify_memory
from config.settings import get_setting
from core.memory_service import execute_upsert_memory, handle_delete_memory
from search.relevance_scorer import search_hybrid_relevance
from storage.db_manager import find_memory_by_title_or_slug, get_all_memories, get_memory_by_id
from storage.markdown_handler import read_markdown_file


CATEGORY_TAXONOMY_DOC = """
Available Categories & Auto-Classification Guide:
- 'personal': Habits, daily routines, diary, thoughts, health, sleep, preferences, contacts, family, lifestyle. Default category if unclassifiable.
- 'development': Programming languages (Python, TypeScript, JS, Rust, Go, C++), frameworks (React, FastAPI, Node), code snippets, algorithms, bug fixes, UI/CSS, git.
- 'projects': Specific software applications, side projects, product ideas, roadmaps, architecture blueprints, feature specs.
- 'job': Career history, work experience, resume, employment, interviews, salary, workplace projects, company tasks.
- 'education': University/college courses, degrees, study notes, academic research, computer science concepts, exam prep.
- 'finance': Personal budget, expenses, investments, stocks, crypto, banking, tax planning, financial goals.
- 'gaming': Video games, strategies, achievements, platforms (Steam, PlayStation, Xbox, Nintendo), esports.
- 'achievements': Competitive exam ranks (JEE, SAT), awards, honors, hackathons, tournament prizes, milestone certifications.
- 'integration': MCP servers, API endpoints, webhooks, cloud setup, Tailscale, WSL, Linux server configs, OAuth, CI/CD.
- 'media': Books, podcasts, audio, video, movies, reading lists, YouTube channels, OCR document scans.
- 'others': Miscellaneous or temporary reference information that does not fit the above categories.
"""


def store(
    title: str,
    content: str = "",
    category: str = "personal",
    tags: Optional[List[str]] = None,
    memory_id: Optional[str] = None,
) -> dict:
    """
    Stores knowledge into the Memorize knowledge base. Automatically creates a new note or appends to an existing topic.
    
    CRITICAL INSTRUCTION FOR LLM:
    If the user does NOT explicitly provide a category, YOU MUST choose the single best matching category from this predefined taxonomy:
    
    1. 'personal': Daily life, habits, health, sleep, diary, contacts, personal preferences, lifestyle.
    2. 'development': Programming languages, frameworks (React, FastAPI, Python, TypeScript), code snippets, algorithms, dev tools, CSS/UI, debugging.
    3. 'projects': Application builds, side projects, product specs, MVPs, feature roadmaps, system designs.
    4. 'job': Career, resume, employment history, company projects, interviews, work achievements, salary.
    5. 'education': College/university, study notes, degrees, exam prep, academic research, courses.
    6. 'finance': Budget, expenses, investments, stock portfolio, crypto, bank accounts, taxes.
    7. 'gaming': Video games, game lore, strategies, game achievements, Steam/console gaming.
    8. 'achievements': Exam ranks, awards, prizes, certifications, hackathon wins, major milestones.
    9. 'integration': MCP server configs, APIs, webhooks, SSH, WSL, cloud infrastructure, OAuth.
    10. 'media': Books, movies, podcasts, YouTube playlists, reading summaries, audio/video notes.
    11. 'others': General miscellaneous reference notes.
    
    Args:
        title: Title or subject of the memory (e.g., 'Python Async Best Practices', 'Investment Portfolio 2026')
        content: Detailed Markdown body content
        category: Category name strictly chosen from the taxonomy above (defaults to 'personal')
        tags: Optional list of 2-5 concise descriptive tags (e.g. ['python', 'async', 'backend'])
        memory_id: Optional explicit memory ID
    """
    if tags is None:
        tags = []

    use_llm = bool(get_setting("use_llm", False))
    if use_llm and (not tags or not category or category == "personal") and content:
        try:
            full_text = f"{title}\n{content}".strip()
            classification = classify_memory(full_text)
            if classification.get("category") and (not category or category == "personal"):
                category = classification["category"]
            if classification.get("tags") and not tags:
                tags = classification["tags"]
        except Exception:
            pass

    return execute_upsert_memory(
        title=title,
        content=content,
        action="auto",
        category=category or "personal",
        tags=tags,
        memory_id=memory_id,
    )


def update(
    title: str,
    content: str = "",
    category: str = "personal",
    tags: Optional[List[str]] = None,
    memory_id: Optional[str] = None,
    append: bool = False,
) -> dict:
    """
    Updates an existing memory's content. Overwrites, cleanly merges, or appends new information.
    
    Categories:
    'personal', 'development', 'projects', 'job', 'education', 'finance', 'gaming', 'achievements', 'integration', 'media', 'others'.
    
    Args:
        title: Title or subject of the memory to update
        content: New content or update to apply
        category: Category folder name (strictly one of the 11 categories)
        tags: Optional list of updated tags
        memory_id: Optional memory ID to target
        append: If True, appends content to the end of the note rather than updating/merging
    """
    if tags is None:
        tags = []

    action = "append" if append else "update"
    return execute_upsert_memory(
        title=title,
        content=content,
        action=action,
        category=category or "personal",
        tags=tags,
        memory_id=memory_id,
    )


def delete(
    memory_id: Optional[str] = None,
    title: Optional[str] = None,
    category: str = "personal",
) -> dict:
    """
    Deletes a memory across disk Markdown storage, SQLite database index, and ChromaDB vector store.
    
    Args:
        memory_id: The unique ID of the memory to delete (e.g. 'mem_abc123')
        title: Optional title of the memory if memory_id is unknown
        category: Category name where the note is stored (default 'personal')
    """
    if not memory_id and not title:
        return {
            "status": "error",
            "message": "Either 'memory_id' or 'title' must be provided to delete a memory.",
        }

    return handle_delete_memory(
        norm_title=title or "",
        category=category or "personal",
        memory_id=memory_id,
    )


def fetch(
    memory_id: Optional[str] = None,
    title: Optional[str] = None,
    category_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
) -> dict:
    """
    Fetches full memory metadata and markdown content for a specific ID/title, or lists stored memories.
    
    Available category filters:
    'personal', 'development', 'projects', 'job', 'education', 'finance', 'gaming', 'achievements', 'integration', 'media', 'others'.
    
    Args:
        memory_id: Specific memory ID to retrieve
        title: Specific title to retrieve if memory_id is unknown
        category_filter: Optional category restriction to filter listed memories
        tag_filter: Optional tag restriction to filter listed memories
    """
    target_mem = None

    if memory_id:
        target_mem = get_memory_by_id(memory_id)
    elif title:
        target_mem = find_memory_by_title_or_slug(title, category_filter or "personal")
        if not target_mem:
            all_mems = get_all_memories()
            clean_title = title.strip().lower()
            for m in all_mems:
                if m.get("title", "").strip().lower() == clean_title or m.get("id") == title:
                    target_mem = m
                    break

    if target_mem:
        file_path = target_mem.get("file_path", "")
        read_result = read_markdown_file(file_path)

        frontmatter, content = ({}, "")
        if not (isinstance(read_result, dict) and read_result.get("status") == "error"):
            frontmatter, content = read_result

        return {
            "status": "success",
            "memory_id": target_mem.get("id"),
            "title": target_mem.get("title"),
            "category": target_mem.get("category"),
            "tags": target_mem.get("tags", []),
            "file_path": file_path,
            "frontmatter": frontmatter,
            "content": content or target_mem.get("content", ""),
            "created_at": target_mem.get("created_at"),
            "updated_at": target_mem.get("updated_at"),
        }

    if memory_id or title:
        return {
            "status": "error",
            "message": f"Memory with ID/Title '{memory_id or title}' not found.",
        }

    memories = get_all_memories(category_filter=category_filter, tag_filter=tag_filter)
    return {
        "status": "success",
        "total_count": len(memories),
        "memories": memories,
    }


def hybrid_fetch(
    query: str,
    category_filter: Optional[str] = None,
    top_k: int = 5,
) -> Union[List[dict], dict]:
    """
    Performs 50/30/20 weighted hybrid RAG search across memories combining Vector Similarity (50%),
    Tag Match (30%), and Category Match (20%).
    
    Category filter can be any of:
    'personal', 'development', 'projects', 'job', 'education', 'finance', 'gaming', 'achievements', 'integration', 'media', 'others'.
    
    Args:
        query: Natural language search query or question
        category_filter: Optional category restriction
        top_k: Number of ranked memories to retrieve (default 5)
    """
    return search_hybrid_relevance(
        query=query,
        category_filter=category_filter if category_filter else None,
        top_k=top_k,
    )


def register_memory_tools(mcp):
    """Register the 5 core MCP tools on the FastMCP server instance."""
    mcp.tool()(store)
    mcp.tool()(update)
    mcp.tool()(delete)
    mcp.tool()(fetch)
    mcp.tool()(hybrid_fetch)
    return mcp



