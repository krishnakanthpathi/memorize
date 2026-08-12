from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, memories, models, search, system

app = FastAPI(
    title="Memorize API Service",
    description="REST API Service powered by LangChain & LangGraph GraphRAG Engine",
    version="2.0.0",
)

# Enable CORS for local web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular route handlers
app.include_router(memories.router)
app.include_router(models.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(system.router)


@app.get("/")
def read_root():
    return {
        "service": "Memorize LangGraph REST API Service",
        "status": "online",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=6999, reload=True)
