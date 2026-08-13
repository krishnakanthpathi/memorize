from cli.commands import (
    handle_chat,
    handle_create,
    handle_delete,
    handle_list,
    handle_read,
    handle_recover_orphans,
    handle_revert,
    handle_search,
    handle_settings,
)
from cli.printer import printer
from storage.sync_manager import audit_storage_integrity


def show_help():
    help_text = (
        "\n[bold bright_white]Available CLI Commands:[/bold bright_white]\n"
        "  [bold cyan]/list [category][/bold cyan]         - List memories (optional category filter)\n"
        "  [bold cyan]/search <query>[/bold cyan]          - Hybrid search across stored memories\n"
        "  [bold cyan]/create[/bold cyan]                  - Create a new memory interactively or with parameters\n"
        "                             [dim yellow](title: str, content: str = \"\", category: str = \"personal\", tags: Optional[List[str]] = None)[/dim yellow]\n"
        "  [bold cyan]/settings [key] [val][/bold cyan]   - View or update configuration settings\n"
        "  [bold cyan]/read <memory_id>[/bold cyan]        - View memory content and status\n"
        "  [bold cyan]/delete <memory_id>[/bold cyan]      - Delete memory by ID\n"
        "  [bold cyan]/revert <id> [ver][/bold cyan]       - Revert memory to a previous version\n"
        "  [bold cyan]/audit[/bold cyan]                   - Run storage integrity & orphan audit\n"
        "  [bold cyan]/recover[/bold cyan]                 - Recover unindexed files & generate IDs\n"
        "  [bold cyan]/help[/bold cyan]                    - Show this help message\n"
        "  [bold cyan]/exit[/bold cyan]                    - Exit shell\n"
        "  [dim white]<type any text>[/dim white]             - Chat directly with AI Companion (Ollama)\n"
    )
    if printer.console:
        printer.console.print(help_text)
    else:
        print(help_text)


def run_interactive_mode():
    printer.print_banner()
    show_help()

    while True:
        try:
            if printer.console:
                user_input = printer.console.input("[bold cyan]memorize › [/bold cyan]").strip()
            else:
                user_input = input("memorize › ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q", "/exit", "/quit"):
                printer.print_info("Goodbye!")
                break

            if user_input.lower() in ("/help", "help"):
                show_help()
                continue

            if user_input.lower() in ("/settings", "settings"):
                handle_settings()
                continue

            if user_input.startswith("/settings "):
                parts = user_input[10:].strip().split(maxsplit=1)
                k = parts[0]
                v = parts[1] if len(parts) > 1 else None
                handle_settings(key=k, value=v)
                continue

            if user_input.lower() in ("/create", "create"):
                if printer.console:
                    t = printer.console.input("[bold yellow]Memory Title: [/bold yellow]").strip()
                    c = printer.console.input("[bold yellow]Content (optional): [/bold yellow]").strip()
                    cat = printer.console.input("[bold yellow]Category (default: personal): [/bold yellow]").strip() or "personal"
                    tg = printer.console.input("[bold yellow]Tags (comma-separated): [/bold yellow]").strip()
                else:
                    t = input("Memory Title: ").strip()
                    c = input("Content (optional): ").strip()
                    cat = input("Category (default: personal): ").strip() or "personal"
                    tg = input("Tags (comma-separated): ").strip()
                tags_list = [x.strip() for x in tg.split(",") if x.strip()] if tg else []
                handle_create(title=t, content=c, category=cat, tags=tags_list)
                continue

            if user_input.startswith("/create "):
                t = user_input[8:].strip()
                handle_create(title=t)
                continue

            if user_input.lower() in ("/list", "list"):
                handle_list()
                continue

            if user_input.startswith("/list "):
                cat = user_input[6:].strip()
                handle_list(category=cat)
                continue

            if user_input.startswith("/search "):
                q = user_input[8:].strip()
                handle_search(query=q)
                continue

            if user_input.startswith("/read "):
                mem_id = user_input[6:].strip()
                handle_read(memory_id_or_path=mem_id)
                continue

            if user_input.startswith("/delete "):
                mem_id = user_input[8:].strip()
                handle_delete(memory_id=mem_id)
                continue

            if user_input.startswith("/revert "):
                parts = user_input[8:].strip().split()
                mem_id = parts[0]
                ver = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                handle_revert(memory_id=mem_id, version=ver)
                continue

            if user_input in ("/audit", "audit"):
                report = audit_storage_integrity(auto_fix=False)
                printer.print_audit_report(report)
                continue

            if user_input in ("/recover", "recover"):
                handle_recover_orphans()
                continue

            # Standard chat input
            handle_chat(message=user_input)

        except KeyboardInterrupt:
            printer.print_info("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            printer.print_error(str(e))

