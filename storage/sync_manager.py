from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from config.constants import MEMORIES_DIR
from core.hashing import compute_string_hash
from core.id_generator import generate_memory_id
from core.logger import handle_errors, logger
from storage.backup_manager import clear_all_backups
from storage.db_manager import (
    clear_all_index_memories,
    delete_memory_from_index,
    get_all_memories,
    get_memory_by_id,
)
from storage.markdown_handler import read_markdown_file
from vector.vector_db import (
    delete_chunks_by_ids,
    get_all_chunks,
    get_chroma_client,
)


@handle_errors
def find_orphan_files() -> List[Dict[str, Any]]:
    """
    Finds Markdown files on disk in MEMORIES_DIR that are not tracked in the SQLite database index.
    """
    db_memories = get_all_memories()
    indexed_paths = set()
    for mem in db_memories:
        if mem.get("file_path"):
            try:
                indexed_paths.add(Path(mem["file_path"]).resolve())
            except Exception:
                pass

    orphan_files = []
    if MEMORIES_DIR.exists():
        for path in MEMORIES_DIR.rglob("*.md"):
            if path.name.startswith(".") or path.name == ".gitkeep":
                continue
            resolved_path = path.resolve()
            if resolved_path not in indexed_paths:
                stat = path.stat()
                orphan_files.append({
                    "file_path": str(path),
                    "file_name": path.name,
                    "category": path.parent.name if path.parent != MEMORIES_DIR else "personal",
                    "file_size_bytes": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                })

    return orphan_files


@handle_errors
def find_orphan_indexes() -> List[Dict[str, Any]]:
    """
    Finds SQLite database records whose corresponding Markdown file does not exist on disk.
    """
    db_memories = get_all_memories()
    orphan_indexes = []
    for mem in db_memories:
        file_path_str = mem.get("file_path", "")
        if not file_path_str or not Path(file_path_str).exists():
            orphan_indexes.append({
                "memory_id": mem.get("id"),
                "title": mem.get("title"),
                "category": mem.get("category"),
                "file_path": file_path_str,
                "created_at": mem.get("created_at"),
            })
    return orphan_indexes


@handle_errors
def find_orphan_chunks() -> List[Dict[str, Any]]:
    """
    Finds ChromaDB vector chunk embeddings whose memory_id is not found in SQLite or on disk.
    """
    db_memories = get_all_memories()
    valid_memory_ids = {mem.get("id") for mem in db_memories if mem.get("id")}
    all_chunks = get_all_chunks()

    orphan_chunks = []
    for chunk in all_chunks:
        mem_id = chunk.get("memory_id")
        if not mem_id or mem_id not in valid_memory_ids:
            orphan_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "memory_id": mem_id,
                "category": chunk.get("category"),
            })
    return orphan_chunks


@handle_errors
def delete_orphan_files() -> Dict[str, Any]:
    """
    Deletes orphan Markdown files from disk.
    """
    orphans = find_orphan_files()
    deleted_paths = []
    failed_paths = []

    for orphan in orphans:
        path = Path(orphan["file_path"])
        try:
            if path.exists():
                path.unlink()
                deleted_paths.append(str(path))
        except Exception as e:
            logger.error(f"Failed to delete orphan file {path}: {e}")
            failed_paths.append(str(path))

    return {
        "status": "success",
        "deleted_count": len(deleted_paths),
        "deleted_files": deleted_paths,
        "failed_files": failed_paths,
    }


@handle_errors
def delete_orphan_indexes() -> Dict[str, Any]:
    """
    Deletes orphan records from the SQLite database index.
    """
    orphans = find_orphan_indexes()
    deleted_ids = []

    for orphan in orphans:
        mem_id = orphan.get("memory_id")
        if mem_id:
            if delete_memory_from_index(mem_id):
                deleted_ids.append(mem_id)

    return {
        "status": "success",
        "deleted_count": len(deleted_ids),
        "deleted_memory_ids": deleted_ids,
    }


@handle_errors
def delete_orphan_chunks() -> Dict[str, Any]:
    """
    Deletes orphan vector chunk embeddings from ChromaDB.
    """
    orphans = find_orphan_chunks()
    chunk_ids = [orphan["chunk_id"] for orphan in orphans if orphan.get("chunk_id")]

    if not chunk_ids:
        return {"status": "success", "deleted_count": 0, "deleted_chunk_ids": []}

    res = delete_chunks_by_ids(chunk_ids)
    return {
        "status": "success",
        "deleted_count": res.get("deleted_count", 0),
        "deleted_chunk_ids": chunk_ids,
    }


