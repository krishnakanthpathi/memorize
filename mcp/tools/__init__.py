"""
MCP Tools Package
Exports core MCP tools for Memorize (store, update, delete, fetch, hybrid_fetch, list_memories, get_categories).
"""

from mcp.tools.memory_tools import register_memory_tools


def register_all_tools(mcp):
    """Register all memory and category MCP tools on the FastMCP instance."""
    register_memory_tools(mcp)
    return mcp


