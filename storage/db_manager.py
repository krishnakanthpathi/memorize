from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

import config.constants as constants
from core.logger import handle_errors, logger
from search.filter_extractor import extract_keywords_and_snippet
from utils.category_utils import get_available_categories, get_category_dir



def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with row factory enabled.
    """
    constants.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(constants.DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


@handle_errors
def init_db() -> None:
    """
    Initializes SQLite database schema, backup tables, and indexes if they do not exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                slug TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT NOT NULL, -- JSON array of tags
                keywords TEXT NOT NULL, -- JSON array of keywords
                file_path TEXT NOT NULL UNIQUE,
                snippet TEXT,
                content TEXT,
                content_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_slug ON memories(category, slug);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);"
        )

        # Migration: Ensure 'content' column exists in existing database schemas
        cursor.execute("PRAGMA table_info(memories);")
        columns = [col["name"] for col in cursor.fetchall()]
        if "content" not in columns:
            cursor.execute("ALTER TABLE memories ADD COLUMN content TEXT;")
            logger.info("Migrated SQLite schema: Added 'content' column to 'memories' table.")

        # Create backup metadata tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                file_path TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_readme (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                readme_text TEXT NOT NULL,
                total_memories INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_versions_id ON memory_versions(memory_id, version_number);"
        )

        # Create media_items table for original uncompressed images & OCR metadata
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS media_items (
                id TEXT PRIMARY KEY,
                memory_id TEXT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                mime_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                ocr_text TEXT,
                ocr_status TEXT DEFAULT 'pending',
                ocr_model TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_media_memory_id ON media_items(memory_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_media_hash ON media_items(content_hash);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_media_filename ON media_items(filename);"
        )

        conn.commit()
    logger.info(f"SQLite database initialized at {constants.DB_PATH}")


@handle_errors
def upsert_memory_index(memory_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts or updates a memory record in SQLite.
    Guarantees no duplicate entries per memory_id or file_path.
    """
    init_db()

    full_content = memory_entry.get("content", "")
    snippet, extracted_keywords = extract_keywords_and_snippet(full_content)

    user_tags = memory_entry.get("tags", [])
    if isinstance(user_tags, str):
        user_tags = [t.strip() for t in user_tags.split(",") if t.strip()]

    tags_json = json.dumps(user_tags)
    keywords_json = json.dumps(extracted_keywords)

    mem_id = memory_entry["id"]
    title = memory_entry["title"]
    category = memory_entry.get("category", "personal").lower()
    file_path = str(memory_entry.get("file_path", ""))
    content_hash = memory_entry.get("content_hash", "")
    now_iso = datetime.now(timezone.utc).isoformat()
    created_at = memory_entry.get("created_at") or now_iso
    updated_at = memory_entry.get("updated_at") or now_iso

    # Derive slug from title or file_path stem
    slug = memory_entry.get("slug")
    if not slug:
        stem = Path(file_path).stem if file_path else title
        if stem.startswith(f"{mem_id}_"):
            stem = stem[len(mem_id) + 1 :]
        slug = stem.lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Prevent UNIQUE constraint failure if file_path belongs to another memory ID
        cursor.execute("SELECT id FROM memories WHERE file_path = ? AND id != ?", (file_path, mem_id))
        if cursor.fetchone():
            fp_path = Path(file_path)
            file_path = str(fp_path.parent / f"{fp_path.stem}_{mem_id}{fp_path.suffix}")

        cursor.execute(
            """
            INSERT INTO memories (
                id, title, slug, category, tags, keywords, file_path, snippet, content, content_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                slug=excluded.slug,
                category=excluded.category,
                tags=excluded.tags,
                keywords=excluded.keywords,
                file_path=excluded.file_path,
                snippet=excluded.snippet,
                content=excluded.content,
                content_hash=excluded.content_hash,
                updated_at=excluded.updated_at;
            """,
            (
                mem_id,
                title,
                slug,
                category,
                tags_json,
                keywords_json,
                file_path,
                snippet,
                full_content,
                content_hash,
                created_at,
                updated_at,
            ),
        )
        conn.commit()

    logger.info(f"Upserted memory '{mem_id}' in SQLite database.")
    return get_memory_by_id(mem_id)


@handle_errors
def get_memory_by_id(memory_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single memory record by Memory ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["tags"] = json.loads(res["tags"]) if res["tags"] else []
            res["keywords"] = json.loads(res["keywords"]) if res["keywords"] else []
            return res
    return None


@handle_errors
def find_memory_by_title_or_slug(title: str, category: str = "personal") -> Optional[Dict[str, Any]]:
    """
    Finds an existing memory matching the title or title slug within a category.
    Supports exact slug match, title match, or partial slug alignment.
    """
    init_db()
    from storage.markdown_handler import title_to_slug, normalize_title

    category_clean = category.strip().lower()
    target_norm = normalize_title(title).lower()
    target_slug = title_to_slug(title)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 1. Direct exact slug or title match
        cursor.execute(
            "SELECT * FROM memories WHERE category = ? AND (slug = ? OR LOWER(title) = ?)",
            (category_clean, target_slug, target_norm),
        )
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["tags"] = json.loads(res["tags"]) if res["tags"] else []
            res["keywords"] = json.loads(res["keywords"]) if res["keywords"] else []
            return res

        # 2. Fuzzy / Partial slug containment match (e.g. 'user_profile' matches 'user_profile_krishnakanth')
        cursor.execute(
            "SELECT * FROM memories WHERE category = ? AND (slug LIKE ? OR ? LIKE '%' || slug || '%')",
            (category_clean, f"%{target_slug}%", target_slug),
        )
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["tags"] = json.loads(res["tags"]) if res["tags"] else []
            res["keywords"] = json.loads(res["keywords"]) if res["keywords"] else []
            return res

    return None


@handle_errors
def get_all_memories(
    category_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves memories with optional filtering by category or tag.
    """
    init_db()
    results = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if category_filter:
            cursor.execute("SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC", (category_filter.lower(),))
        else:
            cursor.execute("SELECT * FROM memories ORDER BY updated_at DESC")
        
        rows = cursor.fetchall()
        for row in rows:
            res = dict(row)
            res["tags"] = json.loads(res["tags"]) if res["tags"] else []
            res["keywords"] = json.loads(res["keywords"]) if res["keywords"] else []
            
            if tag_filter:
                tag_lower = tag_filter.strip().lower()
                if not any(t.lower() == tag_lower for t in res["tags"]):
                    continue
            results.append(res)
    return results


@handle_errors
def delete_memory_from_index(memory_id: str) -> bool:
    """Removes a memory and its associated version and backup records from SQLite index by ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        cursor.execute("DELETE FROM memory_versions WHERE memory_id = ?", (memory_id,))
        cursor.execute("DELETE FROM backup_records WHERE memory_id = ?", (memory_id,))
        conn.commit()
        return deleted


@handle_errors
def clear_all_index_memories() -> None:
    """Purges all records from SQLite memories table."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories;")
        conn.commit()


@handle_errors
def clear_all_backup_records_from_db() -> None:
    """Purges all backup records and readme entries from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM backup_records;")
        cursor.execute("DELETE FROM backup_readme;")
        conn.commit()
    logger.info("Cleared all backup records and README entries from SQLite DB.")



@handle_errors
def get_categories_stats() -> List[str]:
    """Returns list of categories from disk and DB."""
    return get_available_categories()


@handle_errors
def log_backup_record(
    memory_id: str,
    title: str,
    category: str,
    file_path: str,
    backup_path: str,
    content_hash: str,
) -> bool:
    """Logs a single memory backup record into SQLite."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_records (
                memory_id, title, category, file_path, backup_path, content_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (memory_id, title, category, str(file_path), str(backup_path), content_hash, now_iso),
        )
        conn.commit()
    return True


@handle_errors
def save_backup_readme_to_db(readme_text: str, total_memories: int) -> bool:
    """Saves the generated backup README.txt snapshot content into SQLite."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_readme (readme_text, total_memories, created_at)
            VALUES (?, ?, ?)
            """,
            (readme_text, total_memories, now_iso),
        )
        conn.commit()
    return True


