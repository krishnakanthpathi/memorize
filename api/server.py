from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import (
    audit_router,
    chat_router,
    memories_router,
    models_router,
    search_router,
    settings_router,
    system_router,
)
from mcp.service import mcp, SERVER_NAME, AcceptHeaderMiddleware
from mcp.server.fastmcp.server import StreamableHTTPASGIApp
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Initialize Streamable HTTP session manager for Google Gemini, Claude, and remote clients
session_manager = StreamableHTTPSessionManager(
    app=mcp._mcp_server,
    event_store=mcp._event_store,
    retry_interval=mcp._retry_interval,
    json_response=True,
    stateless=True,
    security_settings=mcp.settings.transport_security,
)
streamable_app = StreamableHTTPASGIApp(session_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with session_manager.run():
        yield


app = FastAPI(
    title="Memorize API & Universal MCP Service",
    description="Unified REST API & FastMCP Service for Memorize Personal Knowledge Base",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for web applications and MCP clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AcceptHeaderMiddleware)

# Register modularized REST routers
app.include_router(memories_router)
app.include_router(audit_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(system_router)
app.include_router(models_router)
app.include_router(settings_router)


# OAuth Probes for Google Gemini Custom Connected Apps
@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/sse")
@app.get("/.well-known/oauth-protected-resource/mcp")
@app.head("/.well-known/oauth-protected-resource")
@app.head("/.well-known/oauth-protected-resource/sse")
@app.head("/.well-known/oauth-protected-resource/mcp")
def oauth_probe():
    return JSONResponse({"resource": SERVER_NAME, "scopes_supported": []})


@app.get("/info")
def mcp_info():
    return {
        "name": SERVER_NAME,
        "version": "2.0.0",
        "status": "active",
        "mcp_version": "1.0",
        "tools": [t.name for t in mcp._tool_manager.list_tools()],
    }


@app.api_route("/sse", methods=["GET", "POST", "HEAD", "OPTIONS"])
@app.api_route("/sse/{path:path}", methods=["GET", "POST", "HEAD", "OPTIONS"])
@app.api_route("/mcp", methods=["GET", "POST", "HEAD", "OPTIONS"])
@app.api_route("/mcp/{path:path}", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def mcp_endpoint(request: Request):
    """Directly route Streamable HTTP and SSE requests to the FastMCP ASGI app."""
    return await streamable_app(request.scope, request.receive, request._send)


@app.get("/")
def read_root():
    return {
        "service": "Memorize REST API Service",
        "status": "online",
        "version": "2.0.0",
        "mcp_endpoint": "/sse",
        "tools": [t.name for t in mcp._tool_manager.list_tools()],
    }



if __name__ == "__main__":
    import uvicorn
    from config.constants import BACKEND_PORT

    uvicorn.run("api.server:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)



