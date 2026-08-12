from typing import Any, Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown


class CLIPrinter:
    """
    Rich terminal printing visualizer for Memorize CLI commands, memory queries, and metrics.
    """

    def __init__(self):
        self.console = Console()

    def print_banner(self):
        banner_text = (
            "[bold cyan]🧠 MEMORIZE AI COMPANION[/bold cyan]\n"
            "[dim]LangChain & LangGraph GraphRAG Personal Knowledge Assistant[/dim]"
        )
        self.console.print(Panel(banner_text, border_style="cyan", expand=False))

    def print_agent_response(self, response: Dict[str, Any]):
        status = response.get("status")
        query = response.get("query", "")
        reply = response.get("reply", "")
        intent = response.get("intent", "retrieve")
        latency = response.get("latency_ms", 0.0)
        is_offline = response.get("is_offline_mode", False)

        if status == "error":
            self.console.print(Panel(f"[bold red]Error:[/bold red] {response.get('message')}", border_style="red"))
            return

        mode_badge = "[bold yellow]⚡ Zero-LLM Offline Mode[/bold yellow]" if is_offline else "[bold green]🤖 LangGraph RAG Mode[/bold green]"
        meta_info = f"Intent: [bold magenta]{intent}[/bold magenta] | Latency: [bold cyan]{latency} ms[/bold cyan] | Mode: {mode_badge}"

        self.console.print("\n" + meta_info)
        self.console.print(Panel(Markdown(reply), title=f"[bold]Query: {query}[/bold]", border_style="green"))

    def print_memories_table(self, memories: List[Dict[str, Any]]):
        if not memories:
            self.console.print("[yellow]No memories found.[/yellow]")
            return

        table = Table(title="🧠 Stored Memories", border_style="blue")
        table.add_column("ID", style="dim", no_wrap=True)
        table.add_column("Title", style="bold white")
        table.add_column("Category", style="cyan")
        table.add_column("Tags", style="green")

        for mem in memories:
            table.add_row(
                mem.get("id", ""),
                mem.get("title", ""),
                mem.get("category", "personal"),
                ", ".join(mem.get("tags", [])),
            )

        self.console.print(table)

    def print_metrics(self, summary: Dict[str, Any]):
        table = Table(title="📊 Performance Metrics Summary", border_style="magenta")
        table.add_column("Metric", style="bold yellow")
        table.add_column("Value", style="bold white")

        table.add_row("Total Queries", str(summary.get("total_queries", 0)))
        table.add_row("Successful Queries", str(summary.get("successful_queries", 0)))
        table.add_row("Offline Mode Executions", str(summary.get("offline_mode_executions", 0)))
        table.add_row("Average Latency", f"{summary.get('avg_query_latency_ms', 0)} ms")
        table.add_row("Total Tokens Used", str(summary.get("total_tokens", 0)))
        table.add_row("Retrieval Hits", str(summary.get("retrieval_hits", 0)))

        self.console.print(table)


printer = CLIPrinter()
