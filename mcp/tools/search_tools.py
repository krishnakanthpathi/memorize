"""
Search & Classification MCP Tools
Handles hybrid relevance search, pure vector semantic similarity, and auto-classification.
"""

from typing import List, Optional, Union

from classification.classifier import classify_memory
from search.relevance_scorer import (
    search_hybrid_relevance,
    search_vector_similarity,
)


def register_search_tools(mcp):
    """Register search and classification tools on the FastMCP server instance."""

    @mcp.tool()
    def hybrid_search_memories(
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> Union[List[dict], dict]:
        """
        Performs hybrid weighted relevance search combining Vector Similarity (50%),
        Tag Match (30%), and Category Match (20%) to return ranked top memories.
        """
        return search_hybrid_relevance(
            query=query,
            category_filter=category_filter if category_filter else None,
            top_k=top_k,
        )

    @mcp.tool()
    def search_memory(
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> Union[List[dict], dict]:
        """
        Performs pure similarity search using vector embeddings to find and rank memories based on query similarity.
        """
        return search_vector_similarity(
            query=query,
            category_filter=category_filter if category_filter else None,
            top_k=top_k,
            threshold=min_similarity,
        )

    @mcp.tool()
    def auto_classify_memory(text: str) -> dict:
        """
        Analyzes raw text, automatically assigns a category, and extracts relevant tags.
        """
        return classify_memory(text=text)
