from datetime import datetime, timezone
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Union

import config.constants as constants
from config.settings import get_memories_dir
from core.hashing import compute_file_hash
from core.logger import handle_errors, logger
from storage.db_manager import (
    get_latest_backup_readme_from_db,
    log_backup_record,
    save_backup_readme_to_db,
)


@handle_errors
def backup_single_memory_file(file_path: Union[str, Path]) -> bool:
    """
    Backs up a single Markdown file to BACKUP_MEMORIES_DIR while preserving category folder structure
    and logs the backup event into the SQLite database.
    """
    file_path = Path(file_path)
    if not file_path.exists() or not file_path.name.endswith(".md"):
        return False

    mem_dir = get_memories_dir()
    backup_mem_dir = constants.BACKUP_MEMORIES_DIR

    try:
        rel_path = file_path.relative_to(mem_dir)
    except ValueError:
        rel_path = Path(file_path.parent.name) / file_path.name

    target_backup_path = backup_mem_dir / rel_path
    target_backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, target_backup_path)

    content_hash = compute_file_hash(file_path)
    category = rel_path.parent.name if rel_path.parent.name != "." else "personal"
    title = file_path.stem.replace("_", " ").title()

    # Attempt to extract frontmatter memory_id if readable
    memory_id = file_path.stem
    try:
        from storage.markdown_handler import read_markdown_file
        fm, _ = read_markdown_file(file_path)
        if fm.get("id"):
            memory_id = fm["id"]
        if fm.get("title"):
            title = fm["title"]
        if fm.get("category"):
            category = fm["category"]
    except Exception:
        pass

    log_backup_record(
        memory_id=memory_id,
        title=title,
        category=category,
        file_path=str(file_path),
        backup_path=str(target_backup_path),
        content_hash=content_hash,
    )

    logger.info(f"Backed up memory file: {rel_path} -> {target_backup_path}")
    return True


@handle_errors
def backup_database_snapshot() -> bool:
    """
    Creates a snapshot backup of the SQLite database (memorize.db) in data/backups/memorize_backup.db.
    """
    db_path = constants.DB_PATH
    backup_dir = constants.BACKUP_DIR
    if not db_path.exists():
        return False

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_db_path = backup_dir / "memorize_backup.db"
    try:
        import sqlite3
        conn_src = sqlite3.connect(str(db_path))
        conn_dst = sqlite3.connect(str(backup_db_path))
        with conn_dst:
            conn_src.backup(conn_dst)
        conn_src.close()
        conn_dst.close()
        logger.info(f"Backed up SQLite database snapshot to: {backup_db_path}")
        return True
    except Exception as e:
        logger.warning(f"Database online backup failed: {e}. Falling back to copy.")
        shutil.copy2(db_path, backup_db_path)
        return True


@handle_errors
def generate_backup_readme() -> str:
    """
    Generates a comprehensive README.txt snapshot summarizing all backed up memory files,
    category breakdowns, and backup metadata. Writes README.txt to data/backups/ and SQLite database.
    """
    backup_mem_dir = constants.BACKUP_MEMORIES_DIR
    backup_dir = constants.BACKUP_DIR
    if not backup_mem_dir.exists():
        backup_mem_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    categories_dict: Dict[str, list] = {}
    total_files = 0

    for root, _, files in os.walk(backup_mem_dir):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                full_path = Path(root) / file
                rel = full_path.relative_to(backup_mem_dir)
                cat = rel.parent.name if rel.parent.name != "." else "personal"
                if cat not in categories_dict:
                    categories_dict[cat] = []
                categories_dict[cat].append({
                    "name": file,
                    "rel_path": str(rel),
                    "size_bytes": full_path.stat().st_size,
                })
                total_files += 1

    lines = [
        "================================================================================",
        "                       MEMORIZE BACKUP REPOSITORY INDEX                        ",
        "================================================================================",
        f"Backup Timestamp : {timestamp}",
        f"Database File    : data/backups/memorize_backup.db",
        f"Total Files      : {total_files} Markdown memories backed up",
        "================================================================================",
        "",
        "CATEGORY BREAKDOWN & INVENTORY:",
        "--------------------------------------------------------------------------------",
    ]

    for cat in sorted(categories_dict.keys()):
        files_in_cat = categories_dict[cat]
        lines.append(f"📁 Category: [{cat.upper()}] ({len(files_in_cat)} memories)")
        for item in sorted(files_in_cat, key=lambda x: x["name"]):
            lines.append(f"   - {item['rel_path']} ({item['size_bytes']} bytes)")
        lines.append("")

    lines.extend([
        "--------------------------------------------------------------------------------",
        "RECOVERY INSTRUCTIONS:",
        "1. To restore memory files automatically: run restore_memories_from_backup().",
        "2. If SQLite database is lost, restoring memory files will auto-index all frontmatter & content.",
        "3. SQLite backup copy is maintained at data/backups/memorize_backup.db.",
        "================================================================================",
    ])

    readme_content = "\n".join(lines)
    readme_path = backup_dir / "README.txt"
    backup_dir.mkdir(parents=True, exist_ok=True)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    save_backup_readme_to_db(readme_content, total_files)
    logger.info(f"Generated backup README.txt snapshot at {readme_path}")
    return readme_content