@handle_errors
def get_latest_backup_readme_from_db() -> Optional[Dict[str, Any]]:
    """Retrieves the latest backup README summary from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM backup_readme ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


@handle_errors
def db_save_version(
    memory_id: str,
    title: str,
    category: str,
    tags: List[str],
    content: str,
    content_hash: str,
) -> Dict[str, Any]:
    """
    Saves a version snapshot of a memory into SQLite and returns version details.
    Increments version_number based on highest existing version for this memory.
    """
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    tags_json = json.dumps(tags if isinstance(tags, list) else [])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(version_number) FROM memory_versions WHERE memory_id = ?",
            (memory_id,),
        )
        max_row = cursor.fetchone()
        current_max = max_row[0] if (max_row and max_row[0] is not None) else 0
        next_ver = current_max + 1

        cursor.execute(
            """
            INSERT INTO memory_versions (
                memory_id, version_number, title, category, tags, content, content_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                next_ver,
                title,
                category,
                tags_json,
                content,
                content_hash,
                now_iso,
            ),
        )
        conn.commit()

    logger.info(f"Saved version {next_ver} for memory '{memory_id}' in SQLite.")
    return {
        "memory_id": memory_id,
        "version_number": next_ver,
        "title": title,
        "category": category,
        "tags": tags,
        "created_at": now_iso,
        "content_hash": content_hash,
    }


