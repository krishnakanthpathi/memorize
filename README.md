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
│       └── memory_tools.py   # Core tools: store, update, delete, fetch, hybrid_fetch, list_memories, get_categories
├── ⚙️ api/                    # FastAPI REST Service (port 7777)
│   ├── server.py             # App factory & CORS setup
│   └── routes/               # Modular API endpoints (/memories, /search, /chat, /settings, etc.)
├── 💻 frontend/               # React 19 + TypeScript + Vite Web App (port 6666)
├── 🧠 core/                   # Memory services & LLM pipeline
├── 🔍 search/                 # Hybrid relevance ranking & BM25
├── 🗄️ storage/                # SQLite DB manager, versioning, markdown handler
├── ⚡ vector/                 # ChromaDB persistent vector engine
└── main.py                   # Master entrypoint (FastMCP Server / CLI)
```

---

## 🛠️ Registered MCP Tools (7 Tools)

The FastMCP server exposes **7 focused tools**:

1. **`store`**: Stores knowledge into the system with automatic category assignment and topic append/insert.
2. **`update`**: Updates, appends, or cleanly merges content with existing memories.
3. **`delete`**: Purges a memory across Markdown storage, SQLite DB, and ChromaDB.
4. **`fetch`**: Retrieves full markdown content and frontmatter metadata by ID or title.
5. **`hybrid_fetch`**: Performs 50/30/20 weighted hybrid RAG search combining vector similarity, tag matches, and categories.
6. **`list_memories`**: Lists stored memories with optional category/tag filters and limit.
7. **`get_categories`**: Lists all 11 standard predefined categories with note counts and semantic descriptions.

---

## How to Run

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt fastapi uvicorn
```

### 2. Run the FastAPI REST Service
```bash
python3 -m uvicorn api.server:app --host 0.0.0.0 --port 7777 --reload
```
API Documentation will be available at: `http://localhost:7777/docs`

### 3. Run the Frontend Web Application
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:6666`

### 4. Run the Universal FastMCP Server (Claude Desktop / Gemini / Cursor / Antigravity)
```bash
# Stdio transport (for Claude Desktop, Cursor, Antigravity)
python3 main.py

# SSE / Streamable-HTTP transport (for Google Gemini Custom Connected Apps, remote clients)
python3 main.py --transport sse --port 7777
```


---

## 🌐 Remote Access & External LLMs with ngrok

You can expose Memorize securely to external LLMs, cloud agents, remote machines, or mobile browsers using **ngrok**.

### 1. Expose the REST API / MCP Server to External LLMs & Webhooks
Tunnel the local FastAPI REST and Universal MCP server (port `7777`) to a secure public HTTPS endpoint:
```bash
ngrok http 7777
```
- **Forwarding URL**: `https://<your-subdomain>.ngrok-free.app`
- **MCP Endpoint**: `https://<your-subdomain>.ngrok-free.app/sse`
- **Interactive Swagger Docs**: `https://<your-subdomain>.ngrok-free.app/docs`
- External LLMs (e.g. Google Gemini, Claude, OpenAI GPT actions) can now query memories via MCP or REST endpoints.

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
Tunnel the frontend web application (port `6666`):
```bash
ngrok http 6666
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

