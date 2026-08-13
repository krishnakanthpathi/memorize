from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class CLIPrinter:
    def __init__(self):
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def print_banner(self):
        banner_text = (
            "=================================================================\n"
            "   🧠 MEMORIZE — Local-First Personal AI & Vector Memory System  \n"
            "================================================================="
        )
        if HAS_RICH:
            self.console.print(
                Panel.fit(
                    "[bold bright_white]🧠 MEMORIZE[/bold bright_white] [dim]—[/dim] [bold cyan]Local-First Personal AI & Vector Engine[/bold cyan]\n"
                    "[dim white]Organized Memory Management & Interactive Workspace[/dim white]",
                    border_style="cyan",
                )
            )
        else:
            print(banner_text)

    def print_memories_table(self, memories: List[Dict[str, Any]]):
        if not memories:
            self.print_info("No memories stored in database.")
            return

        if HAS_RICH:
            table = Table(
                title=f"Stored Memories ({len(memories)} total)",
                show_header=True,
                header_style="bold bright_white on blue",
                border_style="cyan",
            )
            table.add_column("ID", style="dim cyan", width=14)
            table.add_column("Title", style="bold white")
            table.add_column("Category", style="bright_cyan")
            table.add_column("Tags", style="yellow")
            table.add_column("File Path", style="dim white")
            table.add_column("Updated At", style="green")

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
        else:
            print(f"\n--- Stored Memories ({len(memories)} total) ---")
            for m in memories:
                tags = ", ".join(m.get("tags", []))
                print(f"[{m.get('id')}] {m.get('title')} ({m.get('category')}) | Tags: {tags} | Updated: {m.get('updated_at')}")

    def print_search_results(self, results: List[Dict[str, Any]], query: str = ""):
        if not results:
            self.print_info(f"No search results found for query '{query}'.")
            return

        if HAS_RICH:
            self.console.print(f"\n[bold green]🔍 Search Results for:[/bold green] [bold white]\"{query}\"[/bold white] [dim]({len(results)} matches)[/dim]")
            for idx, res in enumerate(results, start=1):
                score = res.get("final_score") or res.get("similarity_score", 0.0)
                snippet = res.get("snippet") or res.get("content", "")
                tags_str = ", ".join(res.get("tags", []))

                panel_content = (
                    f"[bold yellow]Score:[/bold yellow] {score:.4f} | "
                    f"[bold cyan]Category:[/bold cyan] {res.get('category')} | "
                    f"[bold white]Tags:[/bold white] {tags_str}\n\n"
                    f"[white]{snippet[:300]}[/white]"
                )
                self.console.print(
                    Panel(
                        panel_content,
                        title=f"#{idx} {res.get('title')} [{res.get('id')}]",
                        border_style="cyan" if idx == 1 else "grey35",
                    )
                )
        else:
            print(f"\n--- Search Results for '{query}' ---")
            for idx, res in enumerate(results, start=1):
                score = res.get("final_score", 0.0)
                print(f"#{idx} [{res.get('id')}] {res.get('title')} (Score: {score:.4f})\n   {res.get('snippet', '')[:200]}\n")

    def print_chat_reply(
        self,
        message: str,
        reply: str,
        memories_used: Optional[List[Dict[str, Any]]] = None,
        tool_executed: Optional[Dict[str, Any]] = None,
    ):
        if HAS_RICH:
            self.console.print(f"\n[bold cyan]You ›[/bold cyan] {message}")
            if tool_executed:
                t_name = tool_executed.get("tool", "unknown")
                t_status = tool_executed.get("status", "success")
                self.console.print(f"[bold magenta]⚡ Executed Tool:[/bold magenta] [yellow]{t_name}[/yellow] ([green]{t_status}[/green])")
            self.console.print(Panel(reply, title="Memorize Companion (Ollama)", border_style="cyan"))
            if memories_used:
                sources = ", ".join([f"{m.get('title')} ({m.get('id')})" for m in memories_used])
                self.console.print(f"[dim yellow]Memory Context Used:[/dim yellow] [dim cyan]{sources}[/dim cyan]\n")
        else:
            print(f"\nYou > {message}")
            if tool_executed:
                print(f"Tool Executed: {tool_executed.get('tool')} ({tool_executed.get('status')})")
            print(f"Memorize Companion >\n{reply}")
            if memories_used:
                sources = ", ".join([f"{m.get('title')}" for m in memories_used])
                print(f"Memory Sources: {sources}\n")

    def print_settings_panel(self, settings: Dict[str, Any]):
        if HAS_RICH:
            table = Table(
                title="⚙️ Memorize Engine Settings & Configuration",
                show_header=True,
                header_style="bold bright_white on blue",
                border_style="cyan",
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
            self.console.print("[dim white]Use [bold cyan]/settings <key> <value>[/bold cyan] or [bold cyan]--set-key <key> --set-val <val>[/bold cyan] to change settings.[/dim white]\n")
        else:
            print("\n--- Memorize Engine Settings ---")
            for k, v in settings.items():
                print(f"{k}: {v}")
            print()



    def print_audit_report(self, report: Dict[str, Any]):
        if HAS_RICH:
            is_healthy = report.get("is_healthy", False)
            status_text = "[bold green]HEALTHY ✔[/bold green]" if is_healthy else "[bold yellow]ISSUES DETECTED ⚠️[/bold yellow]"
            self.console.print(f"\n[bold white]Storage Integrity Status:[/bold white] {status_text}")

            summary = report.get("summary", {})
            table = Table(
                title="⚙️ Storage Audit Diagnostics",
                show_header=True,
                header_style="bold bright_white on blue",
                border_style="cyan",
            )
            table.add_column("Diagnostic Check", style="bold white")
            table.add_column("Count", style="yellow")
            table.add_column("Status", style="cyan")

            table.add_row("Orphan Markdown Files (disk only)", str(summary.get("orphan_files_count", 0)), "⚠️ Needs Sync/Recovery" if summary.get("orphan_files_count") else "OK")
            table.add_row("Orphan DB Index Records (missing disk file)", str(summary.get("orphan_indexes_count", 0)), "⚠️ Needs Purge" if summary.get("orphan_indexes_count") else "OK")
            table.add_row("Orphan ChromaDB Vector Chunks (missing DB/disk)", str(summary.get("orphan_chunks_count", 0)), "⚠️ Needs Purge" if summary.get("orphan_chunks_count") else "OK")
            table.add_row("Content Hash Mismatches (out-of-sync content)", str(summary.get("hash_mismatches_count", 0)), "⚠️ Needs Re-index" if summary.get("hash_mismatches_count") else "OK")

            self.console.print(table)
        else:
            print("\n--- Storage Integrity Audit ---")
            print(f"Healthy: {report.get('is_healthy')}")
            summary = report.get("summary", {})
            print(f"Orphan Files: {summary.get('orphan_files_count')}")
            print(f"Orphan Indexes: {summary.get('orphan_indexes_count')}")
            print(f"Orphan Chunks: {summary.get('orphan_chunks_count')}")
            print(f"Hash Mismatches: {summary.get('hash_mismatches_count')}")

    def print_success(self, message: str):
        if HAS_RICH:
            self.console.print(f"[bold green]✔ {message}[/bold green]")
        else:
            print(f"✔ {message}")

    def print_error(self, message: str):
        if HAS_RICH:
            self.console.print(f"[bold red]✖ Error:[/bold red] {message}")
        else:
            print(f"✖ Error: {message}")

    def print_info(self, message: str):
        if HAS_RICH:
            self.console.print(f"[bold cyan]ℹ {message}[/bold cyan]")
        else:
            print(f"ℹ {message}")


printer = CLIPrinter()







