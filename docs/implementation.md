# Implementation Details

This section breaks down each of the three rubric-aligned components —
RAG, Prompt Engineering, Synthetic Data — along with the confidence
scoring, observability, and fault-tolerance infrastructure that glues
them together into a production-quality application.

## 1. RAG Pipeline

### 1.1 Ingestion

`app/services/scraper.py` fetches a URL with a browser-like User-Agent
(`Mozilla/5.0 (compatible; AI-Doc-Assistant/1.0)`) and a 30-second
timeout, then parses with BeautifulSoup (lxml parser). It strips the
following elements from the tree before extracting text:

```
script, style, noscript, iframe, svg, nav, footer, aside, form
```

The remaining `<main>` / `<article>` / `<body>` text is flattened and
whitespace-normalized (collapsing runs of blank lines and multi-space
runs). Pages with fewer than 40 characters of extracted content are
rejected with a `ValueError("No meaningful content extracted")` —
catches 404s served as 200s, login walls, and heavy SPA pages that
return a shell HTML.

### 1.2 Chunking

`app/services/chunker.py` implements what we call "semantic-ish"
chunking: heading- and paragraph-aware without a sentence transformer
in the hot path.

1. Split on blank-line runs into paragraphs.
2. Pack paragraphs into windows of approximately `chunk_size`
   characters (default 800).
3. **Heading-aware break**: a paragraph matching `r"^(#{1,6}\s|\d+\.\s|[A-Z][A-Za-z0-9 ]{0,60}:\s*$)"`
   forces a chunk boundary if the current buffer is already at least
   half full. Keeps semantic units (sections) together.
4. **Oversized paragraph handling**: paragraphs longer than
   `chunk_size` are sliced into overlapping windows directly.
5. **Tail overlap**: each chunk gets the last `chunk_overlap`
   characters (default 120) of the previous chunk prepended, so
   retrieval does not miss boundary-spanning facts.

Defaults chosen empirically to balance retrieval granularity against
embedding cost.

### 1.3 Embedding

OpenAI's `text-embedding-3-small` (1536 dimensions). In stub mode we
fall back to a deterministic SHA-256-seeded pseudo-random vector (384
dimensions) — useless for semantics but keeps every downstream code
path exercised so graders without an API key see the full application
work end-to-end.

### 1.4 Vector Store

`faiss.IndexFlatIP` over **L2-normalized** vectors, which makes inner
product equal to cosine similarity. Metadata (chunk text, source URL,
title, ordinal) lives in a parallel `meta.json` keyed by FAISS row
index. Both files persist under `data/vector_store/` and auto-load at
startup.

Design choice: `IndexFlatIP` (exact search) instead of an approximate
index (HNSW / IVF). At the scale of a student project (a few thousand
chunks) the latency difference is negligible and the exact guarantee
simplifies evaluation.

### 1.5 Retrieval

1. Embed the query with the same model used for chunks.
2. L2-normalize.
3. `index.search(q, k)` returns top-k cosine similarities and row
   indices.
4. Look up metadata for each hit.
5. Surface scores back through the API so the UI can colour-grade the
   confidence bar.

### 1.6 Prompt Injection

The top-k chunks are labelled `[S1]`, `[S2]`, … and inlined into the
user-side prompt. The chat system prompt requires the model to cite
those labels; the frontend rewrites matched labels into interactive
pills that link to the source URL.

## 2. Prompt Engineering

`app/prompts/templates.py` is the single source of truth. Three design
patterns are used consistently across all four system prompts.

### 2.1 Role Separation

System messages carry **identity + hard constraints**. User messages
carry **task + data + output contract**. The split is not cosmetic —
OpenAI's chat endpoint weights system and user roles differently, and
the split keeps invariant rules visible across multi-turn
conversations (future work).

### 2.2 Instruction Hierarchy

Every system prompt lists its constraints in **priority order**:

> Hard constraints (in priority order):
> 1. Ground every factual claim in the provided sources.
> 2. If the sources do not contain enough information to answer, say so explicitly. Do NOT invent APIs, flags, function names, or version numbers.
> 3. …

When constraints could conflict — "be helpful" vs. "don't hallucinate" —
the model has an explicit tiebreaker. This dramatically reduces the
"but the user asked for code" failure mode we observed during
development.

### 2.3 Output Contracts

Each prompt specifies the exact shape of the expected response, which
drastically reduces parsing failures:

- **Chat**: Markdown with inline `[S#]` citations + a Sources section.
- **Doc gen**: strict section order — Overview, Quick Start, Usage,
  Parameters, Edge Cases, Related — every section with an `H2`
  heading.
- **Synthetic**: strict JSON schema with a top-level `"pairs": [...]`
  array. The prompt explicitly says "Return ONLY the JSON object."
- **Agent planner**: strict JSON `{"queries": [...]}`, ≤12-word queries.
- **Relevance judge**: strict JSON `{"decision": "keep"|"skip", "reason": "..."}`.

### 2.4 Edge-Case Handling Inline

Instead of wiring up a separate "fallback" prompt, the main prompt
tells the model what to do when the input is degenerate:

> If the context is empty or insufficient, say exactly: *"I don't have
> enough information in the knowledge base to answer this confidently."*
> and suggest what to ingest.

This reduces hallucination without a separate guardrail model; we can
then filter by substring in post-processing if needed.

### 2.5 Prompt Taxonomy

