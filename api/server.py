from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    audit_router,
    chat_router,
    memories_router,
    models_router,
    search_router,
    settings_router,
    system_router,
)

app = FastAPI(
    title="Memorize API Service",
    description="REST API Service for Memorize Memory Assistant & Vector Engine",
    version="1.0.0",
)

# Enable CORS for local web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modularized routers
app.include_router(memories_router)
app.include_router(audit_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(system_router)
app.include_router(models_router)
app.include_router(settings_router)



@app.get("/")
def read_root():
    return {
        "service": "Memorize REST API Service",
        "status": "online",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    from config.constants import BACKEND_PORT

    uvicorn.run("api.server:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)


