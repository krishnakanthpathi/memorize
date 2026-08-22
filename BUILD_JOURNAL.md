# Memorize: Build Journal & Learning Log

This document records the step-by-step process, commands, design decisions, and lessons learned while building the **Custom Memory MCP Server & Multi-Media RAG**.

---

## 📅 Log & Execution History

### 1. Initial Setup & Git Repository
- Ran: `echo "# memorize" >> README.md`
- Ran: `git init`
- Ran: `git add .`
- Ran: `git commit -m "first commit"`
- Ran: `git remote add origin https://github.com/krishnakanthpathi/memorize.git`
- Ran: `git push -u origin main`

### 2. Dependencies Installation
- Installed requirements: `mcp`, `chromadb`, `openai`, `sentence-transformers`, `pytesseract`, `openai-whisper`.
- Ran: `pip install -r requirements.txt`

### 3. Architecture Refactoring (Flat Root + `data/` Storage)
- **Refactoring**: Removed `src/` wrapper directory and moved all storage (`memories/`, `media_store/`, `index.json`, `chroma_db/`) into a centralized `data/` folder.
- **Why**: Eliminates `ModuleNotFoundError: No module named 'src'`, makes imports clean (`from core.id_generator import ...`), and keeps storage cleanly isolated inside `data/`.

---

## 🛠 Step-by-Step Implementation Progress

### Step 1: Core Utilities (`core/id_generator.py` & `core/hashing.py`)
- [x] Implemented `generate_memory_id()` (`mem_` + 12 random hex characters) and `generate_chunk_id()`.
- [x] Implemented `compute_string_hash()` and `compute_file_hash()` using SHA-256 for content & media deduplication.

### Step 2: Logging & Error Decorators (`core/logger.py`)
- [x] Configured Python standard `logger` writing strictly to `sys.stderr` (preserving clean stdio JSON-RPC streams).
- [x] Implemented `@handle_errors` decorator to log exceptions to `sys.stderr` and return clean JSON error objects.

### Step 3: Layer 1 — Markdown Storage (`storage/markdown_handler.py`)
- [x] Implemented `title_to_filename()` title sanitization.
- [x] Implemented `create_markdown_file()`, `read_markdown_file()`, and `delete_markdown_file()` with YAML frontmatter support.
- [x] Updated handlers to accept both `Path` and `str` types to prevent `AttributeError`.

### Step 4: Layer 2 — Smart Index (`storage/index_manager.py`) & Keyword Extractor (`search/filter_extractor.py`)
- [x] Implemented atomic writes to `data/index.json` using temp file rename (`os.replace`).
- [x] Created `extract_keywords_and_snippet()` to strip Markdown formatting, filter out stop words, and extract key terms.
- [x] Implemented reverse inverted index (`tag_index`) mapping tags/keywords $\rightarrow$ memory IDs in O(1) time.
- [x] Optimized `index.json` memory entries to store 150-char `snippet` previews and `keywords` instead of bloated full text.

### Step 5: Layer 3 — Vector Engine: Model-Aware Chunker (`vector/chunker.py`)
- [x] Added `MODEL_CHUNK_CONFIGS` to `config/constants.py` mapping specific token sizes & overlaps per provider:
  - OpenAI (`text-embedding-3-small`): 500 tokens, 50 overlap.
  - Ollama (`nomic-embed-text`): 500 tokens, 50 overlap.
  - Local HuggingFace (`all-MiniLM-L6-v2`): 256 tokens, 30 overlap.
- [x] Implemented model-aware `count_tokens()` using `tiktoken` for OpenAI with character-ratio estimation for Ollama/local models.
- [x] Built simple, clean, linear sliding-window `chunk_text()` that guarantees EVERY chunk stays under the model's max token limit with context overlap.

### Step 6: Automated Unit Test Suite (`tests/`)
- [x] Created 10 unit tests using Python's built-in `unittest` (`python3 -m unittest discover -s tests`).
- [x] Tests cover ID generation, SHA-256 hashing, Markdown CRUD operations, atomic index updates, and multi-thousand token HTML/Multi-RAG text chunking.
- [x] Test suite passes 100% cleanly in 0.14 seconds.

### Step 7: Interactive Testing Tools in `main.py`
- [x] Registered MCP tools in `main.py` (`ping`, `test_create_markdown_file`, `test_read_markdown_file`, `test_add_memory_to_index`, `test_load_index`, `test_chunk_text`).
- [x] Verified interactive execution in MCP Inspector (`npx @modelcontextprotocol/inspector python3 main.py`).

---

## 📁 Current Clean Directory Map

