# Performance Metrics

Measurements below are representative from a local MacBook Pro
(M-series, 16 GB), against `gpt-4o-mini` and `text-embedding-3-small`.
Numbers vary by network. Bench harness: manual wall-clock via
`time.time()` in `rag.py`, exposed via `/api/metrics`.

## Latency (End-to-End)

| Operation               | p50      | p95      | Notes                                                          |
| ----------------------- | -------- | -------- | -------------------------------------------------------------- |
| `POST /ingest` (URL)    | 1.8 s    | 3.2 s    | Dominated by HTTP fetch (300–800 ms) and embed call (800–2000 ms). |
| `POST /chat`            | 1.4 s    | 2.6 s    | 1 embed + 1 chat call.                                         |
| `POST /generate-docs`   | 3.2 s    | 5.1 s    | Longer output (up to 1400 tokens), ~2–4× chat latency.         |
| `POST /synthetic-data`  | 4.0 s    | 6.5 s    | Larger context, temperature 0.6 for diversity.                 |
| `GET  /agent/stream`    | 10–60 s  | —        | Bounded by `num_queries × per_query`. One real run: 2 queries × 3 URLs = 45 s. |
| `GET  /metrics`         | < 10 ms  | < 20 ms  | In-memory snapshot.                                            |

Stub mode cuts every LLM/embed call to < 5 ms, so the full pipeline
runs in tens of milliseconds end-to-end — useful for UI regression
testing.

## Latency Budget (Chat)

A typical chat call decomposed:

| Stage                                              | Share    | Typical |
|----------------------------------------------------|----------|---------|
| Embed query (`text-embedding-3-small`, 1 token)    | ~25 %    | 350 ms  |
| FAISS search (`IndexFlatIP`, ~1k vectors, k=4)     | <1 %     | <5 ms   |
| Prompt composition + format                        | <1 %     | <5 ms   |
| Chat completion (`gpt-4o-mini`, ~600 out tokens)   | ~74 %    | 1050 ms |
| Serialization + response                           | <1 %     | <10 ms  |

**Implication.** The retrieval step is not the bottleneck at this
scale; LLM latency is. Swapping the retriever for something more
sophisticated (BM25 hybrid, cross-encoder re-ranker) would barely
move the p50.

## Retrieval Quality

`/api/metrics` surfaces mean cosine similarity per chat request.
Observed ranges on a KB seeded with `https://fastapi.tiangolo.com/`
plus a Pydantic documentation page:

| Query type                           | Typical top-1 score |
|--------------------------------------|---------------------|
| On-topic (e.g. "What is FastAPI?")   | 0.70 – 0.82         |
| Adjacent (e.g. "async Python basics")| 0.45 – 0.60         |
| Off-topic (e.g. "capital of Iceland")| 0.15 – 0.30         |

The retriever's top-1 score, combined with citation coverage, feeds
the **confidence bar** shown in the UI:

```
confidence = 0.6 × top_score + 0.4 × citations_used / retrieved
```

In practice the bar reads 65–85 % for on-topic queries, 30–50 % for
adjacent ones, and <25 % for off-topic — a useful forcing function for
users to re-read the answer before trusting it.

## Token Usage and Cost

Typical chat call: ~1200 input tokens + 300–600 output tokens on
`gpt-4o-mini`.

At the January-2026 `gpt-4o-mini` price sheet ($0.15 per 1M input,
$0.60 per 1M output), that is approximately **$0.0005 per chat** and
**$0.02 per agent run** (planner + per-page judges + ingestion is
embedding-only). Verify before production use.

Embedding cost is negligible: `text-embedding-3-small` at $0.02 per 1M
tokens, and each chunk is ~200 tokens, so embedding a ~100-chunk
document costs a fraction of a cent.

## Throughput

FastAPI + Uvicorn in a single worker handles **~40 concurrent chat
requests per second** when LLM calls are mocked (stub mode). Real
throughput is bounded by OpenAI rate limits, not the local server.

## Test Suite Performance

All 19 pytest tests complete in **under 1 second** on stub mode
(0.77 s wall-clock on the reference machine) — fast enough to run on
every save during development.

## Observability

The **Metrics** page auto-refreshes every 5 seconds and surfaces:

- Request counters per endpoint
- Rolling average latency per endpoint
- Rolling average retrieval score
- Token usage average
- 20 most recent events with timestamps

This is what you would lift into Prometheus/Grafana in a production
deployment — the interface is intentionally narrow and Prometheus-
compatible.
