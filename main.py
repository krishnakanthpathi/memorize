from storage.markdown_handler import delete_markdown_file
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from core.id_generator import generate_memory_id, generate_chunk_id
from core.hashing import compute_string_hash
from storage.markdown_handler import create_markdown_file, read_markdown_file

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

def main():
    sys.stderr.write("Started Memorize MCP Server\n")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
