import os
from pathlib import Path
import tempfile


from storage.backup_manager import (
    backup_all_memories,
    clear_all_backups,
    generate_backup_readme,
    get_backup_readme,
)
from storage.db_manager import (
    clear_all_index_memories,
    get_all_memories,
    get_memory_by_id,
    init_db,
    upsert_memory_index,
)
from storage.markdown_handler import create_markdown_file
from storage.sync_manager import clear_all_memories, sync_markdown_files


def test_full_content_storage_in_sqlite():
    init_db()
    test_id = "mem_test_content_123"
    test_title = "Database Content Persistence Test"
    test_content = "This is a full content test body stored directly inside SQLite database."

    mem_entry = {
        "id": test_id,
        "title": test_title,
        "category": "development",
        "tags": ["test", "sqlite"],
        "file_path": "/tmp/test_content_123.md",
        "content": test_content,
        "content_hash": "dummyhash123",
    }

    upsert_memory_index(mem_entry)
    fetched = get_memory_by_id(test_id)

    assert fetched is not None
    assert fetched["id"] == test_id
    assert fetched["content"] == test_content


def test_auto_rematerialization_from_sqlite():
    clear_all_memories(clear_backups=True)

    test_id = "mem_test_rematerialize_456"
    test_title = "Vanished Memory File Recovery Test"
    test_content = "# Auto Rematerialize\nThis file was deleted on disk but lives in SQLite."

    # Create file and sync to SQLite DB
    created_path = create_markdown_file(
        memory_id=test_id,
        title=test_title,
        category="personal",
        tags=["rematerialize"],
        content=test_content,
    )
    sync_markdown_files()

    # Clear backup directory to ensure recovery comes strictly from SQLite DB
    clear_all_backups()

    # Simulate accidental disk file deletion ("vanished file")
    assert created_path.exists()
    created_path.unlink()
    assert not created_path.exists()

    # Trigger sync — system should auto-rematerialize file on disk from SQLite!
    sync_res = sync_markdown_files()
    assert sync_res["status"] == "success"
    assert sync_res["rematerialized"] >= 1
    assert created_path.exists()

    # Verify content restored on disk matches
    with open(created_path, "r", encoding="utf-8") as f:
        restored_text = f.read()
    assert test_content in restored_text

    # Cleanup
    clear_all_memories(clear_backups=True)



def test_backup_and_readme_generation():
    clear_all_memories(clear_backups=True)

    # Create sample memories
    create_markdown_file(
        memory_id="mem_bkp_1",
        title="Backup Test Achievement",
        category="achievements",
        tags=["award"],
        content="Won first place hackathon.",
    )
    create_markdown_file(
        memory_id="mem_bkp_2",
        title="Backup Test Dev Project",
        category="development",
        tags=["python"],
        content="Built high-performance async queue system.",
    )
    sync_markdown_files()

    backup_res = backup_all_memories()
    assert backup_res["status"] == "success"
    assert backup_res["backed_up_count"] >= 2
    assert backup_res["database_snapshot"] is True
    assert backup_res["readme_generated"] is True

    readme_text = get_backup_readme()
    assert "MEMORIZE BACKUP REPOSITORY INDEX" in readme_text
    assert "Category: [ACHIEVEMENTS]" in readme_text
    assert "Category: [DEVELOPMENT]" in readme_text

    clear_all_memories(clear_backups=True)
