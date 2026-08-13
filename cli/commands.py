from typing import List, Optional

from config.settings import get_all_settings, get_setting, set_setting
from core.memory_service import (
    execute_revert_memory,
    execute_upsert_memory,
    handle_delete_memory,
)
from search.relevance_scorer import search_hybrid_relevance
from storage.db_manager import get_all_memories
from storage.sync_manager import (
    audit_storage_integrity,
    delete_orphan_chunks,
    delete_orphan_files,
    delete_orphan_indexes,
    get_memory_file_status,
    recover_orphaned_documents,
)
from cli.printer import printer
from utils.llm_client import generate_llm_response, parse_and_execute_tool


def handle_list(category: Optional[str] = None, tag: Optional[str] = None):
    memories = get_all_memories(category_filter=category, tag_filter=tag)
    printer.print_memories_table(memories)


def handle_search(query: str, category: Optional[str] = None):
    results = search_hybrid_relevance(query=query, category_filter=category, top_k=5)
    printer.print_search_results(results, query=query)


def handle_create(
    title: str,
    content: str = "",
    category: str = "personal",
    tags: Optional[List[str]] = None,
):
    if not title:
        printer.print_error("Memory title cannot be empty.")
        return

    res = execute_upsert_memory(
        title=title,
        content=content,
        action="auto",
        category=category,
        tags=tags or [],
    )
    if res.get("status") == "success":
        printer.print_success(
            f"Successfully created memory '{res.get('title')}' [{res.get('memory_id')}] in category '{res.get('category')}'."
        )
    else:
        printer.print_error(res.get("message", "Failed to create memory."))


def handle_settings(key: Optional[str] = None, value: Optional[str] = None):
    if key and value is not None:
        success = set_setting(key, value)
        if success:
            printer.print_success(f"Setting '{key}' updated to '{get_setting(key)}'.")
        else:
            printer.print_error(f"Failed to update setting '{key}'.")
    else:
        all_settings = get_all_settings()
        printer.print_settings_panel(all_settings)


def handle_chat(message: str):
    provider = get_setting("llm_provider", "ollama")
    model = get_setting("ollama_model", "gpt-oss:120b-cloud")
    base_url = get_setting("ollama_base_url", "http://localhost:11434")
    top_k = get_setting("search_top_k", 4)
    auto_context = get_setting("auto_context", True)
    tool_exec = get_setting("tool_execution", True)
    temp = float(get_setting("temperature", 0.3))


    search_results = []
    context_str = "No relevant memory context attached."
    if auto_context:
        search_results = search_hybrid_relevance(query=message, top_k=top_k)
        if search_results:
            context_snippets = [
                f"[{idx}] Title: {item.get('title')}\nCategory: {item.get('category')}\nExcerpt: {item.get('snippet') or item.get('content', '')}"
                for idx, item in enumerate(search_results, start=1)
            ]
            context_str = "\n\n".join(context_snippets)

    tool_instruction = ""
    if tool_exec:
        tool_instruction = (
            "\nAVAILABLE TOOLS:\n"
            "- create_memory: Save a new memory into the system\n"
            "  Parameters: title: str (required), content: str = \"\", category: str = \"personal\", tags: Optional[List[str]] = None\n"
            "- search_memories: Search stored memories (parameters: query: str, category: Optional[str] = None)\n"
            "If the user explicitly asks you to create/remember/store something or search something specific and you need to invoke a tool, "
            "respond ONLY with a valid JSON object in this format:\n"
            '{"tool": "create_memory", "parameters": {"title": "Title", "content": "Content", "category": "personal", "tags": ["tag1"]}}\n'
        )

    system_prompt = (
        "You are Memorize AI Companion powered by Ollama. "
        "You have direct access to stored personal, project, and technical memories.\n"
        f"{tool_instruction}\n"
        f"RETRIEVED MEMORY CONTEXT:\n{context_str}\n\n"
        "Guidelines: Be concise, friendly, helpful, and reference retrieved memories accurately."
    )

    try:
        reply = generate_llm_response(
            prompt=message,
            system_prompt=system_prompt,
            model=model,
            temperature=temp,
            provider=provider,
            base_url=base_url,
        )

        tool_res = None
        if tool_exec:
            tool_res, raw_reply = parse_and_execute_tool(reply)
            if tool_res:
                t_name = tool_res.get("tool")
                if t_name == "create_memory":
                    res_data = tool_res.get("result", {})
                    reply = f"Memory saved successfully! Title: '{res_data.get('title')}' (ID: {res_data.get('memory_id')}, Category: {res_data.get('category')})."
                elif t_name == "search_memories":
                    res_data = tool_res.get("result", [])
                    res_titles = [m.get("title") for m in res_data] if isinstance(res_data, list) else []
                    reply = f"Found {len(res_titles)} matching memory/memories: {', '.join(res_titles) if res_titles else 'None'}."

        mem_used = [{"id": m.get("id"), "title": m.get("title"), "category": m.get("category")} for m in search_results]
        printer.print_chat_reply(message=message, reply=reply, memories_used=mem_used, tool_executed=tool_res)

    except Exception as e:
        printer.print_error(f"Ollama chat error: {e}")


def handle_read(memory_id_or_path: str):
    res = get_memory_file_status(memory_id_or_path)
    if res.get("status") == "error":
        printer.print_error(res.get("message"))
    else:
        printer.print_info(f"Memory Details for '{memory_id_or_path}':")
        if printer.console:
            printer.console.print(res)
        else:
            print(res)


def handle_delete(memory_id: str):
    res = handle_delete_memory(norm_title="", category="", memory_id=memory_id)
    if res.get("status") == "success":
        printer.print_success(f"Successfully deleted memory '{memory_id}'.")
    else:
        printer.print_error(res.get("message", "Error deleting memory."))


def handle_revert(memory_id: str, version: Optional[int] = None):
    res = execute_revert_memory(memory_id=memory_id, version_number=version)
    if res.get("status") == "success":
        printer.print_success(f"Successfully reverted memory '{memory_id}' to version {res.get('reverted_to_version')}.")
    else:
        printer.print_error(res.get("message", "Error reverting memory."))


def handle_audit():
    report = audit_storage_integrity(auto_fix=False)
    printer.print_audit_report(report)


def handle_clean_orphans():
    f_res = delete_orphan_files()
    i_res = delete_orphan_indexes()
    c_res = delete_orphan_chunks()
    printer.print_success(
        f"Cleaned orphans — Deleted files: {f_res.get('deleted_count')}, "
        f"Indexes: {i_res.get('deleted_count')}, Chunks: {c_res.get('deleted_count')}."
    )


def handle_recover_orphans():
    res = recover_orphaned_documents()
    printer.print_success(f"Recovered {res.get('recovered_count', 0)} document(s) with newly generated IDs.")

