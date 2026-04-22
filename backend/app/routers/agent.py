"""Research-agent routes.

POST /api/agent/research
    Synchronous run. Returns a full event list + summary. Useful for CLI
    and for tests. May take 30–90 s depending on `num_queries * per_query`.

GET /api/agent/stream
    Server-Sent Events stream. The frontend uses EventSource to render
    progress live. Each event is:
        data: {"type": "...", "ts": 1714..., ...}\\n\\n
"""
from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.metrics import get_metrics
from app.schemas import ResearchRequest, ResearchResponse, ResearchSummary
from app.services.agent import ResearchConfig, research
from app.services.search import search_web

router = APIRouter(tags=["agent"])


@router.get("/agent/debug-search")
def debug_search(q: str = Query(..., min_length=1, max_length=200)) -> dict:
    """Diagnostic: probe every search backend and return per-backend status
    so you can tell what's failing in a deployed environment (blocked IP
    vs. parser drift vs. auth missing).
    """
    from app.core.config import get_settings
    from app.services.search import (
        DDG_BACKENDS, _fetch, tavily_search, search_web,
    )

    settings = get_settings()
    attempts: list[dict] = []

    # Tavily
    if settings.tavily_api_key:
        try:
            t_results = tavily_search(q, max_results=6)
            attempts.append({
                "provider": "tavily",
                "count": len(t_results),
                "urls": [r.url for r in t_results[:3]],
            })
        except Exception as e:
            attempts.append({"provider": "tavily", "error": str(e)})
    else:
        attempts.append({"provider": "tavily", "skipped": "TAVILY_API_KEY not set"})

    # DDG backends
    for url, variant, parser in DDG_BACKENDS:
        resp = _fetch(url, q, settings.request_timeout)
        if resp is None:
            attempts.append({"provider": f"ddg-{variant}", "error": "network_error"})
            continue
        body = resp.text or ""
        parsed = parser(body, 6)
        attempts.append({
            "provider": f"ddg-{variant}",
            "status": resp.status_code,
            "body_len": len(body),
            "body_head": body[:300].replace("\n", " ").strip(),
            "count": len(parsed),
            "urls": [r.url for r in parsed[:3]],
        })

    final = search_web(q, max_results=6)
    return {
        "query": q,
        "final_count": len(final),
        "final_results": [
            {"url": r.url, "title": r.title, "snippet": r.snippet[:200]}
            for r in final
        ],
        "attempts": attempts,
    }


@router.post("/agent/research", response_model=ResearchResponse)
def agent_research(req: ResearchRequest) -> ResearchResponse:
    cfg = ResearchConfig(
        topic=req.topic,
        num_queries=req.num_queries,
        per_query=req.per_query,
    )
    try:
        events = list(research(cfg))
    except Exception as e:
        get_metrics().bump("errors")
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}")

    summary_event = next(
        (e for e in reversed(events) if e.get("type") == "done"),
        None,
    )
    if not summary_event:
        raise HTTPException(status_code=500, detail="Agent did not complete")
    return ResearchResponse(summary=ResearchSummary(**summary_event["summary"]), events=events)


@router.get("/agent/stream")
def agent_stream(
    topic: str = Query(..., min_length=1, max_length=300),
    num_queries: int = Query(3, ge=1, le=5),
    per_query: int = Query(3, ge=1, le=5),
) -> StreamingResponse:
    cfg = ResearchConfig(topic=topic, num_queries=num_queries, per_query=per_query)

    def event_gen() -> Iterator[bytes]:
        try:
            for ev in research(cfg):
                yield f"data: {json.dumps(ev, default=str)}\n\n".encode("utf-8")
        except Exception as e:
            err = {"type": "error", "message": f"agent crashed: {e}"}
            yield f"data: {json.dumps(err)}\n\n".encode("utf-8")

    # Headers that disable buffering on common reverse proxies / browsers.
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_gen(), media_type="text/event-stream", headers=headers)
