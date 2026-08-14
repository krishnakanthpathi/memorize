# memorize

Personal Knowledge Base MCP Server, FastAPI REST Service & Apple Notes-Inspired Markdown Web Application with Multi-Media Semantic RAG.

See [BUILD_JOURNAL.md](file:///Users/krishnakanth/Projects/memorize/BUILD_JOURNAL.md) for the detailed build log, architectural insights, and code blueprints.

---

## 📁 Repository Structure

```
memorize/
├── 🤖 mcp/                    # Model Context Protocol Subsystem
│   ├── __init__.py           # Package exports (mcp server, runner, register_all_tools)
│   ├── config.py             # Server metadata, model configs, and USE_LLM toggle
│   ├── service.py            # FastMCP server initialization & runner
│   └── tools/                # Lean core FastMCP tools
│       ├── __init__.py       # Core tool registar
│       └── memory_tools.py   # 5 core tools: store, update, delete, fetch, hybrid_fetch
├── ⚙️ api/                    # FastAPI REST Service (port 6999)
│   ├── server.py             # App factory & CORS setup
│   └── routes/               # Modular API endpoints (/memories, /search, /chat, /settings, etc.)
├── 💻 frontend/               # React 19 + TypeScript + Vite Web App (port 3000)
├── 🧠 core/                   # Memory services & LLM pipeline
├── 🔍 search/                 # Hybrid relevance ranking & BM25
├── 🗄️ storage/                # SQLite DB manager, versioning, markdown handler
├── ⚡ vector/                 # ChromaDB persistent vector engine
└── main.py                   # Master entrypoint (FastMCP Server / CLI)
```

---

## 🛠️ The 5 Lean Core MCP Tools

The FastMCP server exposes strictly **5 core tools**:

1. **`store`**: Stores knowledge into the system with automatic topic append/insert.
2. **`update`**: Updates or merges content with existing memories cleanly.
3. **`delete`**: Purges a memory across Markdown storage, SQLite DB, and ChromaDB.
4. **`fetch`**: Retrieves full markdown content by ID/title, or lists stored memories.
5. **`hybrid_fetch`**: Performs 50/30/20 weighted hybrid RAG search combining vector similarity, tag matches, and categories.

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
# Direct entrypoint (stdio transport)
python3 main.py

# Or run directly via mcp module
python3 -m mcp.service
```

---

## 🌐 Remote Access & External LLMs with ngrok

You can expose Memorize securely to external LLMs, cloud agents, remote machines, or mobile browsers using **ngrok**.

### 1. Expose the REST API to External LLMs & Webhooks
Tunnel the local FastAPI REST server (port `6999`) to a secure public HTTPS endpoint:
```bash
ngrok http 6999
```
- **Forwarding URL**: `https://<your-subdomain>.ngrok-free.app`
- **Interactive Swagger Docs**: `https://<your-subdomain>.ngrok-free.app/docs`
- External LLMs (e.g. OpenAI GPT actions, LangChain, custom cloud agents) can now query memories via `POST /api/search` and store data via `POST /api/memories`.

### 2. Connect to Remote Ollama GPU Servers via ngrok
If you are running Ollama or an open-weights model on a separate GPU server or cloud instance:
1. Run ngrok on your GPU machine:
   ```bash
   ngrok http 11434
   ```
2. Update your local `.env` or Settings Panel with the ngrok URL:
   ```ini
   OLLAMA_BASE_URL=https://<your-ollama-gpu>.ngrok-free.app
   ```

### 3. Expose the Web App for Remote Access
Tunnel the frontend web application (port `3000`):
```bash
ngrok http 3000
```
Open the generated HTTPS URL on any mobile device or external browser.

---

## Frontend Features (Apple Notes Monochrome Aesthetic)
- **3-Column Resizable Layout**: Navigation Sidebar, Note Master Stream, and WYSIWYG Editor Canvas.
- **3-Way Theme Switcher**: Light Mode, Slate Dark Mode (Default), and OLED Pitch Black Mode.
- **Master LLM Toggle & Model Config**: Switch between AI-Augmented Mode and 100% Offline Fast Mode directly from the Settings Panel.
- **Milkdown WYSIWYG Editor**: Live GitHub Flavored Markdown (GFM) editing with headings, task lists, code blocks, tables, and blockquotes.
- **Hybrid AI Vector Search**: Real-time semantic retrieval using ChromaDB and BM25 relevance scoring (`⌘K`).
- **AI Companion Chat**: Chat drawer querying local knowledge base using LLM context RAG (`/chat`).
- **Version History & Rollback**: Browse historical snapshots and restore any previous version.
- **Storage Integrity & Audit**: Multi-tier health dashboard with 1-click auto-fix for orphan files, indexes, and vector chunks.
- **Backup & Recovery**: Instant full markdown snapshots and DB backups.

