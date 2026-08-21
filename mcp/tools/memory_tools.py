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
from core.memory_merger import (
    find_correlated_memories as core_find_correlated,
    generate_title_service,
    merge_memories_service,
    organize_selection_service,
    organize_single_memory_service,
)
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


import base64
from pathlib import Path
import re
import requests

from storage.media_store_manager import save_raw_image
from utils.llm_client import extract_text_with_ollama_ocr


def process_embedded_data_urls(content: str, memory_id: Optional[str] = None) -> str:
    """
    Detects base64 data URIs, local image paths, or remote image links in markdown content,
    saves uncompressed images into data/media/, runs local Ollama GLM-OCR, and replaces with local media URLs.
    """
    if not content:
        return content

    # 1. Process Base64 Data URIs
    if "data:image/" in content:
        def replace_data_uri(match):
            mime_type = match.group(1)
            b64_data = match.group(2)
            try:
                raw_bytes = base64.b64decode(b64_data)
                ext = mime_type.split("/")[-1].replace("jpeg", "jpg").split(";")[0]
                rec = save_raw_image(
                    file_bytes=raw_bytes,
                    filename=f"embedded_image.{ext}",
                    mime_type=mime_type,
                    memory_id=memory_id,
                )
                ocr_text = ""
                try:
                    ocr_text = extract_text_with_ollama_ocr(raw_bytes)
                except Exception:
                    pass

                replacement = f"![Image]({rec['url']})"
                if ocr_text:
                    replacement += f"\n\n**Extracted Content (OCR):**\n{ocr_text}"
                return replacement
            except Exception:
                return match.group(0)

        pattern = r"data:(image/[a-zA-Z0-9\+\-\.]+);base64,([A-Za-z0-9+/=]+)"
        content = re.sub(pattern, replace_data_uri, content)

    # 2. Process local file path image embeds: ![Alt](/path/to/image.png)
    def replace_local_file_image(match):
        alt_text = match.group(1)
        path_str = match.group(2).strip()
        
        # Expand ~ if present
        expanded_path = Path(path_str).expanduser()
        if (
            expanded_path.is_file()
            and expanded_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]
        ):
            try:
                raw_bytes = expanded_path.read_bytes()
                mime = f"image/{expanded_path.suffix.lower().lstrip('.')}".replace("jpg", "jpeg")
                rec = save_raw_image(
                    file_bytes=raw_bytes,
                    filename=expanded_path.name,
                    mime_type=mime,
                    memory_id=memory_id,
                )
                ocr_text = ""
                try:
                    ocr_text = extract_text_with_ollama_ocr(raw_bytes)
                except Exception:
                    pass

                replacement = f"![{alt_text or expanded_path.name}]({rec['url']})"
                if ocr_text:
                    replacement += f"\n\n**Extracted Content (GLM-OCR):**\n{ocr_text}"
                return replacement
            except Exception:
                return match.group(0)
        return match.group(0)

    local_img_pattern = r"!\[([^\]]*)\]\((/[^)]+|\~/[^)]+)\)"
    content = re.sub(local_img_pattern, replace_local_file_image, content)

    return content


