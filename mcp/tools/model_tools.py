"""
Model & Vector DB Inspection MCP Tools
Handles LLM/embedding model discovery and ChromaDB chunk inspection.
"""

from utils.model_fetcher import fetch_and_bifurcate_models
from vector.vector_db import peek_vector_db


def register_model_tools(mcp):
    """Register model discovery and vector DB inspection tools on the FastMCP server instance."""

    @mcp.tool()
    def list_available_models(
        base_url: str = "",
        api_key: str = "",
    ) -> dict:
        """
        Fetches available models and bifurcates into embedding vs generative models.
        """
        return fetch_and_bifurcate_models(
            base_url=base_url if base_url else None,
            api_key=api_key if api_key else None,
        )

    @mcp.tool()
    def peek_vector_db_chunks(limit: int = 10) -> dict:
        """
        Inspects stored vector chunks in ChromaDB.
        """
        return peek_vector_db(limit=limit)