@handle_errors
def db_get_versions(memory_id: str) -> List[Dict[str, Any]]:
    """Retrieves all version snapshots for a given memory ID ordered newest to oldest."""
    init_db()
    results = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM memory_versions WHERE memory_id = ? ORDER BY version_number DESC",
            (memory_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            res = dict(row)
            res["tags"] = json.loads(res["tags"]) if res["tags"] else []
            results.append(res)
    return results


@handle_errors
def db_get_version_by_number(memory_id: str, version_number: int) -> Optional[Dict[str, Any]]:
    """Retrieves a specific version record for a memory ID by version number."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM memory_versions WHERE memory_id = ? AND version_number = ?",
            (memory_id, version_number),
        )
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["tags"] = json.loads(res["tags"]) if res["tags"] else []
            return res
    return None


@handle_errors
def db_prune_versions(memory_id: str, max_versions: int = 3) -> int:
    """
    Keep only the most recent `max_versions` for a given memory_id and delete older ones.
    Returns the count of pruned records.
    """
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM memory_versions WHERE memory_id = ? ORDER BY version_number DESC",
            (memory_id,),
        )
        rows = cursor.fetchall()
        if len(rows) > max_versions:
            to_delete = [r["id"] for r in rows[max_versions:]]
            placeholders = ",".join(["?"] * len(to_delete))
            cursor.execute(
                f"DELETE FROM memory_versions WHERE id IN ({placeholders})",
                to_delete,
            )
            conn.commit()
            logger.info(f"Pruned {cursor.rowcount} old version records for memory '{memory_id}'.")
            return cursor.rowcount
    return 0


@handle_errors
def clear_all_memory_versions_from_db() -> None:
    """Purges all memory version records from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory_versions;")
        conn.commit()
    logger.info("Cleared all memory versions from SQLite DB.")


# ==========================================
# Media Store Database Helpers
# ==========================================


@handle_errors
def upsert_media_record(media_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts or updates a media record in SQLite.
    """
    init_db()
    media_id = media_entry["id"]
    memory_id = media_entry.get("memory_id")
    filename = media_entry["filename"]
    original_filename = media_entry.get("original_filename", filename)
    file_path = str(media_entry["file_path"])
    mime_type = media_entry.get("mime_type", "image/png")
    file_size = int(media_entry.get("file_size", 0))
    content_hash = media_entry.get("content_hash", "")
    ocr_text = media_entry.get("ocr_text", "")
    ocr_status = media_entry.get("ocr_status", "pending")
    ocr_model = media_entry.get("ocr_model", "")
    now_iso = datetime.now(timezone.utc).isoformat()
    created_at = media_entry.get("created_at") or now_iso
    updated_at = media_entry.get("updated_at") or now_iso

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM media_items WHERE id = ? OR file_path = ?", (media_id, file_path))
        existing_row = cursor.fetchone()
        if existing_row:
            target_id = existing_row["id"]
            cursor.execute(
                """
                UPDATE media_items SET
                    memory_id = ?,
                    filename = ?,
                    original_filename = ?,
                    file_path = ?,
                    mime_type = ?,
                    file_size = ?,
                    content_hash = ?,
                    ocr_text = ?,
                    ocr_status = ?,
                    ocr_model = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    memory_id,
                    filename,
                    original_filename,
                    file_path,
                    mime_type,
                    file_size,
                    content_hash,
                    ocr_text,
                    ocr_status,
                    ocr_model,
                    updated_at,
                    target_id,
                ),
            )
            media_entry["id"] = target_id
        else:
            cursor.execute(
                """
                INSERT INTO media_items (
                    id, memory_id, filename, original_filename, file_path,
                    mime_type, file_size, content_hash, ocr_text, ocr_status,
                    ocr_model, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    media_id,
                    memory_id,
                    filename,
                    original_filename,
                    file_path,
                    mime_type,
                    file_size,
                    content_hash,
                    ocr_text,
                    ocr_status,
                    ocr_model,
                    created_at,
                    updated_at,
                ),
            )
        conn.commit()
    logger.info(f"Upserted media record '{media_entry['id']}' ({filename}) in SQLite.")
    return media_entry


@handle_errors
def get_media_record(media_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single media record by its ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_items WHERE id = ?", (media_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


@handle_errors
def get_media_record_by_hash(content_hash: str) -> Optional[Dict[str, Any]]:
    """Retrieves a media record by its SHA-256 content hash."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_items WHERE content_hash = ? LIMIT 1", (content_hash,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


@handle_errors
def get_media_record_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    """Retrieves a media record by its stored filename or original filename."""
    if not filename:
        return None
    init_db()
    clean_name = Path(filename).name
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM media_items 
            WHERE filename = ? OR original_filename = ? OR filename LIKE ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (clean_name, clean_name, f"%{clean_name}%"),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None



@handle_errors
def get_media_records_for_memory(memory_id: str) -> List[Dict[str, Any]]:
    """Retrieves all media records associated with a given memory ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_items WHERE memory_id = ? ORDER BY created_at DESC", (memory_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


@handle_errors
def list_all_media_records() -> List[Dict[str, Any]]:
    """Retrieves all stored media items ordered by creation date descending."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_items ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


@handle_errors
def update_media_ocr_result(media_id: str, ocr_text: str, ocr_status: str = "completed", ocr_model: str = "glm-ocr") -> bool:
    """Updates the OCR text, status, and model for a media item."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE media_items
            SET ocr_text = ?, ocr_status = ?, ocr_model = ?, updated_at = ?
            WHERE id = ?
            """,
            (ocr_text, ocr_status, ocr_model, now_iso, media_id),
        )
        conn.commit()
        return cursor.rowcount > 0


@handle_errors
def delete_media_record(media_id: str) -> bool:
    """Deletes a media item record from SQLite."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM media_items WHERE id = ?", (media_id,))
        conn.commit()
        return cursor.rowcount > 0