def store(
    title: str,
    content: str = "",
    category: str = "personal",
    tags: Optional[List[str]] = None,
    memory_id: Optional[str] = None,
) -> dict:
    """
    Stores knowledge, notes, documentation, code, or media into the Memorize knowledge base. Automatically creates a new note or merges into an existing topic.
    
    CRITICAL WORKFLOW - FETCH BEFORE STORING:
    ALWAYS call `fetch` or `hybrid_fetch` BEFORE calling `store`!
    Check if a relevant note or memory already exists on the subject. If an existing note exists,
    use `update` or append to it to avoid creating duplicate, fragmented notes. Only store a new note
    when no existing note covers the topic.

    IMAGE & MEDIA SUPPORT:
    The `content` field fully supports images and visual media:
    - Markdown image embeds: `![Alt description](https://example.com/image.png)` or `![Alt description](/api/media/filename.png)`
    - Base64 Data URLs: `![Document](data:image/png;base64,iVBORw0KGgo...)` or raw `data:image/jpeg;base64,...`
      (These are automatically extracted, uncompressed, stored into data/media/, and OCR-processed with local Ollama GLM-OCR).
    - Local image file paths or diagram URLs.

    CATEGORY TAXONOMY (Strictly choose the single best matching category):
    1. 'personal': Daily life, habits, health, sleep, diary, contacts, personal preferences, lifestyle.
    2. 'development': Programming languages, frameworks (React, FastAPI, Python, TypeScript), code snippets, algorithms, dev tools, CSS/UI, debugging.
    3. 'projects': Application builds, side projects, product specs, MVPs, feature roadmaps, system designs.
    4. 'job': Career, resume, employment history, company projects, interviews, work achievements, salary.
    5. 'education': College/university, study notes, degrees, exam prep, academic research, courses.
    6. 'finance': Budget, expenses, investments, stock portfolio, crypto, bank accounts, taxes.
    7. 'gaming': Video games, game lore, strategies, game achievements, Steam/console gaming.
    8. 'achievements': Exam ranks, awards, prizes, certifications, hackathon wins, major milestones.
    9. 'integration': MCP server configs, APIs, webhooks, SSH, WSL, cloud infrastructure, OAuth.
    10. 'media': Books, movies, podcasts, YouTube playlists, reading summaries, audio/video notes, image OCR scans.
    11. 'others': General miscellaneous reference notes.
    
    Args:
        title: Title or subject of the memory (e.g., 'Python Async Best Practices', 'Aadhaar Card Details')
        content: Detailed Markdown body content (can include text, code blocks, tables, image links, or Base64 Data URLs)
        category: Category name strictly chosen from the taxonomy above (defaults to 'personal')
        tags: Optional list of 2-5 concise descriptive tags (e.g. ['python', 'async', 'backend'])
        memory_id: Optional explicit memory ID
    """
    if tags is None:
        tags = []

    content = process_embedded_data_urls(content, memory_id=memory_id)

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
    Updates or appends content to an existing memory note in the Memorize knowledge base.
    
    CRITICAL WORKFLOW - FETCH BEFORE UPDATING:
    ALWAYS call `fetch` or `hybrid_fetch` FIRST to read the existing note's current markdown content and structure
    before submitting updates. This ensures you preserve existing context and cleanly merge new details.

    IMAGE & MEDIA SUPPORT:
    The `content` field fully supports images, Markdown image links (`![caption](url)`), and Base64 Data URLs
    (`data:image/...;base64,...`) which are automatically saved into local media storage and OCR-processed.

    Categories:
    'personal', 'development', 'projects', 'job', 'education', 'finance', 'gaming', 'achievements', 'integration', 'media', 'others'.
    
    Args:
        title: Title or subject of the memory to update
        content: New Markdown content to apply or append (supports images, tables, code snippets)
        category: Category folder name strictly chosen from the 11 taxonomy categories
        tags: Optional list of updated tags
        memory_id: Optional memory ID to target
        append: If True, appends content to the end of the note rather than updating/merging
    """
    if tags is None:
        tags = []

    content = process_embedded_data_urls(content, memory_id=memory_id)

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
    
    MANDATORY USAGE RULE:
    Use `fetch` or `hybrid_fetch` BEFORE calling `store` or `update` to inspect existing knowledge,
    prevent duplicate notes, and build upon existing records.
    
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


def list_memories(
    category_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """
    Lists stored memories with optional category or tag filtering.
    Returns structured summaries of memories including ID, title, category, tags, and timestamps.
    
    Available category filters:
    'personal', 'development', 'projects', 'job', 'education', 'finance', 'gaming', 'achievements', 'integration', 'media', 'others'.
    
    Args:
        category_filter: Optional category restriction
        tag_filter: Optional tag restriction
        limit: Optional maximum number of memories to return
    """
    all_mems = get_all_memories(category_filter=category_filter, tag_filter=tag_filter)
    if limit and limit > 0:
        all_mems = all_mems[:limit]

    summaries = []
    for m in all_mems:
        summaries.append({
            "id": m.get("id"),
            "title": m.get("title"),
            "category": m.get("category"),
            "tags": m.get("tags", []),
            "updated_at": m.get("updated_at"),
            "created_at": m.get("created_at"),
        })

    return {
        "status": "success",
        "total_count": len(summaries),
        "memories": summaries,
    }


def get_categories() -> dict:
    """
    Returns all 11 standard predefined memory categories along with descriptions
    and the count of notes currently stored in each category.
    
    Categories:
    - 'personal': Habits, daily routines, diary, thoughts, health, sleep, preferences, contacts, family, lifestyle.
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
    from utils import get_available_categories

    categories = get_available_categories()
    all_mems = get_all_memories()

    category_counts = {}
    for cat in categories:
        category_counts[cat] = 0
    for m in all_mems:
        c = m.get("category", "personal").lower()
        category_counts[c] = category_counts.get(c, 0) + 1

    category_descriptions = {
        "personal": "Habits, daily routines, diary, thoughts, health, sleep, preferences, contacts, family, lifestyle.",
        "development": "Programming languages, frameworks (React, FastAPI, Python, TS), code snippets, algorithms, dev tools, CSS/UI, debugging.",
        "projects": "Application builds, side projects, product specs, MVPs, feature roadmaps, system designs.",
        "job": "Career, resume, employment history, company projects, interviews, work achievements, salary.",
        "education": "College/university, study notes, degrees, exam prep, academic research, courses.",
        "finance": "Budget, expenses, investments, stock portfolio, crypto, bank accounts, taxes.",
        "gaming": "Video games, game lore, strategies, game achievements, Steam/console gaming.",
        "achievements": "Exam ranks, awards, prizes, certifications, hackathon wins, major milestones.",
        "integration": "MCP server configs, APIs, webhooks, SSH, WSL, cloud infrastructure, OAuth.",
        "media": "Books, movies, podcasts, YouTube playlists, reading summaries, audio/video notes.",
        "others": "General miscellaneous reference notes.",
    }

    results = []
    for cat in categories:
        results.append({
            "category": cat,
            "count": category_counts.get(cat, 0),
            "description": category_descriptions.get(cat, "General knowledge notes."),
        })

    return {
        "status": "success",
        "total_categories": len(results),
        "categories": results,
    }


