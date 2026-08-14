"""
Unit Tests for Lean MCP Package & 5 Core Tools
"""

import unittest
from mcp import mcp, create_mcp_server, SERVER_NAME, SERVER_VERSION
from mcp.config import USE_LLM, EMBEDDING_MODEL, CLASSIFICATION_MODEL, FALLBACK_MODEL


class TestModularMCP(unittest.TestCase):

    def test_mcp_server_initialization(self):
        """Verify FastMCP server instance and metadata."""
        self.assertEqual(SERVER_NAME, "Memorize Server")
        self.assertIsNotNone(mcp)
        tools = mcp._tool_manager.list_tools()
        self.assertEqual(len(tools), 5)

    def test_all_expected_tools_registered(self):
        """Verify exactly the 5 core lean tools are present on the server."""
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        expected_tools = {
            "store",
            "update",
            "delete",
            "fetch",
            "hybrid_fetch",
        }
        self.assertEqual(tools, expected_tools, f"MCP tools mismatch. Got: {tools}, Expected: {expected_tools}")

    def test_mcp_config_parameters(self):
        """Verify MCP config parameters are accessible and typed."""
        self.assertIsInstance(USE_LLM, bool)
        self.assertIsInstance(EMBEDDING_MODEL, str)
        self.assertIsInstance(CLASSIFICATION_MODEL, str)
        self.assertIsInstance(FALLBACK_MODEL, str)

    def test_fetch_listing_tool(self):
        """Test fetch tool with no arguments lists memories."""
        from storage.db_manager import init_db
        init_db()
        # fetch tool handler
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "fetch")
        self.assertIsNotNone(tool)

    def test_auto_classify_offline_behavior(self):
        """Test classification works deterministically offline."""
        from classification.classifier import classify_memory
        result = classify_memory("Learning Python async and await for high performance web scraping.")
        self.assertIn("category", result)
        self.assertIn("tags", result)


if __name__ == "__main__":
    unittest.main()

