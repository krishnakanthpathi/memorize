from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import (
    audit_router,
    documents_router,
    media_router,
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
app.include_router(documents_router)
app.include_router(media_router)
app.include_router(audit_router)
app.include_router(search_router)
app.include_router(system_router)
app.include_router(models_router)
app.include_router(settings_router)



# OAuth Probes for Google Gemini Custom Connected Apps & Claude
@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/sse")
@app.get("/.well-known/oauth-protected-resource/mcp")
@app.head("/.well-known/oauth-protected-resource")
@app.head("/.well-known/oauth-protected-resource/sse")
@app.head("/.well-known/oauth-protected-resource/mcp")
def oauth_probe():
    return JSONResponse({"resource": SERVER_NAME, "scopes_supported": []})


@app.get("/info")
@app.head("/info")
def mcp_server_info_probe():
    tools_list = [
        {"name": t.name, "description": t.description}
        for t in mcp._tool_manager.list_tools()
    ]
    return JSONResponse({
        "name": SERVER_NAME,
        "version": "2.0.0",
        "description": "FastMCP Personal Memory & Knowledge Base Server",
        "status": "online",
        "mcp_version": "1.0",
        "tools_count": len(tools_list),
        "tools": tools_list,
        "endpoints": {
            "mcp": "/mcp",
            "sse": "/sse",
            "info": "/info",
        }
    })


@app.get("/")
def root_endpoint():
    return {
        "service": "Memorize REST API & Universal FastMCP Server",
        "version": "2.0.0",
        "status": "healthy",
        "endpoints": {
            "memories": "/api/memories",
            "search": "/api/search",
            "audit": "/api/audit",
            "models": "/api/models",
            "settings": "/api/settings",
            "mcp": "/mcp",
            "sse": "/sse",
            "info": "/info",
        },
    }


# Mount streamable HTTP / SSE MCP Apps
app.mount("/mcp", streamable_app)
app.mount("/sse", streamable_app)