@handle_errors
def recover_orphaned_documents() -> Dict[str, Any]:
    """
    Scans unindexed Markdown files on disk, generates new IDs for documents missing IDs,
    indexes them in-place in SQLite database, and creates vector embeddings in ChromaDB.
    """
    from core.memory_service import reindex_memory_chunks
    from storage.db_manager import upsert_memory_index
    from storage.markdown_handler import create_markdown_file, normalize_title

    orphans = find_orphan_files()
    recovered_count = 0
    recovered_details = []

    for orphan in orphans:
        file_path = Path(orphan["file_path"])
        if not file_path.exists():
            continue

        frontmatter, content = read_markdown_file(file_path)
        mem_id = frontmatter.get("id") or generate_memory_id()
        raw_title = frontmatter.get("title") or file_path.stem.replace("_", " ").title()
        title = normalize_title(raw_title)
        category = frontmatter.get("category") or orphan.get("category") or "personal"
        tags = frontmatter.get("tags") or []
        created_at = frontmatter.get("created_at")
        updated_at = frontmatter.get("updated_at")
        content_hash = compute_string_hash(content)

        # Update the frontmatter in-place in the exact existing file
        create_markdown_file(
            memory_id=mem_id,
            title=title,
            category=category,
            tags=tags,
            content=content,
            content_hash=content_hash,
            created_at=created_at,
            updated_at=updated_at,
            file_path=file_path,
            overwrite=True,
        )

        # Re-index vector chunks in ChromaDB
        chunks, chunk_ids = reindex_memory_chunks(mem_id, content)

        # Index in SQLite database
        memory_entry = {
            "id": mem_id,
            "title": title,
            "category": category,
            "tags": tags,
            "file_path": str(file_path.resolve()),
            "content": content,
            "content_hash": content_hash,
            "chunk_ids": chunk_ids,
        }
        upsert_memory_index(memory_entry)

        recovered_count += 1
        recovered_details.append({
            "memory_id": mem_id,
            "title": title,
            "file_path": str(file_path),
        })

    return {
        "status": "success",
        "recovered_count": recovered_count,
        "recovered_documents": recovered_details,
    }


@handle_errors
def audit_storage_integrity(auto_fix: bool = False) -> Dict[str, Any]:
    """
    Performs a full storage integrity audit across disk storage, SQLite database, and ChromaDB vector store.
    Optionally reconciles/auto-fixes orphan records and indexes out-of-sync files.
    """
    orphan_files = find_orphan_files()
    orphan_indexes = find_orphan_indexes()
    orphan_chunks = find_orphan_chunks()

    # Detect content hash mismatches between disk and SQLite DB
    db_memories = get_all_memories()
    hash_mismatches = []
    for mem in db_memories:
        fp_str = mem.get("file_path")
        if fp_str and Path(fp_str).exists():
            _, content = read_markdown_file(Path(fp_str))
            disk_hash = compute_string_hash(content)
            db_hash = mem.get("content_hash")
            if disk_hash != db_hash:
                hash_mismatches.append({
                    "memory_id": mem.get("id"),
                    "title": mem.get("title"),
                    "file_path": fp_str,
                    "disk_hash": disk_hash,
                    "db_hash": db_hash,
                })

    auto_fix_results = None
    if auto_fix:
        deleted_idx = delete_orphan_indexes()
        deleted_chk = delete_orphan_chunks()
        recovered_docs = recover_orphaned_documents()
        auto_fix_results = {
            "deleted_orphan_indexes": deleted_idx.get("deleted_count", 0),
            "deleted_orphan_chunks": deleted_chk.get("deleted_count", 0),
            "recovered_documents": recovered_docs.get("recovered_count", 0),
        }
        # Refresh state after auto-fix
        orphan_files = find_orphan_files()
        orphan_indexes = find_orphan_indexes()
        orphan_chunks = find_orphan_chunks()
        hash_mismatches = []

    is_healthy = not (orphan_files or orphan_indexes or orphan_chunks or hash_mismatches)

    return {
        "status": "success",
        "is_healthy": is_healthy,
        "summary": {
            "orphan_files_count": len(orphan_files),
            "orphan_indexes_count": len(orphan_indexes),
            "orphan_chunks_count": len(orphan_chunks),
            "hash_mismatches_count": len(hash_mismatches),
        },
        "details": {
            "orphan_files": orphan_files,
            "orphan_indexes": orphan_indexes,
            "orphan_chunks": orphan_chunks,
            "hash_mismatches": hash_mismatches,
        },
        "auto_fix_applied": auto_fix,
        "auto_fix_results": auto_fix_results,
    }


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
        "message": "Successfully cleared memories directory, reset SQLite database, and purged ChromaDB vector store.",
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


