"""In-memory metrics store.

Tracks retrieval latency, LLM latency, token usage, and retrieval scores.
Thread-safe for the single-process dev server. For multi-process deployments,
swap this for Redis or Prometheus.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from statistics import mean
from typing import Any


class MetricsStore:
    def __init__(self, window: int = 200):
        self._lock = threading.Lock()
        self._events: deque[dict[str, Any]] = deque(maxlen=window)
        self._counters: dict[str, int] = {
            "chat_requests": 0,
            "ingest_requests": 0,
            "generate_docs_requests": 0,
            "synthetic_requests": 0,
            "errors": 0,
        }
        self._started = time.time()

    def record(self, event: dict[str, Any]) -> None:
        event = {**event, "ts": time.time()}
        with self._lock:
            self._events.append(event)

    def bump(self, key: str, n: int = 1) -> None:
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + n

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            events = list(self._events)
            counters = dict(self._counters)

        chat_events = [e for e in events if e.get("kind") == "chat"]
        ingest_events = [e for e in events if e.get("kind") == "ingest"]

        def _avg(xs: list[float]) -> float:
            return round(mean(xs), 3) if xs else 0.0

        return {
            "uptime_seconds": round(time.time() - self._started, 1),
            "counters": counters,
            "chat": {
                "count": len(chat_events),
                "avg_latency_ms": _avg([e["latency_ms"] for e in chat_events if "latency_ms" in e]),
                "avg_retrieval_score": _avg(
                    [e["retrieval_score"] for e in chat_events if "retrieval_score" in e]
                ),
                "avg_tokens": _avg(
                    [e["tokens"] for e in chat_events if e.get("tokens") is not None]
                ),
            },
            "ingest": {
                "count": len(ingest_events),
                "avg_chunks": _avg([e["chunks"] for e in ingest_events if "chunks" in e]),
            },
            "recent_events": events[-20:],
        }


_store: MetricsStore | None = None


def get_metrics() -> MetricsStore:
    global _store
    if _store is None:
        _store = MetricsStore()
    return _store
