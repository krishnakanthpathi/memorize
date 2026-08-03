from pathlib import Path
import sys
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from config.constants import (
    EMBEDDING_MODEL_NAME,
    FALLBACK_EMBEDDING_MODEL,
    OLLAMA_EMBEDDING_MODEL,
)
from core.hashing import compute_string_hash
from core.id_generator import generate_chunk_id, generate_memory_id
from storage.index_manager import (
    add_memory_to_index,
    get_initial_index_structure,
    load_index,
    save_index,
)
from storage.markdown_handler import (
    create_markdown_file,
    delete_markdown_file,
    read_markdown_file,
)
from utils.model_fetcher import fetch_and_bifurcate_models
from vector.chunker import chunk_text
from vector.embedder import (
    generate_local_embeddings,
    generate_ollama_embeddings,
    generate_openai_embeddings,
)

# Initialize FastMCP Server
mcp = FastMCP("Memorize Server")


@mcp.tool()
def ping(message: str = "hello") -> str:
    """
    Test tool to verify that the Memorize MCP server is online.
    """
    return f"Memorize MCP Server is active! You sent: '{message}'"


@mcp.tool()
def test_generate_id() -> dict:
    """
    Test tool to generate a new unique Memory ID and Chunk ID.
    """
    mem_id = generate_memory_id()
    chunk_id = generate_chunk_id(mem_id, 0)
    return {
        "status": "success",
        "generated_memory_id": mem_id,
        "generated_chunk_id": chunk_id,
    }


@mcp.tool()
def test_hash_string(content: str) -> dict:
    """
    Test tool to compute the SHA-256 hash of a given text content.
    """
    content_hash = compute_string_hash(content)
    return {
        "content": content,
        "sha256_hash": content_hash,
    }


@mcp.tool()
def test_create_markdown_file(
    memory_id: str,
    title: str,
    content: str,
    category: str = "personal",
    tags: list[str] = ["test"],
    content_hash: str = "",
    created_at: str = "",
    updated_at: str = "",
) -> dict:
    """
    Creates a Markdown file with YAML frontmatter and content body.
    """
    file_path = create_markdown_file(
        memory_id=memory_id,
        title=title,
        category=category,
        tags=tags,
        content=content,
        content_hash=content_hash,
        created_at=created_at,
        updated_at=updated_at,
    )
    return {
        "status": "success",
        "file_path": str(file_path),
        "exists_on_disk": Path(file_path).exists() if isinstance(file_path, (str, Path)) else False,
    }


@mcp.tool()
def test_read_markdown_file(file_path: str) -> dict:
    """
    Reads a Markdown file from disk and parses YAML frontmatter + content body.
    """
    result = read_markdown_file(file_path)
    
    # If read_markdown_file returned an error dict from @handle_errors
    if isinstance(result, dict) and result.get("status") == "error":
        return result

    frontmatter, content = result
    return {
        "status": "success",
        "file_path": file_path,
        "frontmatter": frontmatter,
        "content": content,
    }

@mcp.tool()
def test_delete_markdown_file(file_path: str) -> dict:
    """
    Deletes a Markdown file from disk if it exists.
    """
    result = delete_markdown_file(file_path)
    return {
        "status": "success",
        "file_path": file_path,
        "deleted": result,
    }


@mcp.tool()
def test_get_initial_index_structure() -> dict:
    """
    Returns a blank index structure.
    """
    return get_initial_index_structure()

@mcp.tool()
def test_load_index() -> dict:
    """
    Loads data/index.json. Seeds a fresh index file if missing or empty.
    """
    return load_index()

@mcp.tool()
def test_save_index(index_data: dict) -> dict:
    """
    Atomically writes index_data to data/index.json using a temp file.
    """
    return save_index(index_data)

@mcp.tool()
def test_add_memory_to_index(memory_entry: dict) -> dict:
    """
    Adds a new memory metadata entry to index.json and updates stats & tag maps.
    """
    return add_memory_to_index(memory_entry)


@mcp.tool()
def test_chunk_text(
    memory_id: str,
    text: str,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> dict:
    """
    Chunks text accurately using the exact token limits of the active model.
    """
    result = chunk_text(memory_id, text, model_name)
    return {
        "status": "success",
        "chunked_data": result,
    }

@mcp.tool()
def test_generate_openai_embeddings(
    texts: List[str],
    api_key: str,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> dict:
    """
    Generates embeddings using OpenAI API. 
    """
    result = generate_openai_embeddings(texts, model_name, api_key)
    return {
        "status": "success",
        "embeddings": result,
    }

@mcp.tool()
def test_generate_ollama_embeddings(
    texts: List[str], 
    model_name: str = OLLAMA_EMBEDDING_MODEL
) -> dict:
    """
    Generates embeddings using Ollama API. 
    """
    result = generate_ollama_embeddings(texts, model_name)
    return {
        "status": "success",
        "embeddings": result,
    }


@mcp.tool()
def test_generate_local_embeddings(
    texts: List[str],
    model_name: str = FALLBACK_EMBEDDING_MODEL,
) -> dict:
    """
    Generates embeddings using local SentenceTransformer.
    """
    result = generate_local_embeddings(texts, model_name=model_name)
    return {
        "status": "success",
        "embeddings": result,
    }
    


@mcp.tool()
def list_available_models(
    base_url: str = "",
    api_key: str = "",
) -> dict:
    """
    Fetches all available models from base_url/api_key and bifurcates them into embedding vs generative models.
    """
    return fetch_and_bifurcate_models(
        base_url=base_url if base_url else None,
        api_key=api_key if api_key else None,
    )



def main():
    sys.stderr.write("Started Memorize MCP Server\n")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
