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

### 4. Current Clean Directory Map

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
│   └── constants.py                  <-- Central paths & settings
├── core/
│   ├── id_generator.py               <-- Memory ID & Chunk ID generator
│   ├── hashing.py                    <-- SHA-256 string & file hasher
│   └── logger.py                     <-- Stderr logger
├── storage/
│   ├── markdown_handler.py           <-- YAML frontmatter + Markdown handler
│   ├── index_manager.py              <-- Atomic index.json updates
│   └── media_store_manager.py        <-- Raw media file manager
├── vector/
│   ├── chunker.py                    <-- Token chunker (500 tokens, 50 overlap)
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
└── search/
    ├── filter_extractor.py           <-- Query parser
    └── relevance_scorer.py           <-- Weighted ranker (Vector 50% + Tag 30% + Cat 20%)
```

---

## 🚀 How to Run the MCP Server & Inspector

```bash
npx @modelcontextprotocol/inspector python3 main.py
```
