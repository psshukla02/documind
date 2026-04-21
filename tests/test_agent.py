"""Agent tests.

Network calls are mocked so these run offline. We patch:
- `app.services.agent.search_web` → returns a canned result list
- `app.services.agent.scrape_url`  → returns a canned ScrapedPage

Everything else (planning, judging, chunking, embedding, storage) runs
through the real code paths in stub mode.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.agent import ResearchConfig, research
from app.services.scraper import ScrapedPage
from app.services.search import SearchResult


FAKE_PAGE_TEXT = (
    "FastAPI is a modern, fast web framework for building APIs with Python based on standard type hints. "
    "It uses Pydantic for validation and Starlette for the web parts. " * 20
)


@dataclass
class FakeScrape:
    url: str = "https://fake.example.com/page"
    title: str = "Fake FastAPI docs"
    text: str = FAKE_PAGE_TEXT


def _fake_search(query, max_results=6):
    return [
        SearchResult(
            url=f"https://example.com/{i}-{query.replace(' ', '-')}",
            title=f"Result {i} for {query}",
            snippet=f"Snippet for {query} #{i}",
        )
        for i in range(max_results)
    ]


def _fake_scrape(url):
    return ScrapedPage(url=url, title=f"Title of {url}", text=FAKE_PAGE_TEXT)


@pytest.fixture
def patched_agent(monkeypatch, client):
    monkeypatch.setattr("app.services.agent.search_web", _fake_search)
    monkeypatch.setattr("app.services.agent.scrape_url", _fake_scrape)
    return client


def test_agent_research_sync_endpoint(patched_agent):
    r = patched_agent.post(
        "/api/agent/research",
        json={"topic": "FastAPI basics", "num_queries": 2, "per_query": 2},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    summary = data["summary"]
    assert summary["topic"] == "FastAPI basics"
    assert len(summary["queries"]) == 2
    assert summary["ingested"] >= 1
    assert summary["total_chunks"] >= 1

    kinds = [e["type"] for e in data["events"]]
    assert "start" in kinds
    assert "plan" in kinds
    assert "search_start" in kinds
    assert "search_results" in kinds
    assert "ingest" in kinds
    assert "done" in kinds


def test_agent_deduplicates_existing_sources(monkeypatch, client):
    # Narrow search — only 2 unique URLs exist, so the second run has nothing new.
    def tiny_search(query, max_results=6):
        return [
            SearchResult(url="https://example.com/a", title="A", snippet=""),
            SearchResult(url="https://example.com/b", title="B", snippet=""),
        ]

    monkeypatch.setattr("app.services.agent.search_web", tiny_search)
    monkeypatch.setattr("app.services.agent.scrape_url", _fake_scrape)

    r1 = client.post(
        "/api/agent/research",
        json={"topic": "FastAPI basics", "num_queries": 1, "per_query": 2},
    )
    assert r1.status_code == 200
    assert r1.json()["summary"]["ingested"] == 2

    r2 = client.post(
        "/api/agent/research",
        json={"topic": "FastAPI basics", "num_queries": 1, "per_query": 2},
    )
    assert r2.status_code == 200
    data = r2.json()
    skip_events = [e for e in data["events"] if e.get("type") == "skip"]
    assert len(skip_events) >= 2
    assert data["summary"]["ingested"] == 0


def test_agent_rejects_empty_topic(patched_agent):
    r = patched_agent.post(
        "/api/agent/research",
        json={"topic": "", "num_queries": 1, "per_query": 1},
    )
    assert r.status_code == 422


def test_agent_stream_sse(patched_agent):
    with patched_agent.stream(
        "GET",
        "/api/agent/stream",
        params={"topic": "Pydantic basics", "num_queries": 1, "per_query": 2},
    ) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        body = b"".join(r.iter_bytes())
    text = body.decode("utf-8")
    assert 'data: {"type": "start"' in text
    assert '"type": "done"' in text


def test_blacklist_and_scrape_failure(monkeypatch, client):
    # Mix of good, blacklisted, and failing URLs.
    def mixed_search(query, max_results=6):
        return [
            SearchResult(url="https://youtube.com/watch?v=1", title="video", snippet=""),
            SearchResult(url="https://example.com/good.html", title="good", snippet=""),
            SearchResult(url="https://example.com/broken.html", title="broken", snippet=""),
        ]

    def selective_scrape(url):
        if "broken" in url:
            raise ValueError("HTTP 404")
        return ScrapedPage(url=url, title="Good Page", text=FAKE_PAGE_TEXT)

    monkeypatch.setattr("app.services.agent.search_web", mixed_search)
    monkeypatch.setattr("app.services.agent.scrape_url", selective_scrape)

    r = client.post(
        "/api/agent/research",
        json={"topic": "anything", "num_queries": 1, "per_query": 3},
    )
    assert r.status_code == 200
    kinds = [e["type"] for e in r.json()["events"]]
    assert "skip" in kinds  # the youtube url
    assert "scrape_failed" in kinds  # the broken url
    assert "ingest" in kinds  # the good url


def test_search_url_unwrap_and_blacklist_helpers():
    from app.services.search import is_blacklisted

    assert is_blacklisted("https://youtube.com/watch?v=x") is True
    assert is_blacklisted("https://x.com/anything") is True
    assert is_blacklisted("https://example.com/doc.pdf") is True
    assert is_blacklisted("https://fastapi.tiangolo.com/") is False
