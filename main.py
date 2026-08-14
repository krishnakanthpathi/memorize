"""
Memorize Master Entrypoint
Runs FastMCP Model Context Protocol Server or delegates to interactive CLI.
"""

import sys
import argparse
from mcp import mcp, run_mcp_server
from mcp.config import DEFAULT_PORT, DEFAULT_TRANSPORT
import cli


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        sys.argv.pop(1)
        cli.main()
        return

    parser = argparse.ArgumentParser(description="Run Memorize FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default=DEFAULT_TRANSPORT, help="Transport protocol (stdio, sse, streamable-http)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for SSE/HTTP transport (default: 7777)")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    args, _ = parser.parse_known_args()

    run_mcp_server(transport=args.transport, host=args.host, port=args.port)



if __name__ == "__main__":
    main()

