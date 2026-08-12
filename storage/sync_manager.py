from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.constants import MEMORIES_DIR
from core.hashing import compute_string_hash
from core.logger import handle_errors, logger
from storage.backup_manager import clear_all_backups
from storage.db_manager import (
    clear_all_index_memories,
    delete_memory_from_index,
    get_all_memories,
    get_memory_by_id,
    upsert_memory_index,
)
from storage.markdown_handler import create_markdown_file, read_markdown_file
from vector.vector_db import (
    delete_chunks_by_memory_id,
    get_chroma_client,
    get_or_create_collection,
)


@handle_errors
def clear_all_memories(clear_backups: bool = True) -> Dict[str, Any]:
    """
    Completely purges all memory Markdown files and directories in MEMORIES_DIR,
    re-initializes standard category folders, resets SQLite DB,
    clears ChromaDB vector store collection, and purges backups if clear_backups is True.
    """
    import shutil
    from config.constants import DEFAULT_CATEGORIES

    deleted_files = 0
    if MEMORIES_DIR.exists():
        for item in MEMORIES_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted_files += 1
            except Exception as e:
                logger.error(f"Error removing {item}: {e}")

    if clear_backups:
        clear_all_backups()

    # Re-initialize standard category subdirectories with .gitkeep
    for cat in DEFAULT_CATEGORIES:
        cat_dir = MEMORIES_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        gitkeep = cat_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    # Reset SQLite database
    clear_all_index_memories()

    # Clear ChromaDB vector database collection
    try:
        client = get_chroma_client()
        try:
            client.delete_collection(name="memories")
        except Exception:
            pass
        client.get_or_create_collection(name="memories")
    except Exception as e:
        logger.warning(f"Error resetting ChromaDB collection: {e}")

    return {
        "status": "success",
        "message": f"Successfully cleared memories directory, reset SQLite database, and purged ChromaDB vector store.",
        "deleted_files_count": deleted_files,
    }


