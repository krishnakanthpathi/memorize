from cli.commands import (
    handle_create,
    handle_delete,
    handle_list,
    handle_purge_orphans,
    handle_read,
    handle_recover_orphans,
    handle_revert,
    handle_search,
    handle_settings,
    handle_sync,
)
from cli.printer import printer
from storage.sync_manager import audit_storage_integrity


def show_help():
    help_text = (
        "\n[bold orange1]Available CLI Commands:[/bold orange1] [dim](commands work with or without leading '/')[/dim]\n\n"
        "  [bold bright_white]📁 Memory Operations[/bold bright_white]\n\n"
        "    [bold orange1]/list \\[category][/bold orange1]          [dim white]- List memories (optional category filter)[/dim white]\n"
        "    [bold orange1]/search <query>[/bold orange1]           [dim white]- Hybrid search across stored memories[/dim white]\n"
        "    [bold orange1]/create \\[title][/bold orange1]           [dim white]- Create a new memory interactively[/dim white]\n"
        "                              [dim yellow]Parameters: title, content, category, tags[/dim yellow]\n"
        "    [bold orange1]/read <memory_id>[/bold orange1]         [dim white]- View memory document content and status[/dim white]\n"
        "    [bold orange1]/delete <memory_id>[/bold orange1]       [dim white]- Delete memory by ID[/dim white]\n"
        "    [bold orange1]/reset[/bold orange1]                    [dim white]- Clear ALL stored memories (with confirmation)[/dim white]\n"
        "    [bold orange1]/revert <id> \\[ver][/bold orange1]        [dim white]- Revert memory to a previous version[/dim white]\n\n"
        "  [bold bright_white]⚙️  System & Diagnostics[/bold bright_white]\n\n"
        "    [bold orange1]/settings \\[key] \\[val][/bold orange1]    [dim white]- View or update configuration settings[/dim white]\n"
        "    [bold orange1]/prompts \\[key][/bold orange1]          [dim white]- View LLM system prompts & templates[/dim white]\n"
        "    [bold orange1]/endpoints[/bold orange1]                [dim white]- View all backend REST API routes & URLs[/dim white]\n"
        "    [bold orange1]/audit[/bold orange1]                    [dim white]- Run storage integrity & orphan audit[/dim white]\n"
        "    [bold orange1]/recover[/bold orange1]                  [dim white]- Recover unindexed files & generate IDs[/dim white]\n"
        "    [bold orange1]/purge[/bold orange1]                    [dim white]- Purge dead DB records & orphan chunks[/dim white]\n"
        "    [bold orange1]/sync[/bold orange1]                     [dim white]- Auto-repair & reconcile all storage systems[/dim white]\n"
        "    [bold orange1]/clear[/bold orange1]                    [dim white]- Clear the terminal screen[/dim white]\n"
        "    [bold orange1]/help[/bold orange1]                     [dim white]- Show this help message[/dim white]\n"
        "    [bold orange1]/exit[/bold orange1]                     [dim white]- Exit shell[/dim white]\n"
    )
    printer.console.print(help_text)


