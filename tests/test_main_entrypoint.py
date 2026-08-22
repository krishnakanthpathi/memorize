"""
Unit Tests for main.py Master Entrypoint & CLI Options
"""

import sys
import unittest
from unittest.mock import patch, MagicMock


class TestMainEntrypoint(unittest.TestCase):

    @patch("main.run_all")
    def test_main_default_dev_start(self, mock_run_all):
        with patch.object(sys, "argv", ["main.py", "start"]), \
             patch("sys.stdin.isatty", return_value=True):
            from main import main
            main()
            mock_run_all.assert_called_once()

    @patch("main.run_backend")
    def test_main_backend_subcommand(self, mock_run_backend):
        with patch.object(sys, "argv", ["main.py", "backend", "--port", "7788", "--no-reload"]):
            from main import main
            main()
            mock_run_backend.assert_called_once_with(
                host="0.0.0.0",
                port=7788,
                reload=False,
            )

    @patch("main.run_backend")
    def test_main_server_alias(self, mock_run_backend):
        with patch.object(sys, "argv", ["main.py", "server"]):
            from main import main
            main()
            mock_run_backend.assert_called_once()

    @patch("main.run_frontend")
    def test_main_frontend_subcommand(self, mock_run_frontend):
        with patch.object(sys, "argv", ["main.py", "frontend", "--frontend-port", "9000", "--port", "7777"]):
            from main import main
            main()
            mock_run_frontend.assert_called_once_with(
                host="0.0.0.0",
                frontend_port=9000,
                backend_port=7777,
            )

    @patch("main.run_mcp_server")
    def test_main_mcp_subcommand(self, mock_run_mcp):
        with patch.object(sys, "argv", ["main.py", "mcp", "--transport", "sse", "--port", "7799"]):
            from main import main
            main()
            mock_run_mcp.assert_called_once_with(
                transport="sse",
                host="0.0.0.0",
                port=7799,
            )

    @patch("main.run_mcp_server")
    def test_main_piped_non_interactive_defaults_to_mcp(self, mock_run_mcp):
        """Verify Claude Desktop/Cursor pipe invocations (isatty=False) default to FastMCP stdio."""
        with patch.object(sys, "argv", ["main.py"]), \
             patch("sys.stdin.isatty", return_value=False):
            from main import main
            main()
            mock_run_mcp.assert_called_once_with(
                transport="stdio",
                host="0.0.0.0",
                port=7777,
            )

    @patch("main.run_all")
    def test_main_flag_aliases(self, mock_run_all):
        with patch.object(sys, "argv", ["main.py", "--all"]):
            from main import main
            main()
            mock_run_all.assert_called_once()

    @patch("cli.main")
    def test_main_cli_subcommand(self, mock_cli_main):
        with patch.object(sys, "argv", ["main.py", "cli"]):
            from main import main
            main()
            mock_cli_main.assert_called_once()


if __name__ == "__main__":
    unittest.main()
