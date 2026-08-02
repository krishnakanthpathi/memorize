import sys
from mcp.server.fastmcp import FastMCP

from core.id_generator import generate_memory_id, generate_chunk_id
from core.hashing import compute_string_hash

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


def main():
    sys.stderr.write("Started Memorize MCP Server\n")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
