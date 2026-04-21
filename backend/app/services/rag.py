"""RAG pipeline: ingest, retrieve, and generate grounded answers."""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import get_metrics
from app.prompts.templates import (
    CHAT_SYSTEM,
    DOC_GEN_SYSTEM,
    SYNTHETIC_SYSTEM,
    RetrievedChunk,
    build_chat_user_prompt,
    build_doc_gen_user_prompt,
    build_synthetic_user_prompt,
)
from app.services.chunker import chunk_text
from app.services.llm import get_llm
from app.services.scraper import scrape_url
from app.services.vector_store import SearchHit, get_vector_store

logger = get_logger(__name__)


@dataclass
class IngestResult:
    doc_id: str
    source: str
    title: str
    chunks: int
    latency_ms: float


@dataclass
class ChatResult:
    answer: str
    citations: list[dict[str, Any]]
    confidence: float
    retrieval_score: float
    latency_ms: float
    tokens: int | None
    model: str


# ---------- Ingestion ----------


def ingest_url(url: str) -> IngestResult:
    t0 = time.time()
    page = scrape_url(url)
    return _ingest(page.title, page.url, page.text, t0)


def ingest_text(title: str, text: str, source: str = "manual") -> IngestResult:
    t0 = time.time()
    return _ingest(title, source, text, t0)


def _ingest(title: str, source: str, text: str, t0: float) -> IngestResult:
    s = get_settings()
    chunks = chunk_text(text, chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)
    if not chunks:
        raise ValueError("No chunks produced from content")

    llm = get_llm()
    embeddings = llm.embed([c.text for c in chunks])

    store = get_vector_store()
    doc_id = str(uuid.uuid4())
    added = store.add(
        doc_id=doc_id,
        source=source,
        title=title,
        chunks=[c.text for c in chunks],
        embeddings=embeddings,
    )

    latency_ms = round((time.time() - t0) * 1000, 1)
    get_metrics().record(
        {"kind": "ingest", "source": source, "title": title, "chunks": added, "latency_ms": latency_ms}
    )
    get_metrics().bump("ingest_requests")
    logger.info("Ingested %s: %d chunks in %sms", title, added, latency_ms)
    return IngestResult(doc_id=doc_id, source=source, title=title, chunks=added, latency_ms=latency_ms)


# ---------- Retrieval ----------


def _retrieve(query: str, k: int) -> list[SearchHit]:
    llm = get_llm()
    q_vec = llm.embed([query])[0]
    return get_vector_store().search(q_vec, k=k)


def _hits_to_retrieved(hits: list[SearchHit]) -> list[RetrievedChunk]:
    out = []
    for i, h in enumerate(hits, start=1):
        out.append(
            RetrievedChunk(
                idx=i,
                title=h.record.title,
                url=h.record.source,
                text=h.record.text,
                score=h.score,
            )
        )
    return out


# ---------- Chat ----------


def chat(query: str, top_k: int | None = None) -> ChatResult:
    t0 = time.time()
    if not query or not query.strip():
        raise ValueError("Query is empty")

    s = get_settings()
    k = top_k or s.top_k
    hits = _retrieve(query, k=k)
    retrieved = _hits_to_retrieved(hits)

    user_prompt = build_chat_user_prompt(query, retrieved)
    llm_resp = get_llm().chat(system=CHAT_SYSTEM, user=user_prompt, temperature=0.2, max_tokens=900)

    retrieval_score = round(
        sum(c.score for c in retrieved) / len(retrieved), 3
    ) if retrieved else 0.0

    # Confidence heuristic: weight top-hit score + coverage + presence of citations.
    top_score = retrieved[0].score if retrieved else 0.0
    cited = len(re.findall(r"\[S\d+\]", llm_resp["text"]))
    coverage = min(cited / max(len(retrieved), 1), 1.0) if retrieved else 0.0
    confidence = round(0.6 * max(top_score, 0.0) + 0.4 * coverage, 3)

    citations = [
        {"id": f"S{c.idx}", "title": c.title, "url": c.url, "score": round(c.score, 3)}
        for c in retrieved
    ]

    latency_ms = round((time.time() - t0) * 1000, 1)
    get_metrics().record(
        {
            "kind": "chat",
            "query": query[:160],
            "latency_ms": latency_ms,
            "retrieval_score": retrieval_score,
            "confidence": confidence,
            "tokens": llm_resp.get("tokens"),
            "hits": len(retrieved),
        }
    )
    get_metrics().bump("chat_requests")

    return ChatResult(
        answer=llm_resp["text"],
        citations=citations,
        confidence=confidence,
        retrieval_score=retrieval_score,
        latency_ms=latency_ms,
        tokens=llm_resp.get("tokens"),
        model=llm_resp.get("model", "unknown"),
    )


