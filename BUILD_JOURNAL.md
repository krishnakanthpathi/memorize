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

### 2. Environment & Dependencies Installation
- Created `requirements.txt`:
  ```txt
  mcp>=1.0.0
  chromadb>=0.4.0
  openai>=1.0.0
  sentence-transformers>=2.2.0
  tiktoken>=0.5.0
  langchain-text-splitters>=0.0.1
  pyyaml>=6.0
  python-dotenv>=1.0.0
  pydantic>=2.0.0
  requests>=2.31.0
  pillow>=10.0.0
  pytesseract>=0.3.10
  pypdf>=3.10.0
  pdfplumber>=0.10.0
  openai-whisper>=20231117
  ```
- Ran: `pip install -r requirements.txt`

### 3. Architecture Simplification Decision
- **Initial Idea**: Build a React + Bootstrap frontend + FastAPI REST server.
- **Revised Decision**: Removed the frontend (`rm -rf frontend`) and FastAPI endpoints.
- **Why**: A pure STDIO MCP server allows direct, zero-bloat connections from AI agents (Claude Desktop, Cursor, LangChain/LangGraph agents) via standard MCP JSON-RPC protocol.

### 4. Folder Structure Created

```
memorize/
├── requirements.txt
├── index.json                        <-- Layer 2: Fast Metadata Index
├── chroma_db/                        <-- Layer 3: ChromaDB Vector Store
├── memories/                         <-- Layer 1: Human Markdown Files
│   ├── personal/
│   ├── job/
│   ├── study/
│   ├── routine/
│   └── media/
├── media_store/                      <-- Raw Media Binary Store
│   ├── images/
│   ├── videos/
│   ├── audio/
│   └── documents/
└── src/
    ├── config/
    │   └── constants.py              <-- Central paths & settings
    ├── core/
    │   ├── id_generator.py           <-- Memory ID & Chunk ID generator
    │   ├── hashing.py                <-- SHA-256 string & file hasher
    │   └── logger.py                 <-- Stderr logger
    ├── storage/
    │   ├── markdown_handler.py       <-- YAML frontmatter + Markdown handler
    │   ├── index_manager.py          <-- Atomic index.json updates
    │   └── media_store_manager.py    <-- Raw media file manager
    ├── vector/
    │   ├── chunker.py                <-- Token chunker (500 tokens, 50 overlap)
    │   ├── embedder.py               <-- OpenAI / Ollama / Local Embeddings
    │   └── vector_db.py              <-- ChromaDB collection manager
    ├── media/                        <-- Multi-Media Processors
    │   ├── pipeline.py
    │   ├── image_processor.py        <-- OCR + Vision Captioning
    │   ├── audio_processor.py        <-- Whisper Speech-to-Text
    │   ├── video_processor.py        <-- Keyframe sampling + Audio Whisper
    │   └── doc_processor.py          <-- PDF / DOCX parser
    ├── classification/
    │   └── classifier.py             <-- Rule-based & LLM Classifier
    ├── search/
    │   ├── filter_extractor.py       <-- Query parser
    │   └── relevance_scorer.py       <-- Weighted ranker (Vector 50% + Tag 30% + Cat 20%)
    └── main.py                       <-- Main MCP Server & Tools
```

## MCP Inspector Testing
npx @modelcontextprotocol/inspector python3 src/main.py
