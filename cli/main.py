import os
from pathlib import Path
import sys

# Ensure repository root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cli.commands import (

    handle_audit,
    handle_chat,
    handle_clean_orphans,
    handle_create,
    handle_delete,
    handle_list,
    handle_read,
    handle_recover_orphans,
    handle_revert,
    handle_search,
    handle_settings,
)
from cli.interactive import run_interactive_mode
from cli.parser import build_cli_parser
from core.logger import configure_cli_logging
from storage.db_manager import init_db


def main():
    configure_cli_logging()
    init_db()

    parser = build_cli_parser()
    args = parser.parse_args()

    has_action_flag = any([
        args.list, args.search, args.chat, args.create, args.settings, args.set_key,
        args.read, args.delete, args.revert, args.audit, args.clean_orphans, args.recover_orphans
    ])

    if has_action_flag:
        if args.settings or args.set_key:
            handle_settings(key=args.set_key, value=args.set_val)
        elif args.create:
            tags_list = [x.strip() for x in args.tags.split(",") if x.strip()] if args.tags else []
            handle_create(
                title=args.title or "",
                content=args.content or "",
                category=args.category or "personal",
                tags=tags_list,
            )
        elif args.list:
            handle_list(category=args.category, tag=args.tag)
        elif args.search:
            handle_search(query=args.search, category=args.category)
        elif args.chat:
            handle_chat(message=args.chat)
        elif args.read:
            handle_read(memory_id_or_path=args.read)
        elif args.delete:
            handle_delete(memory_id=args.delete)
        elif args.revert:
            handle_revert(memory_id=args.revert, version=args.version)
        elif args.audit:
            handle_audit()
        elif args.clean_orphans:
            handle_clean_orphans()
        elif args.recover_orphans:
            handle_recover_orphans()
        return

    # Default to interactive mode
    run_interactive_mode()


if __name__ == "__main__":
    main()

