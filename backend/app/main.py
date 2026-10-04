from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.models.database import init_db
from backend.app.api.endpoints import router as api_router
from backend.app.services.demo_service import DemoService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    # Initialize demo dataset on startup so demonstration is immediately ready
    try:
        DemoService.ensure_demo_dataset()
    except Exception as e:
        print(f"[Startup] Demo dataset init notice: {e}")
    yield

app = FastAPI(
    title=settings.app_name,
    description="SIGNAL — AI-Powered Video Intelligence & Search Workstation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    settings.frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # hackathon demo local friendly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "tagline": "SEE WHAT MATTERS.",
        "description": "Turn video into searchable, explainable events.",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
