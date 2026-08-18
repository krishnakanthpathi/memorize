from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from core.hashing import compute_string_hash
from core.logger import handle_errors, logger
from storage.backup_manager import backup_single_memory_file, delete_single_backup_file
from utils import get_category_dir


@handle_errors
def normalize_title(title: str) -> str:
    """
    Normalizes a title string by removing duplicate contiguous words/phrases or redundant prefixes.
    Example: 'User Profile - User Profile Krishnakanth' -> 'User Profile - Krishnakanth'
    """
    if not title:
        return "Untitled Memory"

    clean_title = re.sub(r"\s+", " ", title.strip())
    # Separate symbols with spaces for tokenization
    tokens = re.findall(r"\w+|[^\w\s]", clean_title)

    # Deduplicate consecutive repeating word n-grams (n from 4 down to 1)
    i = 0
    new_tokens = []
    while i < len(tokens):
        matched_n = 0
        max_n = min(4, (len(tokens) - i) // 2)
        for n in range(max_n, 0, -1):
            pattern = [t.lower() for t in tokens[i : i + n]]
            next_pattern = [t.lower() for t in tokens[i + n : i + 2 * n]]
            if pattern == next_pattern:
                matched_n = n
                break

        if matched_n > 0:
            new_tokens.extend(tokens[i : i + matched_n])
            pattern = [t.lower() for t in tokens[i : i + matched_n]]
            i += 2 * matched_n
            while i + matched_n <= len(tokens):
                next_check = [t.lower() for t in tokens[i : i + matched_n]]
                if next_check == pattern:
                    i += matched_n
                else:
                    break
        else:
            new_tokens.append(tokens[i])
            i += 1

    # Reassemble text from tokens cleanly
    reassembled = ""
    for t in new_tokens:
        if not reassembled or t in "-:,!.?":
            reassembled += t
        else:
            reassembled += " " + t

    # Format with clean dashes if hyphenated/colonized
    parts = [p.strip() for p in re.split(r"[-:]+", reassembled) if p.strip()]
    deduped_parts = []
    seen = set()
    for part in parts:
        part_lower = part.lower()
        if part_lower not in seen:
            seen.add(part_lower)
            deduped_parts.append(part)

    if deduped_parts:
        return " - ".join(deduped_parts)
    return clean_title


@handle_errors
def title_to_slug(title: str) -> str:
    """
    Converts a title to a clean, safe slug string.
    Example: 'User Profile - User Profile Krishnakanth' -> 'user_profile_krishnakanth'
    """
    norm_title = normalize_title(title)
    clean = re.sub(r"[^\w\s-]", "", norm_title.lower())
    slug = re.sub(r"[-\s]+", "_", clean).strip("_")
    return slug if slug else "untitled_memory"


@handle_errors
def title_to_filename(title: str) -> str:
    """
    Converts a title string to a safe filename ending with .md.
    """
    slug = title_to_slug(title)
    return f"{slug}.md"


@handle_errors
def create_markdown_file(
    memory_id: str,
    title: str,
    category: str = "personal",
    tags: Optional[List[str]] = None,
    content: str = "",
    content_hash: str = "",
    created_at: str = "",
    updated_at: str = "",
    overwrite: bool = True,
    file_path: Optional[Union[Path, str]] = None,
) -> Path:
    """
    Builds YAML frontmatter + content body and writes a Markdown file to disk.
    Returns the absolute Path of the created file.
    """
    if tags is None:
        tags = []

    title = normalize_title(title)
    now_iso = datetime.now(timezone.utc).isoformat()
    if not created_at:
        created_at = now_iso
    if not updated_at:
        updated_at = now_iso
    if not content_hash:
        content_hash = compute_string_hash(content)

    category_dir = get_category_dir(category)

    if file_path:
        target_path = Path(file_path)
    else:
        filename = title_to_filename(title)
        target_path = category_dir / filename
        if target_path.exists():
            try:
                fm, _ = read_markdown_file(target_path)
                existing_fm_id = fm.get("id")
                if existing_fm_id and existing_fm_id != memory_id:
                    target_path = category_dir / f"{memory_id}_{filename}"
            except Exception:
                if not overwrite:
                    target_path = category_dir / f"{memory_id}_{filename}"

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

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    logger.info(f"Wrote Markdown memory file: {target_path}")
    backup_single_memory_file(target_path)
    return target_path


@handle_errors
def append_to_markdown_file(
    file_path: Union[Path, str],
    additional_content: str,
    tags: Optional[List[str]] = None,
) -> Tuple[Path, str, str]:
    """
    Appends new content to an existing Markdown memory file on disk.
    Updates frontmatter updated_at and content_hash.
    Returns (file_path, memory_id, updated_full_content).
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File to append does not exist: {path_obj}")

    frontmatter, existing_content = read_markdown_file(path_obj)
    memory_id = frontmatter.get("id", "")
    title = frontmatter.get("title", path_obj.stem.replace("_", " ").title())
    category = frontmatter.get("category", path_obj.parent.name)
    existing_tags = frontmatter.get("tags", [])

    if tags:
        combined_tags = list(set(existing_tags + tags))
    else:
        combined_tags = existing_tags

    now_iso = datetime.now(timezone.utc).isoformat()
    created_at = frontmatter.get("created_at", now_iso)

    timestamp_hdr = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_section = f"\n\n### Update ({timestamp_hdr})\n{additional_content.strip()}"
    updated_content = (existing_content + new_section).strip()

    updated_hash = compute_string_hash(updated_content)

    updated_path = create_markdown_file(
        memory_id=memory_id,
        title=title,
        category=category,
        tags=combined_tags,
        content=updated_content,
        content_hash=updated_hash,
        created_at=created_at,
        updated_at=now_iso,
        overwrite=True,
        file_path=path_obj,
    )

    return updated_path, memory_id, updated_content


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
        delete_single_backup_file(path_obj)
        return True
    return False