@handle_errors
def get_memory_file_status(memory_id_or_path: str) -> Dict[str, Any]:
    """
    Finds a Markdown file by Memory ID or filepath and returns its exact status,
    parsed frontmatter, raw text, content hash, token count estimate, and sync status.
    """
    target_mem = get_memory_by_id(memory_id_or_path)

    target_path = None
    if target_mem:
        target_path = Path(target_mem["file_path"])
    else:
        path_candidate = Path(memory_id_or_path)
        if path_candidate.exists():
            target_path = path_candidate

    if not target_path or not target_path.exists():
        return {
            "status": "error",
            "message": f"Memory file or ID '{memory_id_or_path}' not found.",
            "exists": False,
        }

    frontmatter, content = read_markdown_file(target_path)
    content_hash = compute_string_hash(content)
    stat = target_path.stat()

    with open(target_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    est_tokens = len(content) // 4

    return {
        "status": "success",
        "exists": True,
        "file_path": str(target_path),
        "file_size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "memory_id": frontmatter.get("id", target_mem.get("id") if target_mem else None),
        "title": frontmatter.get("title", target_mem.get("title") if target_mem else target_path.stem),
        "category": frontmatter.get("category", target_mem.get("category") if target_mem else None),
        "tags": frontmatter.get("tags", target_mem.get("tags") if target_mem else []),
        "created_at": frontmatter.get("created_at"),
        "updated_at": frontmatter.get("updated_at"),
        "content_hash": content_hash,
        "estimated_tokens": est_tokens,
        "is_indexed": target_mem is not None and target_mem.get("content_hash") == content_hash,
        "frontmatter": frontmatter,
        "content": content,
        "raw_file_text": raw_text,
    }


def _gather_disk_memory_ids() -> Dict[str, Dict[str, Any]]:
    """
    Walks data/memories/ and reads YAML frontmatter from every .md file.
    Returns dict mapping memory_id -> {file_path, title, category, tags, content, content_hash}.
    """
    disk_memories: Dict[str, Dict[str, Any]] = {}
    if not MEMORIES_DIR.exists():
        return disk_memories

    for md_file in MEMORIES_DIR.rglob("*.md"):
        if md_file.name.startswith("."):
            continue
        try:
            result = read_markdown_file(md_file)
            if isinstance(result, dict) and result.get("status") == "error":
                continue
            frontmatter, content = result
            mem_id = frontmatter.get("id")
            if mem_id:
                disk_memories[mem_id] = {
                    "file_path": str(md_file),
                    "title": frontmatter.get("title", md_file.stem),
                    "category": frontmatter.get("category", md_file.parent.name),
                    "tags": frontmatter.get("tags", []),
                    "content": content,
                    "content_hash": compute_string_hash(content),
                }
        except Exception as e:
            logger.warning(f"Audit: Error reading disk file {md_file}: {e}")

    return disk_memories


def _gather_chroma_memory_ids() -> Dict[str, List[str]]:
    """
    Scans ChromaDB for all unique memory_id values and their associated chunk_ids.
    Returns dict mapping memory_id -> [chunk_id1, chunk_id2, ...].
    """
    chroma_map: Dict[str, List[str]] = {}
    try:
        collection = get_or_create_collection("memories")
        total = collection.count()
        if total == 0:
            return chroma_map

        # Fetch all items in batches
        batch_size = 500
        offset = 0
        while offset < total:
            data = collection.get(
                limit=batch_size,
                offset=offset,
                include=["metadatas"],
            )
            if not data or not data.get("ids"):
                break

            for chunk_id, meta in zip(data["ids"], data["metadatas"]):
                mem_id = (meta or {}).get("memory_id", "")
                if mem_id:
                    if mem_id not in chroma_map:
                        chroma_map[mem_id] = []
                    chroma_map[mem_id].append(chunk_id)

            offset += batch_size

    except Exception as e:
        logger.warning(f"Audit: Error scanning ChromaDB: {e}")

    return chroma_map


@handle_errors
def audit_storage_integrity(
    auto_fix: bool = False,
    recover: bool = False,
) -> Dict[str, Any]:
    """
    Performs a three-way integrity audit across Markdown files, SQLite DB,
    and ChromaDB vector store. Detects orphaned records in each direction.

    Modes:
      - Default (auto_fix=False, recover=False): Report only.
      - auto_fix=True: Delete ghost SQLite/ChromaDB entries, re-index unindexed files.
      - recover=True: Reconstruct missing .md files from SQLite content column.
    """
    from core.memory_service import reindex_memory_chunks

    # ── Step 1: Gather IDs from all three sources ──
    sqlite_memories = get_all_memories()
    sqlite_map = {m["id"]: m for m in sqlite_memories}
    sqlite_ids = set(sqlite_map.keys())

    disk_map = _gather_disk_memory_ids()
    disk_ids = set(disk_map.keys())

    chroma_map = _gather_chroma_memory_ids()
    chroma_ids = set(chroma_map.keys())

    # ── Step 2: Detect orphans ──

    # 2a. Ghost SQLite entries: in SQLite but no file on disk
    ghost_sqlite = []
    for mem_id in sqlite_ids - disk_ids:
        entry = sqlite_map[mem_id]
        ghost_sqlite.append({
            "memory_id": mem_id,
            "title": entry.get("title", ""),
            "category": entry.get("category", ""),
            "file_path": entry.get("file_path", ""),
            "has_content_in_db": bool(entry.get("content")),
            "has_chroma_chunks": mem_id in chroma_ids,
        })

    # 2b. Ghost ChromaDB chunks: in ChromaDB but no SQLite record
    ghost_chroma = []
    for mem_id in chroma_ids - sqlite_ids:
        ghost_chroma.append({
            "memory_id": mem_id,
            "chunk_count": len(chroma_map[mem_id]),
            "chunk_ids": chroma_map[mem_id][:5],  # show first 5
            "has_disk_file": mem_id in disk_ids,
        })

    # 2c. Unindexed disk files: on disk but no SQLite record
    unindexed_files = []
    for mem_id in disk_ids - sqlite_ids:
        info = disk_map[mem_id]
        unindexed_files.append({
            "memory_id": mem_id,
            "title": info["title"],
            "category": info["category"],
            "file_path": info["file_path"],
            "has_chroma_chunks": mem_id in chroma_ids,
        })

    # 2d. Stale content hashes: in both SQLite and disk, but hashes diverge
    stale_hashes = []
    for mem_id in sqlite_ids & disk_ids:
        sqlite_hash = sqlite_map[mem_id].get("content_hash", "")
        disk_hash = disk_map[mem_id].get("content_hash", "")
        if sqlite_hash and disk_hash and sqlite_hash != disk_hash:
            stale_hashes.append({
                "memory_id": mem_id,
                "title": sqlite_map[mem_id].get("title", ""),
                "sqlite_hash": sqlite_hash[:16] + "...",
                "disk_hash": disk_hash[:16] + "...",
            })

    is_healthy = (
        len(ghost_sqlite) == 0
        and len(ghost_chroma) == 0
        and len(unindexed_files) == 0
        and len(stale_hashes) == 0
    )

    # ── Step 3: Actions ──
    actions_taken = []

    if auto_fix:
        # 3a. Delete ghost SQLite entries (no file to back them)
        for item in ghost_sqlite:
            mem_id = item["memory_id"]
            if not recover or not item["has_content_in_db"]:
                delete_memory_from_index(mem_id)
                if mem_id in chroma_ids:
                    delete_chunks_by_memory_id(mem_id)
                actions_taken.append(f"Deleted ghost SQLite entry + ChromaDB chunks: {mem_id}")

        # 3b. Delete ghost ChromaDB chunks (no SQLite record)
        for item in ghost_chroma:
            mem_id = item["memory_id"]
            if not item["has_disk_file"]:
                delete_chunks_by_memory_id(mem_id)
                actions_taken.append(f"Deleted orphaned ChromaDB chunks: {mem_id} ({item['chunk_count']} chunks)")

        # 3c. Re-index unindexed disk files into SQLite + ChromaDB
        for item in unindexed_files:
            mem_id = item["memory_id"]
            info = disk_map[mem_id]
            content = info["content"]

            chunks, chunk_ids = reindex_memory_chunks(mem_id, content)
            memory_entry = {
                "id": mem_id,
                "title": info["title"],
                "category": info["category"],
                "tags": info["tags"],
                "file_path": info["file_path"],
                "content": content,
                "content_hash": info["content_hash"],
                "chunk_ids": chunk_ids,
            }
            upsert_memory_index(memory_entry)
            actions_taken.append(f"Re-indexed unindexed disk file: {mem_id} ({info['title']})")

        # 3d. Rehash stale entries (re-read file, update SQLite)
        for item in stale_hashes:
            mem_id = item["memory_id"]
            info = disk_map[mem_id]
            content = info["content"]

            chunks, chunk_ids = reindex_memory_chunks(mem_id, content)
            existing = sqlite_map[mem_id]
            memory_entry = {
                "id": mem_id,
                "title": existing.get("title", info["title"]),
                "category": existing.get("category", info["category"]),
                "tags": existing.get("tags", info["tags"]),
                "file_path": info["file_path"],
                "content": content,
                "content_hash": info["content_hash"],
                "chunk_ids": chunk_ids,
            }
            upsert_memory_index(memory_entry)
            actions_taken.append(f"Rehashed stale entry: {mem_id}")

    if recover:
        # 3e. Reconstruct missing .md files from SQLite content
        for item in ghost_sqlite:
            mem_id = item["memory_id"]
            if item["has_content_in_db"]:
                entry = sqlite_map[mem_id]
                content = entry.get("content", "")
                title = entry.get("title", "Recovered Memory")
                category = entry.get("category", "personal")
                tags = entry.get("tags", [])
                content_hash = compute_string_hash(content)

                recovered_path = create_markdown_file(
                    memory_id=mem_id,
                    title=title,
                    category=category,
                    tags=tags,
                    content=content,
                    content_hash=content_hash,
                    created_at=entry.get("created_at", ""),
                    overwrite=False,
                )

                # Re-index vector chunks if missing
                if mem_id not in chroma_ids:
                    reindex_memory_chunks(mem_id, content)

                # Update file_path in SQLite to point to recovered file
                entry["file_path"] = str(recovered_path)
                entry["content_hash"] = content_hash
                upsert_memory_index(entry)

                actions_taken.append(
                    f"Recovered .md file from SQLite: {mem_id} ({title}) -> {recovered_path}"
                )

    report = {
        "status": "success",
        "is_healthy": is_healthy and not actions_taken,
        "summary": {
            "total_sqlite_records": len(sqlite_ids),
            "total_disk_files": len(disk_ids),
            "total_chroma_memory_ids": len(chroma_ids),
        },
        "orphans": {
            "ghost_sqlite_entries": ghost_sqlite,
            "ghost_chroma_chunks": ghost_chroma,
            "unindexed_disk_files": unindexed_files,
            "stale_content_hashes": stale_hashes,
        },
        "orphan_counts": {
            "ghost_sqlite": len(ghost_sqlite),
            "ghost_chroma": len(ghost_chroma),
            "unindexed_files": len(unindexed_files),
            "stale_hashes": len(stale_hashes),
        },
        "actions_taken": actions_taken,
        "auto_fix_enabled": auto_fix,
        "recover_enabled": recover,
    }

    if is_healthy and not actions_taken:
        logger.info("Storage integrity audit: All layers are in sync. ✅")
    else:
        total_orphans = len(ghost_sqlite) + len(ghost_chroma) + len(unindexed_files) + len(stale_hashes)
        logger.warning(f"Storage integrity audit: Found {total_orphans} orphan(s). Actions taken: {len(actions_taken)}.")

    return report
