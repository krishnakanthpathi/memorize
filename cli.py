import argparse
import sys
from typing import Optional

from core.logger import configure_cli_logging
from graph.workflow import MemorizeGraphRAGAgent
from storage.db_manager import get_all_memories, init_db
from core.metrics import metrics_collector
from ui.cli_printer import printer


def main():
    configure_cli_logging()
    parser = argparse.ArgumentParser(description="Memorize LangGraph GraphRAG Interactive CLI")
    parser.add_argument("--query", "-q", type=str, help="Query string to execute")
    parser.add_argument("--category", "-c", type=str, help="Category filter")
    parser.add_argument("--list", "-l", action="store_true", help="List stored memories")
    parser.add_argument("--metrics", "-m", action="store_true", help="Display performance metrics")

    args = parser.parse_args()

    init_db()
    agent = MemorizeGraphRAGAgent()

    if args.list:
        memories = get_all_memories(category_filter=args.category)
        printer.print_memories_table(memories)
        return

    if args.metrics:
        printer.print_metrics(metrics_collector.get_summary())
        return

    if args.query:
        res = agent.run(query=args.query, category=args.category)
        printer.print_agent_response(res)
        return

    # Interactive Loop
    printer.print_banner()
    printer.console.print("\n[dim]Type your message to chat, or 'exit' / 'quit' to stop.[/dim]\n")

    while True:
        try:
            user_input = printer.console.input("[bold cyan]You > [/bold cyan]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                printer.console.print("[dim]Goodbye![/dim]")
                break
            if user_input.lower() == "/metrics":
                printer.print_metrics(metrics_collector.get_summary())
                continue
            if user_input.lower() == "/list":
                memories = get_all_memories()
                printer.print_memories_table(memories)
                continue

            res = agent.run(query=user_input)
            printer.print_agent_response(res)
        except KeyboardInterrupt:
            printer.console.print("\n[dim]Session terminated.[/dim]")
            break


if __name__ == "__main__":
    main()
