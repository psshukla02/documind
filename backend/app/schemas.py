"""Pydantic request/response models."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class IngestURLRequest(BaseModel):
    url: str = Field(..., description="HTTP/HTTPS URL to scrape and ingest")

    @field_validator("url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v


class IngestTextRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    text: str = Field(..., min_length=20)
    source: str = Field(default="manual", max_length=300)


class IngestResponse(BaseModel):
    doc_id: str
    source: str
    title: str
    chunks: int
    latency_ms: float


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    id: str
    title: str
    url: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    retrieval_score: float
    latency_ms: float
    tokens: Optional[int] = None
    model: str


class DocsRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    code: Optional[str] = Field(default=None, max_length=8000)
    use_retrieval: bool = True


class DocsResponse(BaseModel):
    markdown: str
    citations: list[Citation]
    latency_ms: float
    model: str


class SyntheticRequest(BaseModel):
    doc_id: Optional[str] = None
    n_pairs: int = Field(default=5, ge=1, le=20)


class SyntheticPair(BaseModel):
    question: str
    answer: str
    category: Literal["factual", "reasoning", "edge_case", "example"] | str = "factual"
    difficulty: Literal["easy", "medium", "hard"] | str = "medium"


class SyntheticResponse(BaseModel):
    title: str
    source: str
    pairs: list[SyntheticPair]
    latency_ms: float
    model: str


class DocumentSummary(BaseModel):
    doc_id: str
    source: str
    title: str
    chunks: int


class KnowledgeBaseResponse(BaseModel):
    documents: list[DocumentSummary]
    total_chunks: int


class MetricsResponse(BaseModel):
    uptime_seconds: float
    counters: dict[str, int]
    chat: dict[str, Any]
    ingest: dict[str, Any]
    recent_events: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    stub_mode: bool
    vector_store_size: int
    model: str


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=300)
    num_queries: int = Field(default=3, ge=1, le=5)
    per_query: int = Field(default=3, ge=1, le=5)


class ResearchSummary(BaseModel):
    topic: str
    queries: list[str]
    scraped: int
    ingested: int
    skipped: int
    total_chunks: int
    documents: list[dict]
    elapsed_ms: float


class ResearchResponse(BaseModel):
    summary: ResearchSummary
    events: list[dict]
