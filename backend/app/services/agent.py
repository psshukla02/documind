"""Autonomous research agent.

Loop:
    1. Plan N diverse search queries for the topic (LLM).
    2. For each query: search the web (DuckDuckGo HTML, no API key).
    3. For each top result (dedup + blacklist filtered):
        a. Scrape the page.
        b. Ask the LLM to judge relevance (keep / skip).
        c. If "keep", chunk + embed + add to the vector store.
    4. Yield a structured event stream; the caller can either consume it
       live (SSE) or collect it into a final report.

Stub-mode behavior:
    - Query planning returns simple topic variants instead of calling the LLM.
    - Relevance judge keeps any page with > 400 characters of extracted text.
    - Real web fetches still run so the end-to-end flow is honest.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Iterator

from app.core.logging import get_logger
from app.core.metrics import get_metrics
from app.prompts.templates import (
    AGENT_PLANNER_SYSTEM,
    RELEVANCE_JUDGE_SYSTEM,
    build_judge_prompt,
    build_plan_queries_prompt,
)
from app.services import rag
from app.services.llm import get_llm
from app.services.scraper import scrape_url
from app.services.search import SearchResult, is_blacklisted, search_web
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)


@dataclass
class ResearchConfig:
    topic: str
    num_queries: int = 3
    per_query: int = 3
    min_chars: int = 400  # skip pages with less than this after cleaning


def _plan_queries(topic: str, n: int) -> list[str]:
    llm = get_llm()
    if llm.stub_mode:
        base = topic.strip().rstrip("?.! ")
        variants = [
            base,
            f"{base} tutorial",
            f"{base} official documentation",
            f"{base} examples",
            f"{base} best practices",
        ]
        return variants[:n]

    resp = llm.chat(
        system=AGENT_PLANNER_SYSTEM,
        user=build_plan_queries_prompt(topic, n),
        temperature=0.5,
        max_tokens=300,
    )
    queries = _extract_queries(resp["text"], fallback_topic=topic, n=n)
    return queries[:n] if queries else [topic]


def _extract_queries(text: str, fallback_topic: str, n: int) -> list[str]:
    try:
        data = json.loads(text)
        q = data.get("queries") or []
        if isinstance(q, list) and all(isinstance(x, str) for x in q):
            return [x.strip() for x in q if x.strip()]
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            q = data.get("queries") or []
            if isinstance(q, list):
                return [str(x).strip() for x in q if str(x).strip()]
        except Exception:
            pass
    # Very last resort: just return the topic.
    return [fallback_topic]


def _judge_relevance(topic: str, title: str, snippet: str, excerpt: str) -> tuple[str, str]:
    llm = get_llm()
    if llm.stub_mode:
        if len(excerpt.strip()) >= 400:
            return "keep", "stub-mode: kept because page has substantive text"
        return "skip", "stub-mode: skipped thin page"

    resp = llm.chat(
        system=RELEVANCE_JUDGE_SYSTEM,
        user=build_judge_prompt(topic, title, snippet, excerpt),
        temperature=0.0,
        max_tokens=120,
    )
    return _parse_judge(resp["text"])


def _parse_judge(text: str) -> tuple[str, str]:
    def _norm(d: dict) -> tuple[str, str]:
        decision = str(d.get("decision", "skip")).strip().lower()
        if decision not in ("keep", "skip"):
            decision = "skip"
        reason = str(d.get("reason", "")).strip()[:200]
        return decision, reason

    try:
        return _norm(json.loads(text))
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return _norm(json.loads(m.group(0)))
        except Exception:
            pass
    # Conservative default.
    return "skip", "unparseable judge response"


def _existing_sources() -> set[str]:
    """URLs already present in the vector store, used to skip duplicate work."""
    return {d["source"].rstrip("/") for d in get_vector_store().list_documents()}


def research(cfg: ResearchConfig) -> Iterator[dict]:
    """Run one research pass and yield timestamped progress events."""
    t0 = time.time()

    if not cfg.topic or not cfg.topic.strip():
        yield _event("error", message="Topic is empty")
        return

    num_queries = max(1, min(cfg.num_queries, 5))
    per_query = max(1, min(cfg.per_query, 5))

    yield _event("start", topic=cfg.topic, num_queries=num_queries, per_query=per_query)

    # 1. Plan
    try:
        queries = _plan_queries(cfg.topic, num_queries)
    except Exception as e:
        yield _event("error", message=f"planning failed: {e}")
        return
    yield _event("plan", queries=queries)

    seen_urls = _existing_sources()
    kept_docs: list[dict] = []
    skipped = 0
    scraped = 0

    # 2. Search + 3. Scrape + Judge + Ingest
    for i, q in enumerate(queries):
        yield _event("search_start", iter=i, query=q)
        try:
            results = search_web(q, max_results=per_query * 2)
        except Exception as e:
            yield _event("error", message=f"search failed: {e}", query=q)
            continue
        yield _event(
            "search_results",
            query=q,
            urls=[{"url": r.url, "title": r.title, "snippet": r.snippet} for r in results],
        )

        picked = 0
        for r in results:
            if picked >= per_query:
                break
            key = r.url.rstrip("/")
            if key in seen_urls or is_blacklisted(r.url):
                yield _event("skip", url=r.url, reason="dedup-or-blacklist")
                continue
            seen_urls.add(key)

            yield _event("scrape_start", url=r.url, title=r.title)
            try:
                page = scrape_url(r.url)
            except Exception as e:
                yield _event("scrape_failed", url=r.url, reason=str(e))
                continue
            scraped += 1
            yield _event("scrape_done", url=r.url, chars=len(page.text), title=page.title)

            if len(page.text) < cfg.min_chars:
                skipped += 1
                yield _event("judge", url=r.url, decision="skip", reason="too thin")
                continue

            try:
                decision, reason = _judge_relevance(cfg.topic, page.title, r.snippet, page.text)
            except Exception as e:
                decision, reason = "skip", f"judge error: {e}"
            yield _event("judge", url=r.url, decision=decision, reason=reason)

            if decision != "keep":
                skipped += 1
                continue

            try:
                res = rag.ingest_text(page.title, page.text, source=page.url)
            except Exception as e:
                yield _event("ingest_failed", url=r.url, reason=str(e))
                continue
            kept_docs.append(
                {"title": res.title, "url": res.source, "chunks": res.chunks, "doc_id": res.doc_id}
            )
            picked += 1
            yield _event(
                "ingest", url=res.source, title=res.title, chunks=res.chunks, doc_id=res.doc_id
            )

    elapsed_ms = round((time.time() - t0) * 1000, 1)
    summary = {
        "topic": cfg.topic,
        "queries": queries,
        "scraped": scraped,
        "ingested": len(kept_docs),
        "skipped": skipped,
        "total_chunks": sum(d["chunks"] for d in kept_docs),
        "documents": kept_docs,
        "elapsed_ms": elapsed_ms,
    }
    get_metrics().record({"kind": "agent_research", **summary, "latency_ms": elapsed_ms})
    get_metrics().bump("agent_requests")
    yield _event("done", summary=summary)


def _event(kind: str, **data) -> dict:
    return {"type": kind, "ts": time.time(), **data}