def run_interactive_mode():
    from core.logger import configure_cli_logging
    configure_cli_logging()
    printer.print_banner()
    show_help()

    while True:
        try:
            user_input = printer.console.input("[bold orange1]memorize› [/bold orange1]").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q", "/exit", "/quit"):
                printer.print_info("Goodbye!")
                break

            if user_input.lower() in ("/clear", "clear", "cls", "/cls"):
                printer.console.clear()
                printer.print_banner()
                continue

            if user_input.lower() in ("/help", "help"):
                show_help()
                continue

            if user_input.lower() in ("/settings", "settings"):
                handle_settings()
                continue

            if user_input.startswith(("/settings ", "settings ")):
                prefix_len = 10 if user_input.startswith("/settings ") else 9
                parts = user_input[prefix_len:].strip().split(maxsplit=1)
                k = parts[0]
                v = parts[1] if len(parts) > 1 else None
                handle_settings(key=k, value=v)
                continue

            if user_input.lower() in ("/prompts", "prompts"):
                printer.print_prompts_panel()
                continue

            if user_input.startswith(("/prompts ", "prompts ")):
                prefix_len = 9 if user_input.startswith("/prompts ") else 8
                p_key = user_input[prefix_len:].strip()
                printer.print_prompts_panel(prompt_name=p_key)
                continue

            if user_input.lower() in ("/create", "create"):
                t = printer.console.input("[bold yellow]Memory Title: [/bold yellow]").strip()
                c = printer.console.input("[bold yellow]Content (optional): [/bold yellow]").strip()
                cat = printer.console.input("[bold yellow]Category (default: personal): [/bold yellow]").strip() or "personal"
                tg = printer.console.input("[bold yellow]Tags (comma-separated): [/bold yellow]").strip()
                tags_list = [x.strip() for x in tg.split(",") if x.strip()] if tg else []
                handle_create(title=t, content=c, category=cat, tags=tags_list)
                continue

            if user_input.startswith(("/create ", "create ")):
                prefix_len = 8 if user_input.startswith("/create ") else 7
                title = user_input[prefix_len:].strip()
                c = printer.console.input("[bold yellow]Content (optional): [/bold yellow]").strip()
                cat = printer.console.input("[bold yellow]Category (default: personal): [/bold yellow]").strip() or "personal"
                tg = printer.console.input("[bold yellow]Tags (comma-separated): [/bold yellow]").strip()
                tags_list = [x.strip() for x in tg.split(",") if x.strip()] if tg else []
                handle_create(title=title, content=c, category=cat, tags=tags_list)
                continue

            if user_input.lower() in ("/list", "list"):
                handle_list()
                continue

            if user_input.startswith(("/list ", "list ")):
                prefix_len = 6 if user_input.startswith("/list ") else 5
                cat = user_input[prefix_len:].strip()
                handle_list(category=cat)
                continue

            if user_input.startswith(("/search ", "search ")):
                prefix_len = 8 if user_input.startswith("/search ") else 7
                q = user_input[prefix_len:].strip()
                handle_search(query=q)
                continue

            if user_input.lower() in ("/reset", "reset"):
                from cli.commands import handle_clear_all
                handle_clear_all()
                continue

            if user_input.startswith(("/read ", "read ")):
                prefix_len = 6 if user_input.startswith("/read ") else 5
                mid = user_input[prefix_len:].strip()
                handle_read(memory_id_or_path=mid)
                continue

            if user_input.startswith(("/delete ", "delete ")):
                prefix_len = 8 if user_input.startswith("/delete ") else 7
                mid = user_input[prefix_len:].strip()
                handle_delete(memory_id=mid)
                continue

            if user_input.startswith(("/revert ", "revert ")):
                prefix_len = 8 if user_input.startswith("/revert ") else 7
                parts = user_input[prefix_len:].strip().split()
                mem_id = parts[0]
                ver = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                handle_revert(memory_id=mem_id, version=ver)
                continue

            if user_input.lower() in ("/endpoints", "endpoints", "/routes", "routes", "/api", "api"):
                printer.print_endpoints_panel()
                continue

            if user_input.lower() in ("/audit", "audit", "/aduit", "aduit", "/status", "status"):
                report = audit_storage_integrity(auto_fix=False)
                printer.print_audit_report(report)
                continue

            if user_input.lower() in ("/recover", "recover", "/recovery", "recovery"):
                handle_recover_orphans()
                continue

            if user_input.lower() in ("/purge", "purge", "/clean", "clean"):
                handle_purge_orphans()
                continue

            if user_input.lower() in ("/sync", "sync", "/autofix", "autofix", "/fix", "fix"):
                handle_sync()
                continue

            # If user entered an unrecognized command or plain text
            printer.print_error(f"Unrecognized input '{user_input}'. Type [bold orange1]/help[/bold orange1] to view available commands.")

        except KeyboardInterrupt:
            printer.print_info("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            printer.print_error(str(e))
