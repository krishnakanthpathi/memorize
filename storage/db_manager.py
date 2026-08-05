from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from config.constants import DATA_DIR, DB_PATH, MEMORIES_DIR
from core.logger import handle_errors, logger
from search.filter_extractor import extract_keywords_and_snippet
from utils.category_utils import get_available_categories, get_category_dir



def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with row factory enabled.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


@handle_errors
def init_db() -> None:
    """
    Initializes SQLite database schema and indexes if they do not exist.
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
        conn.commit()
    logger.info(f"SQLite database initialized at {DB_PATH}")


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
        # strip mem_id prefix if present
        if stem.startswith(f"{mem_id}_"):
            stem = stem[len(mem_id) + 1 :]
        slug = stem.lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (
                id, title, slug, category, tags, keywords, file_path, snippet, content_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                slug=excluded.slug,
                category=excluded.category,
                tags=excluded.tags,
                keywords=excluded.keywords,
                file_path=excluded.file_path,
                snippet=excluded.snippet,
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
    """Removes a memory from the SQLite index by ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0


@handle_errors
def clear_all_index_memories() -> None:
    """Purges all records from SQLite memories table."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories;")
        conn.commit()


@handle_errors
def get_categories_stats() -> List[str]:
    """Returns list of categories from disk and DB."""
    return get_available_categories()
