import os
import sys
import argparse
from mcp.server.fastmcp import FastMCP

from mcp.config import DEFAULT_PORT, DEFAULT_TRANSPORT, SERVER_NAME
from mcp.tools import register_all_tools
from storage.db_manager import init_db


def create_mcp_server(host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> FastMCP:
    """Create and configure FastMCP server instance with all tools registered."""
    server = FastMCP(SERVER_NAME, host=host, port=port)
    register_all_tools(server)
    return server


# Default singleton FastMCP instance
mcp = create_mcp_server()


class AcceptHeaderMiddleware:
    """Ensures incoming requests accept application/json and text/event-stream."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            if b"accept" not in headers or headers[b"accept"] == b"*/*" or b"application/json" not in headers[b"accept"]:
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", b"application/json, text/event-stream, */*"))
                scope["headers"] = new_headers
        await self.app(scope, receive, send)


def create_universal_mcp_app():
    """Builds a universal MCP app supporting Streamable HTTP (Gemini), SSE (Claude), and OAuth probes."""
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from mcp.server.fastmcp.server import StreamableHTTPASGIApp
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=mcp._event_store,
        retry_interval=mcp._retry_interval,
        json_response=True,
        stateless=True,
        security_settings=mcp.settings.transport_security,
    )

    streamable_app = StreamableHTTPASGIApp(session_manager)

    async def oauth_probe(request):
        return JSONResponse({"resource": SERVER_NAME, "scopes_supported": []})

    async def root_info(request):
        return JSONResponse({
            "name": SERVER_NAME,
            "version": "2.0.0",
            "status": "active",
            "mcp_version": "1.0",
            "tools": [t.name for t in mcp._tool_manager.list_tools()],
        })

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        ),
        Middleware(AcceptHeaderMiddleware),
    ]

    routes = [
        Route("/.well-known/oauth-protected-resource", endpoint=oauth_probe, methods=["GET", "HEAD", "OPTIONS"]),
        Route("/.well-known/oauth-protected-resource/sse", endpoint=oauth_probe, methods=["GET", "HEAD", "OPTIONS"]),
        Route("/.well-known/oauth-protected-resource/mcp", endpoint=oauth_probe, methods=["GET", "HEAD", "OPTIONS"]),
        Route("/info", endpoint=root_info, methods=["GET", "HEAD", "OPTIONS"]),
        Route("/mcp", endpoint=streamable_app, methods=["GET", "POST", "HEAD", "OPTIONS"]),
        Route("/sse", endpoint=streamable_app, methods=["GET", "POST", "HEAD", "OPTIONS"]),
        Route("/", endpoint=streamable_app, methods=["GET", "POST", "HEAD", "OPTIONS"]),
    ]

    app = Starlette(
        routes=routes,
        middleware=middleware,
        lifespan=lambda a: session_manager.run(),
    )
    return app


def run_mcp_server(transport: str = None, host: str = "0.0.0.0", port: int = DEFAULT_PORT):
    """Initializes SQLite database and runs the FastMCP server."""
    if transport is None:
        transport = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT)
    
    port_env = os.getenv("MCP_PORT")
    if port_env:
        try:
            port = int(port_env)
        except ValueError:
            pass

    mcp.settings.host = host
    mcp.settings.port = port

    sys.stderr.write(f"Started {SERVER_NAME} (transport: {transport}, host: {host}, port: {port})\n")
    init_db()

    if transport in ("sse", "streamable-http", "http"):
        import uvicorn
        sys.stderr.write(f"Universal MCP Endpoint: http://{host}:{port}/sse or http://{host}:{port}/mcp\n")
        app = create_universal_mcp_app()
        uvicorn.run(app, host=host, port=port)
    else:
        mcp.run(transport=transport)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Memorize FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default=DEFAULT_TRANSPORT, help="Transport protocol (default: stdio)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for SSE/HTTP transport (default: 7777)")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    args, _ = parser.parse_known_args()

    run_mcp_server(transport=args.transport, host=args.host, port=args.port)


