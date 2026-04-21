"""FastAPI entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.logging import get_logger
from app.routers import agent, chat, docs, ingest, metrics, synthetic

logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="AI Technical Documentation Assistant",
    description=(
        "RAG-powered documentation assistant with synthetic data generation "
        "and structured prompt engineering."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(docs.router, prefix="/api")
app.include_router(synthetic.router, prefix="/api")
app.include_router(agent.router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Technical Documentation Assistant",
        "version": __version__,
        "docs": "/docs",
        "api_prefix": "/api",
    }
