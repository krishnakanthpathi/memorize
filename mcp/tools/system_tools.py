"""
System & Maintenance MCP Tools
Handles file reorganization, storage audit, and slugification.
"""

from storage.organization_manager import reorganize_memories


def register_system_tools(mcp):
    """Register system and maintenance tools on the FastMCP server instance."""

    @mcp.tool()
    def organize_memory_files(auto_fix: bool = True) -> dict:
        """
        Audits and reorganizes memory Markdown files into their correct category folders,
        slugifies filenames, cleans empty directories, and refreshes indexes.
        """
        return reorganize_memories(auto_fix=auto_fix)
