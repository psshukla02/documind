# Implementation Details

## 1. RAG Pipeline

### 1.1 Ingestion

`app/services/scraper.py` fetches a URL with a browser-like User-Agent, parses
with BeautifulSoup (lxml), and strips `script`, `style`, `nav`, `footer`,
`aside`, `form`, `iframe`, `noscript`, `svg`. The remaining `<main>` /
`<article>` / `<body>` text is flattened and normalized (collapsing repeated
whitespace and blank lines).

### 1.2 Chunking

`app/services/chunker.py` splits on blank lines into paragraphs, then packs
paragraphs into windows of ~`chunk_size` characters. Three design choices:

1. **Heading-aware breaks** — a paragraph matching a heading pattern
   (`# …`, `1. …`, or `Title Case:`) forces a chunk boundary if the current
   buffer is already > 50% full. This keeps semantic units together.
2. **Hard-split for oversized paragraphs** — paragraphs longer than
   `chunk_size` are sliced into overlapping windows directly.
3. **Tail overlap** — each chunk gets the last `chunk_overlap` characters of
   the previous chunk prepended, so retrieval doesn't miss boundary-spanning
   facts.

Defaults: `chunk_size=800`, `chunk_overlap=120`.

### 1.3 Embedding

Via OpenAI's `text-embedding-3-small` (1536 dims). In stub mode, we fall back
to a deterministic SHA-256-seeded pseudo-random vector (384 dims) — useless
for semantics but keeps all code paths exercised.

### 1.4 Vector Store

`faiss.IndexFlatIP` over L2-normalized vectors (so inner product = cosine
similarity). Metadata (chunk text, source URL, title, ordinal) is stored in a
parallel `meta.json` keyed by FAISS row index. Both files live under
`data/vector_store/` and are loaded on startup.

### 1.5 Retrieval

We embed the query, normalize, and call `index.search(q, k)`. Scores are
returned per-chunk alongside the metadata record.

---

## 2. Prompt Engineering Strategy

`app/prompts/templates.py` is the single source of truth. Three patterns:

### 2.1 Role separation

System messages carry **identity + hard constraints**. User messages carry
**task + data + output contract**. The split matters because providers
weight system and user roles differently, and it keeps instructions visible
across turns.

### 2.2 Instruction hierarchy

Every system prompt lists constraints in **priority order**:

> 1. Ground every factual claim in the provided sources.
> 2. If sources are insufficient, say so explicitly.
> 3. …

When constraints conflict (e.g. "be helpful" vs "don't hallucinate"), the
model has an explicit tiebreaker.

### 2.3 Edge-case handling inline

Instead of separate "fallback" prompts, the main prompt tells the model what
to do when the input is degenerate:

> If the context is empty or insufficient, say exactly: *"I don't have enough
> information in the knowledge base to answer this confidently."* and suggest
> what to ingest.

This reduces hallucination without a separate guardrail model.

### 2.4 Output contracts

- **Chat**: Markdown with inline `[S#]` citations + Sources section.
- **Doc gen**: strict section order (Overview, Quick Start, Usage, Parameters,
  Edge Cases, Related).
- **Synthetic**: strict JSON with a schema; the prompt explicitly says
  "Return ONLY the JSON object." A fallback regex parser handles stray prose.

---

## 3. Synthetic Data Generation

`rag.generate_synthetic()` bundles chunks from a target document (capped at
6000 characters to keep costs bounded), injects them into
`SYNTHETIC_SYSTEM` + `build_synthetic_user_prompt()`, and parses the JSON
response. The prompt enforces diversity by requiring categories: at least
one factual, one reasoning, one edge-case.

Uses for the generated pairs:

1. **Inline examples** in the UI (Synthetic Data page).
2. **Prompt improvement** — pairs can be exported (Copy JSON button) and
   re-used as few-shot examples in future versions of the chat prompt.
3. **Evaluation** — the Q&A pairs are a ready-made test set for regression
   testing the retriever (do the answers still surface the right chunks?).

---

## 4. Confidence Scoring

Confidence is a cheap proxy, not a calibrated probability:

```
confidence = 0.6 * top_retrieval_score + 0.4 * citation_coverage
citation_coverage = cited_sources / total_retrieved_sources
```

- Low top score → retriever didn't find relevant material.
- Low citation coverage → model didn't ground in what it got, suggesting
  hallucination risk.

The UI renders this as a colored bar (red/amber/green thresholds at 40/70).

---

## 5. Metrics

`app/core/metrics.py` is a thread-safe in-memory store with a rolling 200-event
window and a set of integer counters. Each chat/ingest/docs/synthetic call
records `{kind, latency_ms, …}`. `/api/metrics` returns:

- Counters (`chat_requests`, `ingest_requests`, `errors`, …).
- Rolling averages (latency, retrieval score, tokens, chunks/doc).
- Recent 20 events for the live feed.

Swap for Redis/Prometheus in production — the interface is already narrow.

---

## 6. Frontend

React 18 + Vite for fast HMR. Tailwind for design consistency. Five pages:

- **Chat** — message list, confidence bar, citation pills, copy buttons.
- **Knowledge Base** — URL / text ingestion, document table, clear-all.
- **Doc Generator** — topic + code input, rendered Markdown output.
- **Synthetic** — document picker, category-colored pair cards, Copy JSON.
- **Metrics** — stat cards + rolling event table, auto-refresh every 5 s.

A small `api/client.js` centralizes fetch + error handling.

---

## 7. Error Handling

- **Empty input** — validated by Pydantic at the route layer (returns 400).
- **No relevant docs** — model is instructed to say so; confidence drops.
- **OpenAI failures** — `tenacity` retries with exponential backoff (3 tries).
- **Missing API key** — stub mode kicks in transparently; sidebar shows a
  warning.
- **Scrape failures** — 400 with the HTTP error message.
- **Frontend** — every page shows loading, error, and empty states.
