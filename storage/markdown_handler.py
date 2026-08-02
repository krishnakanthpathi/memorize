import os
import re
from pathlib import Path
from typing import Any, Dict, Tuple, Union
import yaml

from config.constants import MEMORIES_CATEGORIES
from core.logger import logger, handle_errors


@handle_errors
def title_to_filename(title: str) -> str:
    """
    Converts a title string to a safe, clean filename.
    Example: 'Family Birthdays 2026!' -> 'family_birthdays_2026.md'
    """
    clean_title = re.sub(r"[^\w\s-]", "", title.lower())
    filename = re.sub(r"[-\s]+", "_", clean_title).strip("_")
    return f"{filename}.md" if filename else "untitled_memory.md"


@handle_errors
def create_markdown_file(
    memory_id: str,
    title: str,
    category: str,
    tags: list[str],
    content: str,
    content_hash: str,
    created_at: str,
    updated_at: str,
) -> Path:
    """
    Builds YAML frontmatter + content body and writes a Markdown file to disk.
    Returns the absolute Path of the created file.
    """
    category_dir = MEMORIES_CATEGORIES.get(category, MEMORIES_CATEGORIES["personal"])
    category_dir.mkdir(parents=True, exist_ok=True)

    filename = title_to_filename(title)
    file_path = category_dir / filename

    if file_path.exists():
        file_path = category_dir / f"{memory_id}_{filename}"

    frontmatter = {
        "id": memory_id,
        "title": title,
        "category": category,
        "tags": tags,
        "created_at": created_at,
        "updated_at": updated_at,
        "content_hash": content_hash,
    }

    yaml_block = yaml.dump(frontmatter, sort_keys=False).strip()
    full_text = f"---\n{yaml_block}\n---\n\n{content.strip()}\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    logger.info(f"Created Markdown memory file: {file_path}")
    return file_path


@handle_errors
def read_markdown_file(file_path: Union[Path, str]) -> Tuple[Dict[str, Any], str]:
    """
    Reads a Markdown file from disk and parses YAML frontmatter + content body.
    Accepts either a Path object or a string file path.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path

    if not path_obj.exists():
        raise FileNotFoundError(f"Markdown file does not exist: {path_obj}")

    with open(path_obj, "r", encoding="utf-8") as f:
        text = f.read()

    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, text, re.DOTALL)

    if not match:
        return {}, text.strip()

    frontmatter_str = match.group(1)
    content = match.group(2).strip()
    frontmatter = yaml.safe_load(frontmatter_str) or {}

    return frontmatter, content


@handle_errors
def delete_markdown_file(file_path: Union[Path, str]) -> bool:
    """
    Deletes a Markdown file from disk if it exists.
    Accepts either a Path object or a string file path.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path

    if path_obj.exists():
        path_obj.unlink()
        logger.info(f"Deleted Markdown memory file: {path_obj}")
        return True
    return False
