import argparse


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Memorize CLI & Storage Integrity Assistant")
    parser.add_argument("--list", "-l", action="store_true", help="List stored memories")
    parser.add_argument("--category", "-c", type=str, help="Category filter for list/search/create")
    parser.add_argument("--tag", "-t", type=str, help="Tag filter for list")
    parser.add_argument("--search", "-s", type=str, help="Search query string")
    parser.add_argument("--create", "-crt", action="store_true", help="Create a new memory (parameters: title: str, content: str = '', category: str = 'personal', tags: Optional[List[str]] = None)")
    parser.add_argument("--title", type=str, help="Title for memory creation (title: str)")
    parser.add_argument("--content", type=str, help="Content for memory creation (content: str = '')")
    parser.add_argument("--tags", type=str, help="Comma-separated tags for memory creation (tags: Optional[List[str]] = None)")
    parser.add_argument("--settings", "-set", action="store_true", help="Display CLI engine settings panel")
    parser.add_argument("--set-key", type=str, help="Setting key to update")
    parser.add_argument("--set-val", type=str, help="Setting value to set")
    parser.add_argument("--read", type=str, help="Read memory file status by ID or path")
    parser.add_argument("--delete", type=str, help="Delete memory by ID")
    parser.add_argument("--revert", type=str, help="Revert memory ID to previous version")
    parser.add_argument("--version", type=int, help="Version number for revert operation")
    parser.add_argument("--audit", action="store_true", help="Run storage integrity audit report")
    parser.add_argument("--clean-orphans", action="store_true", help="Delete orphan files, indexes, and vector chunks")
    parser.add_argument("--recover-orphans", action="store_true", help="Recover unindexed files & chunks, generating unique IDs")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive shell mode")
    return parser