@handle_errors
def delete_single_backup_file(file_path: Union[str, Path]) -> bool:
    """
    Removes the backup file when a memory is explicitly deleted.
    """
    file_path = Path(file_path)
    mem_dir = get_memories_dir()
    backup_mem_dir = constants.BACKUP_MEMORIES_DIR

    try:
        rel_path = file_path.relative_to(mem_dir)
    except ValueError:
        rel_path = Path(file_path.parent.name) / file_path.name

    target_backup_path = backup_mem_dir / rel_path
    if target_backup_path.exists():
        target_backup_path.unlink()
        logger.info(f"Deleted memory backup: {target_backup_path}")
        return True
    return False


@handle_errors
def backup_all_memories() -> Dict[str, Any]:
    """
    Scans data/memories/, backs up all Markdown files into data/backups/memories/,
    snapshots memorize.db into data/backups/memorize_backup.db, and generates README.txt.
    """
    mem_dir = get_memories_dir()
    if not mem_dir.exists():
        return {"status": "success", "backed_up_count": 0}

    backed_up_count = 0
    for root, _, files in os.walk(mem_dir):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                full_path = Path(root) / file
                if backup_single_memory_file(full_path):
                    backed_up_count += 1

    db_backed_up = backup_database_snapshot()
    readme_content = generate_backup_readme()

    return {
        "status": "success",
        "backed_up_count": backed_up_count,
        "database_snapshot": db_backed_up,
        "readme_generated": True,
    }


@handle_errors
def restore_memories_from_backup() -> Dict[str, Any]:
    """
    Restores any missing Markdown memory files from data/backups/memories/ into data/memories/.
    """
    mem_dir = get_memories_dir()
    backup_mem_dir = constants.BACKUP_MEMORIES_DIR
    if not backup_mem_dir.exists():
        return {"status": "success", "restored_count": 0}

    restored_count = 0
    for root, _, files in os.walk(backup_mem_dir):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                backup_file_path = Path(root) / file
                try:
                    rel_path = backup_file_path.relative_to(backup_mem_dir)
                except ValueError:
                    continue

                target_mem_path = mem_dir / rel_path
                if not target_mem_path.exists():
                    target_mem_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file_path, target_mem_path)
                    restored_count += 1
                    logger.info(f"Restored memory from backup: {rel_path}")

    return {"status": "success", "restored_count": restored_count}


@handle_errors
def clear_all_backups() -> bool:
    """
    Clears all backup Markdown files, database snapshots, README files, and DB records.
    """
    from storage.db_manager import clear_all_backup_records_from_db
    clear_all_backup_records_from_db()

    backup_dir = constants.BACKUP_DIR
    backup_mem_dir = constants.BACKUP_MEMORIES_DIR

    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        backup_mem_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cleared all memory backups, snapshots, and README files.")
        return True
    return False



@handle_errors
def get_backup_readme() -> str:
    """
    Retrieves the backup README.txt text summary from disk or SQLite database.
    """
    readme_path = constants.BACKUP_DIR / "README.txt"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()

    db_rec = get_latest_backup_readme_from_db()
    if db_rec:
        return db_rec.get("readme_text", "")

    return generate_backup_readme()

