# memorize

Personal Knowledge Base MCP Server with Multi-Media Semantic RAG.

See [BUILD_JOURNAL.md](file:///Users/krishnakanth/Projects/memorize/BUILD_JOURNAL.md) for the detailed build log, architectural insights, and code blueprints.

## How to Run This Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt fastapi uvicorn
```

### 2. Run the FastAPI REST Service
> ⚠️ **Important**: Make sure your terminal is in the project root directory (`/Users/krishnakanth/Projects/memorize`), not inside the `api/` folder.

```bash
cd /Users/krishnakanth/Projects/memorize
python3 -m api.server
```

Or using uvicorn directly:
```bash
cd /Users/krishnakanth/Projects/memorize
python3 -m uvicorn api.server:app --host 0.0.0.0 --port 6999 --reload
```

### 3. Run the FastMCP Server
```bash
cd /Users/krishnakanth/Projects/memorize
python3 main.py
```



```
WITHOUT SQLite Index (hypothetical):
──────────────────────────────────────
Query arrives
  → Vector search (ChromaDB) .............. ~50ms
  → For each of 20 results:
      → Reconstruct file path ............. ~1ms
      → Open + read .md file .............. ~5ms × 20 = 100ms
      → Parse YAML frontmatter ............ ~2ms × 20 = 40ms
      → Extract keywords .................. ~3ms × 20 = 60ms
  → BM25: read ALL 500 .md files .......... ~2500ms
  → Score + rank ........................... ~10ms
                                    TOTAL: ~2760ms

WITH SQLite Index (actual):
──────────────────────────────────────
Query arrives
  → Vector search (ChromaDB) .............. ~50ms
  → SQLite: SELECT * FROM memories ........ ~5ms  (one query, everything)
  → Build memories_map dict ............... ~1ms
  → BM25: build from SQLite data .......... ~20ms (no file I/O)
  → Enrich vector results ................. ~1ms  (dict lookups)
  → Candidate expansion (text scan) ....... ~3ms  (in-memory strings)
  → Score + rank ........................... ~10ms
                                    TOTAL: ~90ms
```