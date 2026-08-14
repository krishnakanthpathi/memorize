# memorize

Personal Knowledge Base MCP Server, FastAPI REST Service & Apple Notes-Inspired Markdown Web Application with Multi-Media Semantic RAG.

See [BUILD_JOURNAL.md](file:///Users/krishnakanth/Projects/memorize/BUILD_JOURNAL.md) for the detailed build log, architectural insights, and code blueprints.

---

## How to Run

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt fastapi uvicorn
```

### 2. Run the FastAPI REST Service
```bash
python3 -m uvicorn api.server:app --host 0.0.0.0 --port 6999 --reload
```
API Documentation will be available at: `http://localhost:6999/docs`

### 3. Run the Frontend Web Application
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:3000`

### 4. Run the FastMCP Server (Claude Desktop / Cursor / Antigravity)
```bash
python3 main.py
```

---

## Frontend Features (Apple Notes Monochrome Aesthetic)
- **3-Column Resizable Layout**: Navigation Sidebar, Note Master Stream, and WYSIWYG Editor Canvas.
- **3-Way Theme Switcher**: Light Mode, Slate Dark Mode (Default), and OLED Pitch Black Mode.
- **Milkdown WYSIWYG Editor**: Live GitHub Flavored Markdown (GFM) editing with headings, task lists, code blocks, tables, and blockquotes.
- **Hybrid AI Vector Search**: Real-time semantic retrieval using ChromaDB and BM25 relevance scoring (`⌘K`).
- **AI Companion Chat**: Chat drawer querying local knowledge base using LLM context RAG (`/chat`).
- **Version History & Rollback**: Browse historical snapshots and restore any previous version.
- **Storage Integrity & Audit**: Multi-tier health dashboard with 1-click auto-fix for orphan files, indexes, and vector chunks.
- **Backup & Recovery**: Instant full markdown snapshots and DB backups.