# ---------- Doc generation ----------


def generate_documentation(topic: str, code: str | None = None, use_retrieval: bool = True) -> dict:
    t0 = time.time()
    if not topic or not topic.strip():
        raise ValueError("Topic is empty")

    retrieved: list[RetrievedChunk] = []
    if use_retrieval:
        probe = f"{topic}\n{code or ''}".strip()
        retrieved = _hits_to_retrieved(_retrieve(probe, k=get_settings().top_k))

    user_prompt = build_doc_gen_user_prompt(topic, code, retrieved)
    llm_resp = get_llm().chat(system=DOC_GEN_SYSTEM, user=user_prompt, temperature=0.3, max_tokens=1400)

    latency_ms = round((time.time() - t0) * 1000, 1)
    get_metrics().record({"kind": "generate_docs", "topic": topic[:120], "latency_ms": latency_ms})
    get_metrics().bump("generate_docs_requests")

    return {
        "markdown": llm_resp["text"],
        "citations": [
            {"id": f"S{c.idx}", "title": c.title, "url": c.url, "score": round(c.score, 3)}
            for c in retrieved
        ],
        "latency_ms": latency_ms,
        "model": llm_resp.get("model", "unknown"),
    }


# ---------- Synthetic data ----------


def generate_synthetic(doc_id: str | None, n_pairs: int = 5) -> dict:
    t0 = time.time()
    store = get_vector_store()

    if doc_id:
        recs = store.get_document_chunks(doc_id)
        if not recs:
            raise ValueError(f"No document with id={doc_id}")
    else:
        recs = store._records[:]  # snapshot; read-only intent
        if not recs:
            raise ValueError("Knowledge base is empty; ingest at least one document first.")

    title = recs[0].title
    url = recs[0].source
    joined = "\n\n".join(r.text for r in recs)
    # Cap source length so prompts stay small and cheap.
    if len(joined) > 6000:
        joined = joined[:6000] + "\n...[truncated]"

    user_prompt = build_synthetic_user_prompt(joined, title, url, n_pairs)
    llm_resp = get_llm().chat(system=SYNTHETIC_SYSTEM, user=user_prompt, temperature=0.6, max_tokens=1200)

    pairs = _parse_synthetic_json(llm_resp["text"])

    latency_ms = round((time.time() - t0) * 1000, 1)
    get_metrics().record(
        {"kind": "synthetic", "n": len(pairs), "title": title, "latency_ms": latency_ms}
    )
    get_metrics().bump("synthetic_requests")

    return {
        "title": title,
        "source": url,
        "pairs": pairs,
        "latency_ms": latency_ms,
        "model": llm_resp.get("model", "unknown"),
    }


def _parse_synthetic_json(text: str) -> list[dict]:
    """Extract the JSON object even if the LLM added stray prose."""
    # Fast path
    try:
        data = json.loads(text)
        return list(data.get("pairs", []))
    except Exception:
        pass

    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return list(data.get("pairs", []))
        except Exception:
            pass

    logger.warning("Synthetic JSON parse failed; returning empty list. Raw head: %s", text[:200])
    return []
