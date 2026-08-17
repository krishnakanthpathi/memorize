from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown


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
        table.add_column("Snippet Preview", style="dim white", min_width=30)

        for mem in memories:
            tags = mem.get("tags", [])
            tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
            snippet = mem.get("snippet") or mem.get("content", "")[:100].replace("\n", " ")
            table.add_row(
                str(mem.get("id", "")),
                str(mem.get("title", "")),
                str(mem.get("category", "")),
                tags_str,
                snippet,
            )

        self.console.print(table)

    def print_search_results(self, query: str, results: List[Dict[str, Any]]):
        if not results:
            self.print_info(f"No memories matched query: '{query}'")
            return

        table = Table(
            title=f"Hybrid Search Results for '{query}' ({len(results)} matches)",
            show_header=True,
            header_style="bold bright_white on orange4",
            border_style="orange3",
            box=box.ROUNDED,
            caption="[dim white]Hybrid scoring combines vector cosine similarity & full-text relevance[/dim white]",
            caption_justify="center",
        )
        table.add_column("Score", justify="right", style="bold yellow", width=8)
        table.add_column("ID", style="dim orange1", width=16)
        table.add_column("Title", style="bold white", min_width=20)
        table.add_column("Category", style="orange1", width=12)
        table.add_column("Matching Snippet", style="dim white", min_width=32)

        for r in results:
            score_val = r.get("final_score", 0.0)
            score_str = f"{score_val:.3f}" if isinstance(score_val, float) else str(score_val)
            snippet = r.get("snippet") or r.get("content", "")[:120].replace("\n", " ")
            snippet_clean = snippet[:110] + "..." if len(snippet) > 110 else snippet
            table.add_row(
                score_str,
                str(r.get("id", "")),
                str(r.get("title", "")),
                str(r.get("category", "")),
                snippet_clean,
            )

        self.console.print(table)

    def print_memory_details(self, details: Dict[str, Any]):
        if not details or details.get("status") == "error":
            self.print_error(details.get("message", "Invalid memory details."))
            return

        mem = details.get("memory", details)
        m_id = mem.get("id", "Unknown")
        title = mem.get("title", "Untitled")
        category = mem.get("category", "personal")
        tags = mem.get("tags", [])
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
        created_at = mem.get("created_at", "N/A")
        file_path = mem.get("file_path", "N/A")
        content = mem.get("content", "")
        versions_count = details.get("versions_count", 1)

        meta_table = Table(box=None, show_header=False)
        meta_table.add_column("Field", style="bold orange1", width=16)
        meta_table.add_column("Value", style="bold white")

        meta_table.add_row("Memory ID", m_id)
        meta_table.add_row("Title", title)
        meta_table.add_row("Category", category)
        meta_table.add_row("Tags", f"[yellow]{tags_str}[/yellow]")
        meta_table.add_row("Versions Saved", str(versions_count))
        meta_table.add_row("Created At", str(created_at))
        meta_table.add_row("File Path", str(file_path))

        self.console.print(
            Panel(
                meta_table,
                title=f"📁 Memory Metadata — {m_id}",
                subtitle=f"[dim white]Category: {category}[/dim white]",
                border_style="orange3",
                box=box.ROUNDED,
            )
        )

        if content:
            rendered_content = Markdown(content)
            self.console.print(
                Panel(
                    rendered_content,
                    title="📖 Document Markdown Body",
                    border_style="orange1",
                    box=box.ROUNDED,
                )
            )

    def print_endpoints_panel(self):
        table = Table(
            title="🌐 Memorize Backend REST API Routing Table",
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

        table.add_row("GET", "/api/memories", "List all stored memory records", "/list")
        table.add_row("POST", "/api/memories", "Create or update memory file & vector index", "/create")
        table.add_row("POST", "/api/memories/merge", "Merge and synthesize multiple notes", "N/A")
        table.add_row("GET", "/api/memories/{id}", "Get full memory document & metadata", "/read <id>")
        table.add_row("DELETE", "/api/memories/{id}", "Delete memory from disk and databases", "/delete <id>")
        table.add_row("POST", "/api/memories/{id}/revert", "Revert memory to earlier version", "/revert <id>")
        table.add_row("POST", "/api/search", "Semantic hybrid relevance search", "/search <q>")
        table.add_row("GET", "/api/audit", "Storage integrity & orphan diagnostics", "/audit")
        table.add_row("POST", "/api/audit/sync", "Auto-reconcile & fix storage systems", "/sync")
        table.add_row("POST", "/api/audit/purge", "Purge dead DB records & orphan chunks", "/purge")
        table.add_row("GET", "/api/models", "List available LLMs & embedding models", "/settings")
        table.add_row("POST", "/api/settings/test-llm", "Test LLM connectivity", "N/A")
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
            "ollama_model": "Generative LLM model name for Ollama",
            "search_top_k": "Number of top retrieved memories for hybrid search",
            "temperature": "Sampling temperature for model generations",
            "use_llm": "Toggle AI augmentation vs offline fast deterministic mode",
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
            caption="[dim white]Inspect any prompt body with: [bold orange1]/prompts <key>[/bold orange1][/dim white]",
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
