"""
Memorize MCP (Model Context Protocol) Package
Provides modular FastMCP server, bifurcated tool suites, and configuration.
"""

import site
from pathlib import Path

# Extend namespace __path__ to merge third-party 'mcp' library modules (types, server, fastmcp)
for _sp in site.getsitepackages():
    _mcp_site = Path(_sp) / "mcp"
    if _mcp_site.exists() and str(_mcp_site) not in __path__:
        __path__.append(str(_mcp_site))

from mcp.config import SERVER_DESCRIPTION, SERVER_NAME, SERVER_VERSION
from mcp.service import create_mcp_server, mcp, run_mcp_server
from mcp.tools import register_all_tools

__all__ = [
    "SERVER_NAME",
    "SERVER_VERSION",
    "SERVER_DESCRIPTION",
    "mcp",
    "create_mcp_server",
    "run_mcp_server",
    "register_all_tools",
]
