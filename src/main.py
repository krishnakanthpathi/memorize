
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Memorize Server")


@mcp.tool()
def ping(message: str = "hello") -> str:
    """
    Test tool to verify that the Memorize MCP server is online and responding.
    """
    return f"Memorize MCP Server is active! You sent: '{message}'"


# -------------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------------
def main():
    print("Started Mcp Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()