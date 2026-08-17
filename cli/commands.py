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


def handle_list(category: Optional[str] = None, tag: Optional[str] = None):
    memories = get_all_memories(category_filter=category, tag_filter=tag)
    printer.print_memories_table(memories)


def handle_search(query: str, category: Optional[str] = None):
    results = search_hybrid_relevance(query=query, category_filter=category, top_k=5)
    printer.print_search_results(query=query, results=results)


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
            printer.print_success(f"Setting updated: [bold cyan]{key}[/bold cyan] = [bold green]{value}[/bold green]")
        else:
            printer.print_error(f"Failed to update setting '{key}'.")
    elif key:
        val = get_setting(key)
        printer.console.print(f"[bold cyan]{key}[/bold cyan] = [bold yellow]{val}[/bold yellow]")
    else:
        all_settings = get_all_settings()
        printer.print_settings_panel(all_settings)


def handle_read(memory_id_or_path: str):
    res = get_memory_file_status(memory_id_or_path)
    if res.get("status") == "error":
        printer.print_error(res.get("message"))
    else:
        printer.print_memory_details(res)


def handle_delete(memory_id: str):
    res = handle_delete_memory(norm_title="", category="", memory_id=memory_id)
    if res.get("status") == "success":
        printer.print_success(f"Successfully deleted memory '{memory_id}'.")
    else:
        printer.print_error(res.get("message", "Error deleting memory."))


def handle_clear_all():
    """
    Prompts user for confirmation before wiping all memories across disk, DB, and ChromaDB.
    """
    confirm = printer.console.input("[bold red]⚠️ Are you sure you want to delete ALL stored memories? (y/N): [/bold red]").strip().lower()
    if confirm in ("y", "yes"):
        from storage.sync_manager import clear_all_memories
        with printer.console.status("[bold red]🧹 Clearing all memories from disk, SQLite DB, and ChromaDB...[/bold red]", spinner="dots"):
            res = clear_all_memories()
        printer.print_success("All stored memories, database records, and vector chunks have been cleared.")
    else:
        printer.print_info("Operation cancelled.")


def handle_revert(memory_id: str, version: Optional[int] = None):
    res = execute_revert_memory(memory_id=memory_id, version_number=version)
    if res.get("status") == "success":
        printer.print_success(f"Successfully reverted memory '{memory_id}' to version {res.get('reverted_to_version')}.")
    else:
        printer.print_error(res.get("message", "Error reverting memory."))


def handle_audit():
    with printer.console.status("[bold orange1]⚙️ Running storage integrity & orphan diagnostics...[/bold orange1]", spinner="dots"):
        report = audit_storage_integrity(auto_fix=False)
    printer.print_audit_report(report)


def handle_purge_orphans():
    with printer.console.status("[bold orange1]🧹 Purging orphan database records & vector chunks...[/bold orange1]", spinner="dots"):
        i_res = delete_orphan_indexes()
        c_res = delete_orphan_chunks()
    del_indexes = i_res.get("deleted_count", 0)
    del_chunks = c_res.get("deleted_count", 0)
    if del_indexes or del_chunks:
        printer.print_success(
            f"Purged dead records — Removed {del_indexes} orphan DB index record(s) and {del_chunks} orphan ChromaDB chunk(s)."
        )
    else:
        printer.print_info("No orphan DB records or vector chunks found to purge.")


# Alias for backwards compatibility
handle_clean_orphans = handle_purge_orphans


def handle_recover_orphans():
    with printer.console.status("[bold orange1]🩹 Scanning & recovering unindexed markdown documents...[/bold orange1]", spinner="dots"):
        res = recover_orphaned_documents()
    rec_count = res.get("recovered_count", 0)
    if rec_count:
        printer.print_success(f"Recovered {rec_count} document(s) with newly generated IDs.")
    else:
        printer.print_info("No unindexed orphan markdown files found on disk.")


def handle_sync():
    printer.print_info("Running automatic storage synchronization & repair...")
    with printer.console.status("[bold orange1]⚙️ Reconciling disk files, SQLite records, and ChromaDB embeddings...[/bold orange1]", spinner="dots"):
        report = audit_storage_integrity(auto_fix=True)
    res = report.get("auto_fix_results", {})
    printer.print_success(
        f"Storage synchronized — Recovered {res.get('recovered_documents', 0)} document(s), "
        f"Purged {res.get('deleted_orphan_indexes', 0)} dead index(es), "
        f"Purged {res.get('deleted_orphan_chunks', 0)} dead chunk(s)."
    )
    printer.print_audit_report(report)
