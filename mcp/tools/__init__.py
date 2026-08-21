from mcp.tools.category_tools import register_category_tools
from mcp.tools.media_tools import register_media_tools
from mcp.tools.memory_tools import register_memory_tools
from mcp.tools.model_tools import register_model_tools
from mcp.tools.search_tools import register_search_tools
from mcp.tools.system_tools import register_system_tools


def register_all_tools(mcp):
    """Register all memory, document/media, search, model, and system MCP tools."""
    register_memory_tools(mcp)
    register_media_tools(mcp)
    register_category_tools(mcp)
    register_search_tools(mcp)
    register_model_tools(mcp)
    register_system_tools(mcp)
    return mcp



