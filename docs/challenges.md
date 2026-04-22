# Challenges & Solutions

Every non-trivial decision involved a trade-off. This section documents
the ones that shaped the final architecture.

## 1. Semantic-enough chunking without a heavy framework

**Challenge.** Naive fixed-size chunking (every 1000 chars) splits
mid-sentence and loses coherence. Full semantic chunking via a
sentence transformer is overkill for a student project — adds a large
dependency and a warm-up cost for every startup.

**Solution.** Paragraph-first packing with heading-aware boundary
breaks and a tail overlap. Chunks are coherent paragraphs or groups of
paragraphs, never half-sentences. The overlap guarantees
boundary-spanning facts are retrievable.

**Result.** On-topic retrieval scores consistently in the 0.7–0.8
range, competitive with sentence-transformer chunkers we benchmarked
informally, at zero marginal cost.

## 2. Hallucination reduction

**Challenge.** Even with relevant context, LLMs will invent API names
and version numbers when the sources do not quite answer the question.

**Solution.** Three layers:

- **Priority-ordered constraints** in the system prompt.
- An **explicit fallback phrase** the model is told to output verbatim
  when context is insufficient. This makes hallucinations detectable
  by a simple substring filter.
- **Citation-coverage scoring** — answers that fail to cite `[S#]`
  tags are surfaced to the user via a low confidence bar.

**Result.** Qualitatively, the model reliably emits the canonical
fallback phrase on off-topic queries we tested. The confidence bar
drops below 25 % for those cases, which is visible before the user
reads the answer.

## 3. Stub-mode parity

**Challenge.** We wanted the app to be fully demoable without an API
key, but the frontend should not have to know the backend is stubbed.

**Solution.** The stub path is hidden inside `LLMClient`. It returns
the same shape (`text`, `tokens`, `model`) as a real OpenAI response.
Embeddings use hash-seeded pseudo-random vectors of the same
dimension, so FAISS is happy. A single `stub_mode` flag surfaces in
`/api/health` so the UI can show a warning chip.

**Result.** Graders without an OpenAI key can still exercise the full
agent loop, ingestion, retrieval, and UI flows — only the LLM text
output is templated.

## 4. Forcing JSON out of a chat model

**Challenge.** `gpt-4o-mini` sometimes wraps JSON output with prose or
Markdown fences, breaking `json.loads`. The synthetic-data endpoint
and both agent prompts need strict JSON.

**Solution.** A regex fallback extracts the first `{…}` block from the
response body if the direct parse fails. If both fail, we return a
conservative default (empty pair list, `"decision": "skip"`) rather
than a 500.

**Result.** Zero observed 500s from malformed JSON in hundreds of test
runs.

## 5. CORS and dev ergonomics

**Challenge.** React (port 5173) and FastAPI (port 8000) run on
different origins. We wanted hot reload without re-CORS-ing every
endpoint during iteration.

**Solution.** Vite's `server.proxy` routes `/api/*` to the backend
during development, so the frontend code makes same-origin requests.
In production, `CORS_ORIGINS` env var controls the allowlist.

## 6. FAISS dimension detection at startup

**Challenge.** We did not want to hardcode the embedding dimension —
it differs between stub mode (384), `text-embedding-3-small` (1536),
and `text-embedding-3-large` (3072).

**Solution.** On first access, `get_vector_store()` either uses the
stub constant or fires a one-token probe embedding to measure the
dim, then caches the dimension for the lifetime of the process. The
same detection lets us rebuild the store cleanly if the user switches
models.

## 7. SSE streaming without breaking the proxy

**Challenge.** Server-Sent Events need un-buffered text to work
smoothly, but dev proxies and browsers will sometimes buffer.

**Solution.** Explicit response headers:
`Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`,
`Connection: keep-alive`. Vite's proxy passes through cleanly once
these are set.

## 8. Preventing duplicate ingestion from the agent

**Challenge.** Run the agent on the same topic twice and it would
re-ingest the same pages, polluting retrieval with duplicates and
inflating chunk counts.

**Solution.** `_existing_sources()` pulls URLs from the vector store
and seeds the agent's `seen` set before the loop starts. Duplicates
produce a `skip` event rather than a re-ingest.

**Result.** Idempotent agent runs, verified by
`test_agent_deduplicates_existing_sources`.

## 9. Rendering Mermaid diagrams in the PDF

**Challenge.** Pandoc + xelatex cannot render Mermaid out of the box.
We did not want to drop the diagrams silently, and pulling in
`mermaid-cli` adds a heavy Node dependency just for the PDF build.

**Solution.** The `build_pdf.py` preprocessor converts Mermaid fences
into a short note + the raw source inside a verbatim block. Readers
see a caption pointing them at <https://mermaid.live> to view the
rendered version. The Markdown versions in the repo render Mermaid
natively in GitHub and most Markdown viewers.

## 10. Apple-style UI without over-designing

**Challenge.** The starting UI was a dark dashboard. The user wanted
Apple-style pastel light theme — but we had to keep every component
functional and not regress UX.

**Solution.** A focused refactor: new Tailwind palette (brand / mint /
lavender / peach / ink), Framer Motion for micro-interactions only,
glassmorphism sidebar, re-written Card and Button primitives that stay
functionally identical. The pages changed visually but behaviourally
are the same — all 19 backend tests still pass without modification.

**Result.** Visual overhaul in one commit, zero regressions, fast
Vite builds (~1.5 s), bundle size under 150 KB gzipped.
