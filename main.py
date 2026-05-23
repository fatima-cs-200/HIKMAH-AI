"""
HIKMAH AI — FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router  # noqa: E402  (sys.path set by launcher)
from utils.config import settings
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Ollama endpoint: {settings.ollama_base_url} | Model: {settings.ollama_model}")
    logger.info(f"ChromaDB path: {settings.chroma_persist_dir}")
    yield
    logger.info(f"{settings.app_name} shutting down.")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-grade Islamic RAG API — retrieves authentic knowledge "
        "from the Quran and Sahih Bukhari using semantic search and Llama 3."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Streamlit frontend (and any local dev origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routes under /api/v1
app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )
