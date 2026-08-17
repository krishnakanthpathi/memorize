"""
Unit Tests for Lean MCP Package & Core Tools
"""

import unittest
from mcp import mcp, create_mcp_server, SERVER_NAME, SERVER_VERSION
from mcp.config import USE_LLM, EMBEDDING_MODEL, CLASSIFICATION_MODEL, FALLBACK_MODEL
from mcp.tools.memory_tools import list_memories, get_categories


class TestModularMCP(unittest.TestCase):

    def test_mcp_server_initialization(self):
        """Verify FastMCP server instance and metadata."""
        self.assertEqual(SERVER_NAME, "Memorize Server")
        self.assertIsNotNone(mcp)
        tools = mcp._tool_manager.list_tools()
        self.assertEqual(len(tools), 12)

    def test_all_expected_tools_registered(self):
        """Verify exactly the expected core tools are present on the server."""
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        expected_tools = {
            "store",
            "update",
            "delete",
            "fetch",
            "hybrid_fetch",
            "list_memories",
            "get_categories",
            "merge_memories",
            "find_correlated_memories",
            "organize_memory",
            "generate_title",
            "organize_selection",
        }
        self.assertEqual(tools, expected_tools, f"MCP tools mismatch. Got: {tools}, Expected: {expected_tools}")

    def test_mcp_config_parameters(self):
        """Verify MCP config parameters are accessible and typed."""
        self.assertIsInstance(USE_LLM, bool)
        self.assertIsInstance(EMBEDDING_MODEL, str)
        self.assertIsInstance(CLASSIFICATION_MODEL, str)
        self.assertIsInstance(FALLBACK_MODEL, str)

    def test_list_memories_tool(self):
        """Test list_memories tool execution."""
        from storage.db_manager import init_db
        init_db()
        res = list_memories()
        self.assertEqual(res.get("status"), "success")
        self.assertIn("memories", res)
        self.assertIn("total_count", res)

    def test_get_categories_tool(self):
        """Test get_categories tool execution and structure."""
        res = get_categories()
        self.assertEqual(res.get("status"), "success")
        self.assertIn("categories", res)
        self.assertGreaterEqual(res.get("total_categories", 0), 11)
        cats = [c["category"] for c in res["categories"]]
        self.assertIn("personal", cats)
        self.assertIn("development", cats)
        self.assertIn("projects", cats)

    def test_auto_classify_offline_behavior(self):
        """Test classification works deterministically offline."""
        from classification.classifier import classify_memory
        result = classify_memory("Learning Python async and await for high performance web scraping.")
        self.assertIn("category", result)
        self.assertIn("tags", result)


if __name__ == "__main__":
    unittest.main()