```
memorize/
├── main.py                           <-- Root entrypoint for MCP Server
├── requirements.txt                  <-- Dependency manifest
├── README.md                         <-- Project README
├── BUILD_JOURNAL.md                  <-- Build process & learning journal
├── data/                             <-- Centralized Storage Directory
│   ├── index.json                    <-- Layer 2: Fast Metadata Index
│   ├── chroma_db/                    <-- Layer 3: ChromaDB Vector Store
│   ├── memories/                     <-- Layer 1: Human Markdown Files
│   │   ├── personal/
│   │   ├── job/
│   │   ├── study/
│   │   ├── routine/
│   │   └── media/
│   └── media_store/                  <-- Raw Media Binary Store
│       ├── images/
│       ├── videos/
│       ├── audio/
│       └── documents/
├── config/
│   └── constants.py                  <-- Central paths, model limits & settings
├── core/
│   ├── id_generator.py               <-- Memory ID & Chunk ID generator
│   ├── hashing.py                    <-- SHA-256 string & file hasher
│   └── logger.py                     <-- Stderr logger & @handle_errors decorator
├── storage/
│   ├── markdown_handler.py           <-- YAML frontmatter + Markdown handler
│   ├── index_manager.py              <-- Atomic index.json updates
│   └── media_store_manager.py        <-- Raw media file manager
├── vector/
│   ├── chunker.py                    <-- Model-aware token chunker with context overlap
│   ├── embedder.py                   <-- OpenAI / Ollama / Local Embeddings
│   └── vector_db.py                  <-- ChromaDB collection manager
├── media/                            <-- Multi-Media Processors
│   ├── pipeline.py
│   ├── image_processor.py            <-- OCR + Vision Captioning
│   ├── audio_processor.py            <-- Whisper Speech-to-Text
│   ├── video_processor.py            <-- Keyframe sampling + Audio Whisper
│   └── doc_processor.py              <-- PDF / DOCX parser
├── classification/
│   └── classifier.py                 <-- Rule-based & LLM Classifier
├── search/
│   ├── filter_extractor.py           <-- Stop-word & keyword extractor
│   └── relevance_scorer.py           <-- Weighted ranker (Vector 50% + Tag 30% + Cat 20%)
└── tests/                            <-- Automated Unit Test Suite
    ├── test_id_generator.py
    ├── test_hashing.py
    ├── test_markdown_handler.py
    ├── test_index_manager.py
    └── test_chunker.py
### Step 13: Unified Server & Frontend Runner (`main.py`)
- [x] Refactored `main.py` into a master multi-service orchestrator.
- [x] Supports `python main.py` / `python main.py start` (concurrently runs FastAPI backend + Vite frontend with live color-coded logs and graceful SIGINT shutdown).
- [x] Supports subcommands: `backend` (FastAPI REST + MCP on port 7777), `frontend` (Vite UI on port 8888), `mcp` (FastMCP server), and `cli` (terminal memory manager).

### Step 14: Blueprint for Per-Memory Folder Architecture & Customizable Storage
- [x] Designed **Per-Memory Folder Bundle Architecture**:
  ```text
  <MEMORIES_DIR>/<category>/<memory_slug>/
  ├── <memory_slug>.md          <-- Note Markdown content & frontmatter
  ├── media/                    <-- Original attached files (PDFs, high-res images)
  └── thumbnails/               <-- Generated thumbnails and page preview images
  ```
- [x] Designed Customizable Storage Directory setting in Settings Panel with 1-click automated migration.

---

## 🧠 Key Technical Learnings & Engineering Concepts

### Learning 1: `stdout` vs `stderr` in MCP Servers
- **Rule**: Never use plain `print()` statements in a stdio MCP server!
- **Reason**: Standard output (`stdout`) is reserved for JSON-RPC message passing between the MCP Server and the AI client. Plain text on `stdout` breaks JSON parsing.
- **Solution**: Direct all log outputs to `sys.stderr` or use `logging` configured with `stream=sys.stderr`.

### Learning 2: Inverted Reverse Index (`tag_index`)
- **Concept**: Mapping tags and extracted keywords directly to memory IDs (`tag_index["6am"] -> ["mem_123"]`) allows O(1) instant lookups without scanning files or querying ChromaDB.

### Learning 3: Model-Aware Token Chunking & Overlap
- **Concept**: Chunking is required because embedding models have hard API token limits and accuracy drops on giant documents ("needle in a haystack"). Context overlap (50 tokens) prevents losing meaning across chunk boundaries.

---

## 🚀 How to Run Tests & Inspector

### 1. Run Automated Unit Tests:
```bash
python3 -m unittest discover -s tests
```

### 2. Run Full Stack (Backend + Frontend):
```bash
python3 main.py
```

