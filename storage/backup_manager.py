import os
import shutil
from pathlib import Path
from typing import Dict, Any, Union

from config.constants import BACKUP_MEMORIES_DIR, MEMORIES_DIR
from core.logger import handle_errors, logger


@handle_errors
def backup_single_memory_file(file_path: Union[str, Path]) -> bool:
    """
    Backs up a single Markdown file to BACKUP_MEMORIES_DIR while preserving category folder structure.
    """
    file_path = Path(file_path)
    if not file_path.exists() or not file_path.name.endswith(".md"):
        return False

    try:
        rel_path = file_path.relative_to(MEMORIES_DIR)
    except ValueError:
        rel_path = Path(file_path.parent.name) / file_path.name

    target_backup_path = BACKUP_MEMORIES_DIR / rel_path
    target_backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, target_backup_path)
    logger.info(f"Backed up memory file: {rel_path} -> {target_backup_path}")
    return True


@handle_errors
def delete_single_backup_file(file_path: Union[str, Path]) -> bool:
    """
    Removes the backup file when a memory is explicitly deleted.
    """
    file_path = Path(file_path)
    try:
        rel_path = file_path.relative_to(MEMORIES_DIR)
    except ValueError:
        rel_path = Path(file_path.parent.name) / file_path.name

    target_backup_path = BACKUP_MEMORIES_DIR / rel_path
    if target_backup_path.exists():
        target_backup_path.unlink()
        logger.info(f"Deleted memory backup: {target_backup_path}")
        return True
    return False


@handle_errors
def backup_all_memories() -> Dict[str, Any]:
    """
    Scans data/memories/ and backs up all Markdown files into data/backups/memories/.
    """
    if not MEMORIES_DIR.exists():
        return {"status": "success", "backed_up_count": 0}

    backed_up_count = 0
    for root, _, files in os.walk(MEMORIES_DIR):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                full_path = Path(root) / file
                if backup_single_memory_file(full_path):
                    backed_up_count += 1

    return {"status": "success", "backed_up_count": backed_up_count}


@handle_errors
def restore_memories_from_backup() -> Dict[str, Any]:
    """
    Restores any missing Markdown memory files from data/backups/memories/ into data/memories/.
    """
    if not BACKUP_MEMORIES_DIR.exists():
        return {"status": "success", "restored_count": 0}

    restored_count = 0
    for root, _, files in os.walk(BACKUP_MEMORIES_DIR):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                backup_file_path = Path(root) / file
                try:
                    rel_path = backup_file_path.relative_to(BACKUP_MEMORIES_DIR)
                except ValueError:
                    continue

                target_mem_path = MEMORIES_DIR / rel_path
                if not target_mem_path.exists():
                    target_mem_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file_path, target_mem_path)
                    restored_count += 1
                    logger.info(f"Restored memory from backup: {rel_path}")

    return {"status": "success", "restored_count": restored_count}


@handle_errors
def clear_all_backups() -> bool:
    """
    Clears all backup Markdown files in BACKUP_MEMORIES_DIR.
    """
    if BACKUP_MEMORIES_DIR.exists():
        import shutil
        shutil.rmtree(BACKUP_MEMORIES_DIR)
        BACKUP_MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Cleared all memory backups.")
        return True
    return False
