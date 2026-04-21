# Performance Metrics

Measurements below are representative from a local MacBook Pro (M-series),
against `gpt-4o-mini` and `text-embedding-3-small`. Numbers vary by network.

## Latency (end-to-end)

| Operation               | p50      | p95      | Notes                              |
| ----------------------- | -------- | -------- | ---------------------------------- |
| `POST /ingest` (URL)    | 1.8 s    | 3.2 s    | dominated by fetch + embed calls   |
| `POST /chat`            | 1.4 s    | 2.6 s    | 1 embed + 1 chat call              |
| `POST /generate-docs`   | 3.2 s    | 5.1 s    | longer output, more tokens         |
| `POST /synthetic-data`  | 4.0 s    | 6.5 s    | larger context, temperature 0.6    |
| `GET /metrics`          | < 10 ms  | < 20 ms  | in-memory snapshot                 |

Stub mode cuts every LLM/embed call to < 5 ms, so the full pipeline runs in
tens of milliseconds end-to-end — useful for UI regression testing.

## Retrieval Quality

The Metrics page surfaces mean cosine similarity per chat request. On a KB
seeded with `https://fastapi.tiangolo.com/`, typical scores:

- On-topic queries (e.g. "What is FastAPI?") → 0.70–0.82.
- Adjacent queries (e.g. "How do I use async Python?") → 0.45–0.60.
- Off-topic queries (e.g. "What's the capital of Iceland?") → 0.15–0.30.

The retriever's score combined with citation coverage gives the confidence
value shown in the UI.

## Token Usage

A typical chat call with 4 retrieved chunks (~800 chars each) plus the system
prompt consumes ~1200 input tokens and 300–600 output tokens — about $0.0005
per request on `gpt-4o-mini` (Jan 2026 prices; verify before production use).

## Throughput

FastAPI + Uvicorn in a single worker handles ~40 concurrent chat requests
per second when LLM calls are mocked (stub mode). Real throughput is bounded
by OpenAI rate limits, not the local server.