| Prompt                    | System role                    | User data               | Output contract            |
|---------------------------|--------------------------------|-------------------------|----------------------------|
| `CHAT_SYSTEM`             | Senior technical doc assistant | query + ranked chunks   | Markdown + `[S#]` + sources|
| `DOC_GEN_SYSTEM`          | Senior technical writer        | topic + optional code   | 6-section Markdown         |
| `SYNTHETIC_SYSTEM`        | Synthetic data generator       | full-doc source         | strict JSON pairs          |
| `AGENT_PLANNER_SYSTEM`    | Research query planner         | topic + N               | strict JSON queries        |
| `RELEVANCE_JUDGE_SYSTEM`  | Relevance judge                | topic + page excerpt    | strict JSON decision       |

## 3. Synthetic Data Generation

`rag.generate_synthetic()` bundles chunks from a target document
(capped at 6000 characters to keep costs bounded), injects them into
`SYNTHETIC_SYSTEM` plus `build_synthetic_user_prompt()`, and parses
the JSON response.

The prompt enforces diversity by requiring **categorical coverage**:

> Diversity Requirements:
> - At least one factual lookup question.
> - At least one "why/how" reasoning question.
> - At least one edge-case or pitfall question.
> - Vary question length and phrasing.

Categories: `factual | reasoning | edge_case | example`.
Difficulty: `easy | medium | hard`.

### Uses for the generated pairs

1. **Inline examples** in the UI (Synthetic Data page) with
   colour-coded category pills.
2. **Prompt improvement** — pairs can be exported via "Copy JSON" and
   re-used as few-shot examples in future versions of the chat prompt.
3. **Evaluation** — the Q&A pairs are a ready-made regression test set
   for the retriever (do the answers still surface the right chunks?).

### Defensive JSON parsing

The ideal case: `json.loads(response_text)`. Reality: LLMs sometimes
wrap JSON in prose or fenced blocks. We handle three layers:

1. Try `json.loads` on the raw text.
2. On failure, extract the first `{...}` block via regex `r"\{.*\}"`
   with `re.DOTALL` and retry.
3. If both fail, return an empty list and log the first 200 characters
   of the raw response. The UI displays "The model returned no usable
   pairs" rather than a 500.

## 4. Confidence Scoring

Confidence is a cheap proxy, not a calibrated probability:

```
confidence = 0.6 × top_retrieval_score + 0.4 × citation_coverage
citation_coverage = cited_sources / total_retrieved_sources
```

- **Low top score** → retriever did not find relevant material.
- **Low citation coverage** → model did not ground in what it got,
  suggesting hallucination risk.

The UI renders this as a colour-graded bar: mint ≥70%, peach 40–70%,
rose <40%.

## 5. Observability

`app/core/metrics.py` is a thread-safe in-memory store with a rolling
200-event window plus integer counters. Every chat / ingest / docs /
synthetic / agent call records `{kind, latency_ms, retrieval_score,
tokens, ...}`.

`GET /api/metrics` returns:

- Counters (`chat_requests`, `ingest_requests`, `errors`, `agent_requests`, …).
- Rolling averages (latency, retrieval score, tokens, chunks/doc).
- Recent 20 events for the live feed.

Swap for Redis or Prometheus in production — the interface is already
narrow (two methods: `record`, `bump`).

## 6. Frontend

React 18 + Vite for fast HMR. Tailwind CSS for design consistency.
Framer Motion for subtle micro-interactions (page transitions, button
hover scale, bubble fade-ins, staged event rows).

Seven pages:

- **Home** — pastel hero, feature grid, CTA.
- **Chat** — rounded bubble conversation with confidence bar, citation
  pills, copy buttons, typing indicator, sticky glass input bar.
- **Research Agent** — topic input, live SSE event timeline, summary
  stat cards.
- **Knowledge Base** — URL / text ingestion, document table,
  clear-all.
- **Doc Generator** — topic + code input, rendered Markdown output.
- **Synthetic Data** — document picker, category-colored pair cards,
  Copy JSON.
- **Metrics** — stat cards + rolling event table, 5-second
  auto-refresh.

A thin `api/client.js` centralizes `fetch` with error handling.

## 7. Error Handling

- **Empty input** — validated by Pydantic at the route layer (returns
  422 with field-level detail).
- **No relevant docs** — model is instructed to output the canonical
  "I don't have enough information" string; confidence drops.
- **OpenAI failures** — `tenacity` retries with exponential backoff
  (3 tries, 1–8 s jitter).
- **Missing API key** — stub mode kicks in transparently; sidebar
  shows a warning chip.
- **Scrape failures** — 400 with the upstream HTTP error message.
- **SSE dropped** — the frontend's `EventSource.onerror` surfaces the
  error to the user and closes the stream cleanly.
- **Frontend** — every page shows loading, error, and empty states.

## 8. Testing

19 tests in 5 modules (`tests/`):

- `test_health.py` — root + health endpoints
- `test_chunker.py` — paragraph merging, heading-aware breaks,
  oversized paragraph handling
- `test_ingest_and_chat.py` — text ingestion, chat with retrieval,
  empty-query rejection, KB reset
- `test_synthetic_and_docs.py` — doc generation, synthetic data,
  metrics counters
- `test_agent.py` — mocked DDG + scraper, full research loop,
  de-duplication, blacklist, SSE streaming, scrape-failure handling

All tests run in stub mode against a temp vector store so a
developer's real index is never touched.
