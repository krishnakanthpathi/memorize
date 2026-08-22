"""
Category Management MCP Tools
Handles directory creation, listing, and deletion of categories.
"""

import shutil
from utils import get_available_categories, get_category_dir


def register_category_tools(mcp):
    """Register category management tools on the FastMCP server instance."""


    @mcp.tool()
    def add_category(category: str) -> dict:
        """
        Dynamically creates category storage directory.
        """
        cat_dir = get_category_dir(category)
        return {"status": "success", "category": category, "path": str(cat_dir)}

    @mcp.tool()
    def delete_category(category: str) -> dict:
        """
        Deletes a category directory on disk and purges category records from SQLite.
        """
        cat_dir = get_category_dir(category)
        if cat_dir.exists():
            shutil.rmtree(cat_dir)
        return {"status": "success", "category": category}
