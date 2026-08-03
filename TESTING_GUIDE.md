# Memorize MCP Tools - Interactive Testing Guide

This guide provides step-by-step instructions and ready-to-copy JSON inputs to test all registered MCP tools in the **MCP Inspector UI** (`http://localhost:6274`).

---

## 🚀 Getting Started

1. Open the MCP Inspector Web UI at **`http://localhost:6274`**.
2. Select any tool from the dropdown menu.
3. Paste the example JSON arguments provided below and click **Run Tool**.

---

## 🛠 Tool Testing Scenarios & Sample Inputs

### 1. Server Status
#### Tool: `ping`
- **Description**: Verifies that the Memorize MCP Server is live.
- **Input**:
```json
{
  "message": "Hello Memorize Server!"
}
```

---

### 2. Core Identifiers & Security
#### Tool: `test_generate_id`
- **Description**: Generates a unique Memory ID (`mem_...`) and Chunk ID.
- **Input**: `{}`

#### Tool: `test_hash_string`
- **Description**: Computes the SHA-256 hash of text content.
- **Input**:
```json
{
  "content": "This is a test memory note for SHA-256 hashing."
}
```

---

### 3. Layer 1: Markdown Storage (File Operations)

#### Tool: `test_create_markdown_file`
- **Description**: Creates a Markdown file with YAML frontmatter under `data/memories/<category>/`.
- **Input**:
```json
{
  "memory_id": "mem_study_001",
  "title": "Python RAG Architecture Notes",
  "category": "study",
  "tags": ["python", "rag", "mcp"],
  "content": "Building a custom Memory MCP Server with ChromaDB and SentenceTransformer embeddings."
}
```

#### Tool: `test_read_markdown_file`
- **Description**: Reads and parses a Markdown memory file.
- **Input**:
```json
{
  "file_path": "/Users/krishnakanth/Projects/memorize/data/memories/study/python_rag_architecture_notes.md"
}
```

#### Tool: `test_delete_markdown_file`
- **Description**: Deletes a Markdown memory file.
- **Input**:
```json
{
  "file_path": "/Users/krishnakanth/Projects/memorize/data/memories/study/python_rag_architecture_notes.md"
}
```

---

### 4. Layer 2: Fast Metadata Index (`data/index.json`)

#### Tool: `test_load_index`
- **Description**: Reads `data/index.json`. Seeds a fresh structure if missing.
- **Input**: `{}`

#### Tool: `test_add_memory_to_index`
- **Description**: Adds a memory entry to `index.json` and updates stats & tag maps.
- **Input**:
```json
{
  "memory_entry": {
    "id": "mem_study_001",
    "title": "Python RAG Architecture Notes",
    "category": "study",
    "tags": ["python", "rag", "mcp"],
    "file_path": "data/memories/study/python_rag_architecture_notes.md",
    "content_hash": "a1b2c3d4e5f6",
    "created_at": "2026-08-03T10:00:00Z",
    "updated_at": "2026-08-03T10:00:00Z",
    "chunk_ids": ["mem_study_001_chunk_0"]
  }
}
```

---

### 5. Layer 3: Model-Aware Token Chunker

#### Tool: `test_chunk_text`
- **Description**: Splits text into chunks adhering to active model token limits with context overlap.
- **Input**:
```json
{
  "memory_id": "mem_demo_999",
  "text": "The Model Context Protocol (MCP) is an open protocol that enables AI models to securely interact with local or remote resources, vector databases, and external APIs. This allows seamless integration across context providers.",
  "model_name": "all-MiniLM-L6-v2"
}
```

---

### 6. Layer 4: Embeddings Generator

#### Tool: `test_generate_local_embeddings`
- **Description**: Generates 384-dimensional vector embeddings offline via `SentenceTransformer`.
- **Input**:
```json
{
  "texts": ["ChromaDB vector database setup and Python RAG architecture"],
  "model_name": "all-MiniLM-L6-v2"
}
```

#### Tool: `test_generate_ollama_embeddings`
- **Description**: Generates embeddings using local/remote Ollama instance (`100.105.203.102:11434`).
- **Input**:
```json
{
  "texts": ["Local Ollama vector embedding test"],
  "model_name": "nomic-embed-text"
}
```

#### Tool: `list_available_models`
- **Description**: Fetches available models from an API endpoint and bifurcates into embedding vs generative models.
- **Input**:
```json
{
  "base_url": "http://100.105.203.102:11434/v1"
}
```

---

### 7. Layer 5: ChromaDB Vector Database & Inspection

#### Tool: `test_add_chunks_to_vector_db`
- **Description**: Upserts text chunks and 384-dimensional vector embeddings into ChromaDB container.
- **Input**:
```json
{
  "chunks": [
    {
      "id": "mem_study_001_chunk_0",
      "content": "Building a custom Memory MCP Server with ChromaDB and SentenceTransformer embeddings.",
      "metadata": {
        "memory_id": "mem_study_001",
        "chunk_index": 0,
        "category": "study",
        "tags": ["python", "rag", "mcp"]
      }
    }
  ],
  "embeddings": [
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
  ]
}
```

#### Tool: `test_peek_vector_db`
- **Description**: Peeks at stored chunks & metadata in ChromaDB.
- **Input**:
```json
{
  "limit": 10
}
```

---

### 8. Layer 6: Hybrid Relevance Search Engine

#### Tool: `hybrid_search_memories`
- **Description**: Performs weighted hybrid search combining Vector Similarity (50%), Tag Match (30%), and Category Match (20%).
- **Input**:
```json
{
  "query": "python rag architecture",
  "category_filter": "study",
  "top_k": 5
}
```
