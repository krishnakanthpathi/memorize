"""
MCP Tools Package
Exports lean core MCP tools for Memorize (store, update, delete, fetch, hybrid_fetch).
"""

from mcp.tools.memory_tools import register_memory_tools


def register_all_tools(mcp):
    """Register the 5 lean core MCP tools on the FastMCP instance."""
    register_memory_tools(mcp)
    return mcp

