from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

TOOL_ENDPOINT_MAP = {
    "create_memory": ("POST", "/api/memories"),
    "store_memory": ("POST", "/api/memories"),
    "upsert_memory": ("POST", "/api/memories"),
    "read_memory": ("GET", "/api/memories/{id}"),
    "get_memory": ("GET", "/api/memories/{id}"),
    "read": ("GET", "/api/memories/{id}"),
    "search_memories": ("POST", "/api/search"),
    "search": ("POST", "/api/search"),
    "list_memories": ("GET", "/api/memories"),
    "delete_memory": ("DELETE", "/api/memories/{id}"),
    "delete": ("DELETE", "/api/memories/{id}"),
    "clear_all_memories": ("POST", "/api/audit/sync"),
    "clear_all": ("POST", "/api/audit/sync"),
    "reset_memories": ("POST", "/api/audit/sync"),
}


class CLIPrinter:
    def __init__(self):
        self.console = Console()

    def print_banner(self):
        self.console.print(
            Panel.fit(
                "[bold orange1]🧠 MEMORIZE[/bold orange1] [dim]—[/dim] [bold white]Local-First Personal AI & Vector Engine[/bold white]\n"
                "[dim white]Organized Memory Management & Interactive Workspace[/dim white]\n"
                "[dim orange3]Backend REST API: http://localhost:6999[/dim orange3]",
                border_style="orange3",
                box=box.ROUNDED,
            )
        )

    def print_memories_table(self, memories: List[Dict[str, Any]]):
        if not memories:
            self.print_info("No memories stored in database.")
            return

        table = Table(
            title=f"Stored Memories ({len(memories)} total)",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3",
            box=box.ROUNDED,
            caption="[dim white]Endpoint: GET http://localhost:6999/api/memories[/dim white]",
            caption_justify="center",
        )
        table.add_column("ID", style="dim orange1", width=16)
        table.add_column("Title", style="bold white", min_width=20)
        table.add_column("Category", style="orange1", min_width=12)
        table.add_column("Tags", style="yellow")
        table.add_column("File Path", style="dim white")
        table.add_column("Updated At", style="green", width=19)

        for m in memories:
            tags_str = ", ".join(m.get("tags", [])) if isinstance(m.get("tags"), list) else str(m.get("tags", ""))
            table.add_row(
                str(m.get("id", "")),
                str(m.get("title", "")),
                str(m.get("category", "")),
                tags_str,
                str(m.get("file_path", "")),
                str(m.get("updated_at", ""))[:19],
            )
        self.console.print(table)

    def print_search_results(self, query: str, results: List[Dict[str, Any]]):
        if not results:
            self.print_info(f"No memories matched query: '{query}'")
            return

        table = Table(
            title=f"🔍 Search Results for '{query}' ({len(results)} found)",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3",
            box=box.ROUNDED,
            caption="[dim white]Endpoint: POST http://localhost:6999/api/search[/dim white]",
            caption_justify="center",
        )
        table.add_column("Score", justify="center", style="bold green", width=7)
        table.add_column("Title", style="bold white", min_width=20)
        table.add_column("Category", style="orange1", width=12)
        table.add_column("Excerpt / Content Match", style="dim white")

        for r in results:
            score = f"{r.get('relevance_score', 0.0):.2f}"
            snippet = r.get("snippet") or r.get("content", "")
            snippet_clean = snippet.replace("\n", " ").strip()
            if len(snippet_clean) > 90:
                snippet_clean = snippet_clean[:87] + "..."

            table.add_row(
                score,
                str(r.get("title", "")),
                str(r.get("category", "")),
                snippet_clean,
            )

        self.console.print(table)

    def print_chat_reply(
        self,
        message: str,
        reply: str,
        memories_used: Optional[List[Dict[str, Any]]] = None,
        tool_executed: Optional[Dict[str, Any]] = None,
    ):
        self.console.print(
            Panel(
                f"[bold bright_white]{message}[/bold bright_white]",
                title="💬 Prompt",
                subtitle="[dim white]POST http://localhost:6999/api/chat[/dim white]",
                subtitle_align="right",
                border_style="orange3",
                box=box.ROUNDED,
            )
        )

        if tool_executed:
            t_name = tool_executed.get("tool", "unknown")
            t_status = tool_executed.get("status", "success")
            t_info = TOOL_ENDPOINT_MAP.get(t_name.lower(), ("POST", "/api/chat"))
            method, path = t_info
            status_color = "green" if t_status == "success" else "red"
            self.console.print(
                f" [bold magenta]⚡ Tool Executed:[/bold magenta] [bold yellow]{t_name}[/bold yellow] "
                f"([{status_color}]{t_status}[/{status_color}]) [dim]→[/dim] "
                f"[bold cyan]{method}[/bold cyan] [dim white]http://localhost:6999{path}[/dim white]"
            )

        rendered_markdown = Markdown(reply)
        self.console.print(
            Panel(
                rendered_markdown,
                title="🤖 Memorize Companion (Ollama)",
                subtitle="[dim white]POST http://localhost:6999/api/chat[/dim white]",
                subtitle_align="right",
                border_style="orange1",
                box=box.ROUNDED,
            )
        )

        if memories_used:
            sources = ", ".join([f"{m.get('title')} ({m.get('id')})" for m in memories_used])
            self.console.print(f"[dim yellow]Memory Context Injected:[/dim yellow] [dim orange1]{sources}[/dim orange1]\n")

    def print_memory_details(self, details: Dict[str, Any]):
        if not details or details.get("status") == "error":
            self.print_error(details.get("message", "Invalid memory details."))
            return

        title = details.get("title", "Untitled")
        memory_id = details.get("memory_id", "N/A")
        category = details.get("category", "N/A")
        tags_raw = details.get("tags", [])
        tags_str = ", ".join(tags_raw) if isinstance(tags_raw, list) else str(tags_raw or "")
        file_path = details.get("file_path", "N/A")
        created_at = str(details.get("created_at") or "N/A")
        updated_at = str(details.get("updated_at") or "N/A")
        file_size = details.get("file_size_bytes", 0)
        est_tokens = details.get("estimated_tokens", 0)
        is_indexed = "Yes" if details.get("is_indexed") else "No"
        content_hash = details.get("content_hash", "N/A")
        content = details.get("content", "")

        meta_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        meta_table.add_column("Field", style="bold orange1", width=14)
        meta_table.add_column("Value", style="white")

        meta_table.add_row("Memory ID", f"[bold cyan]{memory_id}[/bold cyan]")
        meta_table.add_row("Category", f"[yellow]{category}[/yellow]")
        meta_table.add_row("Tags", f"[dim yellow]{tags_str or 'None'}[/dim yellow]")
        meta_table.add_row("File Path", f"[dim white]{file_path}[/dim white]")
        meta_table.add_row("Timestamps", f"[green]Created: {created_at}[/green] | [green]Updated: {updated_at}[/green]")
        meta_table.add_row("Diagnostics", f"[dim white]Size: {file_size} B | Est Tokens: ~{est_tokens} | Indexed: {is_indexed} | Hash: {str(content_hash)[:12]}...[/dim white]")

        self.console.print(
            Panel(
                meta_table,
                title=f"📖 Memory Metadata — {title}",
                subtitle=f"[dim white]Endpoint: GET http://localhost:6999/api/memories/{memory_id}[/dim white]",
                border_style="orange3",
                box=box.ROUNDED,
            )
        )

        if content.strip():
            self.console.print(
                Panel(
                    Markdown(content),
                    title="📝 Document Content",
                    border_style="orange1",
                    box=box.ROUNDED,
                )
            )
        else:
            self.console.print(
                Panel(
                    "[dim italic yellow]No text content recorded for this memory.[/dim italic yellow]",
                    title="📝 Document Content",
                    border_style="dim orange1",
                    box=box.ROUNDED,
                )
            )

    def print_endpoints_panel(self):
        table = Table(
            title="🌐 Memorize REST API Endpoints (FastAPI Backend :6999)",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3",
            box=box.ROUNDED,
            caption="[dim white]Interactive Swagger API Docs: [bold cyan]http://localhost:6999/docs[/bold cyan][/dim white]",
            caption_justify="center",
        )
        table.add_column("Method", style="bold cyan", width=8)
        table.add_column("Endpoint Route", style="bold white", min_width=32)
        table.add_column("Functionality", style="dim white", min_width=36)
        table.add_column("CLI Command", style="bold orange1", width=14)

        table.add_row("POST", "/api/chat", "Conversational AI companion & tool execution", "chat <msg>")
        table.add_row("GET", "/api/memories", "List all stored memory records", "/list")
        table.add_row("POST", "/api/memories", "Create or update memory file & vector index", "/create")
        table.add_row("GET", "/api/memories/{id}", "Get full memory document & metadata", "/read <id>")
        table.add_row("DELETE", "/api/memories/{id}", "Delete memory from disk and databases", "/delete <id>")
        table.add_row("POST", "/api/memories/{id}/revert", "Revert memory to earlier version", "/revert <id>")
        table.add_row("POST", "/api/search", "Semantic hybrid relevance search", "/search <q>")
        table.add_row("GET", "/api/audit", "Storage integrity & orphan diagnostics", "/audit")
        table.add_row("POST", "/api/audit/sync", "Auto-reconcile & fix storage systems", "/sync")
        table.add_row("POST", "/api/audit/purge", "Purge dead DB records & orphan chunks", "/purge")
        table.add_row("GET", "/api/models", "List available LLMs & embedding models", "/settings")
        self.console.print(table)

    def print_settings_panel(self, settings: Dict[str, Any]):
        table = Table(
            title="⚙️ Memorize Engine Settings & Configuration",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3",
            box=box.ROUNDED,
        )
        table.add_column("Setting Key", style="bold white", width=22)
        table.add_column("Current Value", style="bold yellow")
        table.add_column("Description", style="dim white")

        descriptions = {
            "llm_provider": "Active LLM engine provider ('ollama', 'openai', or 'auto')",
            "ollama_base_url": "REST API URL for local/remote Ollama instance",
            "ollama_model": "Generative/chat LLM model name for Ollama",
            "search_top_k": "Number of top retrieved memories attached to chat context",
            "auto_context": "Automatically attach relevant stored memory context to chat prompts",
            "tool_execution": "Allow LLM to execute tools (e.g. search_memories, create_memory)",
            "temperature": "Sampling temperature for model generations",
        }

        for key, val in settings.items():
            desc = descriptions.get(key, "System configuration parameter")
            table.add_row(str(key), str(val), desc)

        self.console.print("\n")
        self.console.print(table)
        self.console.print("[dim white]Use [bold orange1]/settings <key> <value>[/bold orange1] or [bold orange1]--set-key <key> --set-val <val>[/bold orange1] to change settings.[/dim white]\n")

    def print_audit_report(self, report: Dict[str, Any]):
        is_healthy = report.get("is_healthy", False)
        status_badge = "[bold green]HEALTHY ✔[/bold green]" if is_healthy else "[bold yellow]ISSUES DETECTED ⚠️[/bold yellow]"

        summary = report.get("summary", {})
        orphan_files = summary.get("orphan_files_count", 0)
        orphan_indexes = summary.get("orphan_indexes_count", 0)
        orphan_chunks = summary.get("orphan_chunks_count", 0)
        hash_mismatches = summary.get("hash_mismatches_count", 0)

        if not is_healthy:
            actions = []
            if orphan_files:
                actions.append("[bold orange1]/recover[/bold orange1]")
            if orphan_indexes or orphan_chunks:
                actions.append("[bold orange1]/purge[/bold orange1]")
            actions_hint = " or ".join(actions) if actions else "[bold orange1]/sync[/bold orange1]"
            caption_text = f"[dim white]Use {actions_hint} or [bold orange1]/sync[/bold orange1] to repair storage[/dim white]"
        else:
            caption_text = "[dim green]All systems synchronized and healthy[/dim green]"

        table = Table(
            title=f"⚙️ Storage Integrity Diagnostics — {status_badge}",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3" if not is_healthy else "green",
            box=box.ROUNDED,
            caption=caption_text,
            caption_justify="center",
        )
        table.add_column("Diagnostic Check", style="bold white", min_width=38)
        table.add_column("Count", justify="center", style="bold yellow", width=8)
        table.add_column("Status", min_width=22)

        table.add_row(
            "Orphan Markdown Files (disk only)",
            str(orphan_files),
            "[bold yellow]⚠️ Needs Sync/Recovery[/bold yellow]" if orphan_files else "[bold green]OK ✔[/bold green]",
        )
        table.add_row(
            "Orphan DB Index Records (missing disk file)",
            str(orphan_indexes),
            "[bold red]⚠️ Needs Purge[/bold red]" if orphan_indexes else "[bold green]OK ✔[/bold green]",
        )
        table.add_row(
            "Orphan ChromaDB Vector Chunks (missing DB/disk)",
            str(orphan_chunks),
            "[bold yellow]⚠️ Needs Purge[/bold yellow]" if orphan_chunks else "[bold green]OK ✔[/bold green]",
        )
        table.add_row(
            "Content Hash Mismatches (out-of-sync content)",
            str(hash_mismatches),
            "[bold red]⚠️ Needs Re-index[/bold red]" if hash_mismatches else "[bold green]OK ✔[/bold green]",
        )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def print_prompts_panel(self, prompt_name: Optional[str] = None):
        from config.prompts import PROMPT_REGISTRY, list_prompts

        if prompt_name and prompt_name.lower() in PROMPT_REGISTRY:
            p_data = PROMPT_REGISTRY[prompt_name.lower()]
            self.console.print(
                Panel(
                    p_data.get("template", "").strip(),
                    title=f"📝 LLM Prompt Template — {p_data.get('name')}",
                    subtitle=f"[dim white]Key: {prompt_name.lower()} | {p_data.get('description')}[/dim white]",
                    border_style="orange1",
                    box=box.ROUNDED,
                )
            )
            return

        table = Table(
            title="📝 LLM System Prompts & Templates Registry",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3",
            box=box.ROUNDED,
            caption="[dim white]Inspect any prompt body with: [bold orange1]/prompts <key>[/bold orange1] (e.g. /prompts companion)[/dim white]",
            caption_justify="center",
        )
        table.add_column("Prompt Key", style="bold cyan", width=16)
        table.add_column("Template Name", style="bold white", min_width=28)
        table.add_column("Purpose / Description", style="dim white")

        for key, val in list_prompts().items():
            table.add_row(key, val.get("name", ""), val.get("description", ""))

        self.console.print(table)

    def print_success(self, message: str):
        self.console.print(f"[bold green]✔ {message}[/bold green]")

    def print_error(self, message: str):
        self.console.print(f"[bold red]✖ Error:[/bold red] {message}")

    def print_info(self, message: str):
        self.console.print(f"[bold orange1]ℹ {message}[/bold orange1]")


printer = CLIPrinter()
