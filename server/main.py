import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .mem0_service import Mem0Service
from .routes import setup_routes

DATA_DIR = os.getenv("MEM0_DATA_DIR", "/app/data")
STATIC_DIR = os.getenv("MEM0_STATIC_DIR", "/app/static")

app = FastAPI(
    title="Mem0 Local Memory Manager & Server",
    version="1.0.0",
    description="100% Local Self-Hosted Memory Server for AI Assistants & Coding Agents"
)

# Enable CORS for local cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mem0 Core Service
mem0_service = Mem0Service(data_dir=DATA_DIR)

# Mount API routes
api_router = setup_routes(mem0_service)
app.include_router(api_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "mem0-local-server",
        "data_dir": DATA_DIR
    }


# Mount Web Dashboard static assets
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def serve_dashboard():
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Mem0 Server running. Static files not found."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "28842"))
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=False)