def merge_memories(
    memory_ids: List[str],
    target_title: Optional[str] = None,
    target_category: Optional[str] = None,
    target_tags: Optional[List[str]] = None,
    delete_sources: bool = True,
    instruction: Optional[str] = None,
    use_ai: Optional[bool] = None,
) -> dict:
    """
    Consolidates multiple correlated memories/notes into a single, cohesive, non-redundant Markdown document using context-safe LLM synthesis.
    Automatically ensures the combined notes do not exceed the LLM context window.
    
    Args:
        memory_ids: List of 2 or more memory IDs to merge (e.g. ['mem_abc123', 'mem_def456'])
        target_title: Optional title for the merged master memory (defaults to primary note title)
        target_category: Optional category name from the taxonomy (e.g. 'development', 'projects')
        target_tags: Optional list of tags to attach to the merged memory
        delete_sources: Whether to remove the individual source notes after successful consolidation (default True)
        instruction: Optional specific guidance for the LLM during consolidation (e.g. 'Focus on LeetCode patterns', 'Merge CLI configs')
        use_ai: Optional flag to force AI synthesis (True) or deterministic section merge (False). Defaults to global setting.
    """
    return merge_memories_service(
        memory_ids=memory_ids,
        target_title=target_title,
        target_category=target_category,
        target_tags=target_tags,
        delete_sources=delete_sources,
        instruction=instruction,
        use_ai=use_ai,
    )


def find_correlated_memories(
    memory_id: str,
    top_k: int = 5,
) -> dict:
    """
    Discovers related/correlated memories for a given note using vector similarity, category matches, and tag overlap.
    Useful for finding candidate notes to merge.
    
    Args:
        memory_id: The memory ID to find related notes for (e.g. 'mem_abc123')
        top_k: Number of correlated notes to return (default 5)
    """
    results = core_find_correlated(memory_id=memory_id, top_k=top_k)
    return {
        "status": "success",
        "memory_id": memory_id,
        "total_correlated": len(results),
        "correlated_memories": results,
    }


def organize_memory(
    memory_id: str,
    instruction: Optional[str] = None,
    use_ai: bool = True,
    generate_title: bool = False,
) -> dict:
    """
    Polishes, restructures, organizes, or summarizes a single memory note using AI.
    Automatically creates a version snapshot before applying changes so the original can be reverted.

    Args:
        memory_id: The memory ID to organize/polish (e.g. 'mem_abc123')
        instruction: Optional goal or instruction (e.g. 'Summarize into key takeaways', 'Format as clean API reference')
        use_ai: Whether to use AI for intelligent restructuring (default True)
        generate_title: Whether to also generate and update a new descriptive title (default False)
    """
    return organize_single_memory_service(
        memory_id=memory_id,
        instruction=instruction,
        use_ai=use_ai,
        generate_title=generate_title,
    )


def generate_title(
    content: str,
    current_title: Optional[str] = None,
    instruction: Optional[str] = None,
) -> dict:
    """
    Generates a concise, descriptive, and high-signal title (3-7 words) from markdown content or selected text.

    Args:
        content: The note content or text excerpt to generate a title from
        current_title: Optional current working title
        instruction: Optional user context or focus
    """
    title = generate_title_service(
        content=content,
        current_title=current_title,
        instruction=instruction,
        use_ai=True,
    )
    return {
        "status": "success",
        "title": title,
    }


def organize_selection(
    selected_text: str,
    instruction: Optional[str] = None,
    mode: Optional[str] = "polish",
    full_context: Optional[str] = None,
) -> dict:
    """
    Polishes, restructures, summarizes, or transforms a selected paragraph or text snippet using AI.

    Args:
        selected_text: The selected text passage to transform
        instruction: Optional custom prompt instruction
        mode: Transformation mode ('polish', 'summarize', 'technical', 'simplify', 'expand', 'title')
        full_context: Optional surrounding document context
    """
    return organize_selection_service(
        selected_text=selected_text,
        instruction=instruction,
        mode=mode,
        full_context=full_context,
        use_ai=True,
    )


def register_memory_tools(mcp):
    """Register all memory and category MCP tools on the FastMCP server instance."""
    mcp.tool()(store)
    mcp.tool()(update)
    mcp.tool()(delete)
    mcp.tool()(fetch)
    mcp.tool()(hybrid_fetch)
    mcp.tool()(list_memories)
    mcp.tool()(get_categories)
    mcp.tool()(merge_memories)
    mcp.tool()(find_correlated_memories)
    mcp.tool()(organize_memory)
    mcp.tool()(generate_title)
    mcp.tool()(organize_selection)
    return mcp




