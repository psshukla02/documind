# Challenges & Solutions

## 1. Keeping retrieval "semantic enough" without a heavy framework

**Challenge.** Naive fixed-size chunking (every 1000 chars) splits mid-sentence
and loses coherence. Full semantic chunking via a sentence transformer is
overkill for a student project.

**Solution.** Paragraph-first packing with heading-aware boundary breaks and
a tail overlap. Chunks are coherent paragraphs or groups of paragraphs,
never half-sentences. The overlap guarantees boundary facts are retrievable.

## 2. Hallucination reduction

**Challenge.** Even with relevant context, LLMs will invent API names and
version numbers when the sources don't quite answer the question.

**Solution.** Three layers:
- **Priority-ordered constraints** in the system prompt.
- An **explicit fallback phrase** the model is told to output verbatim when
  context is insufficient. This makes hallucinations visible to a simple
  post-filter.
- **Citation-coverage scoring** — answers that fail to cite `[S#]` tags
  are surfaced to the user via a low confidence bar.

## 3. Stub-mode parity

**Challenge.** We wanted the app to be fully demoable without an API key,
but the frontend shouldn't have to know the backend is stubbed.

**Solution.** The stub path is hidden inside `LLMClient`. It returns the
same shape (`text`, `tokens`, `model`) as a real OpenAI response.
Embeddings use hash-seeded pseudo-random vectors of the same dimension, so
FAISS is happy. A single `stub_mode` flag surfaces in `/health` so the UI
can show a warning.

## 4. Forcing JSON out of a chat model

**Challenge.** `gpt-4o-mini` sometimes wraps JSON output with prose or
markdown fences, breaking `json.loads`.

**Solution.** A regex fallback extracts the first `{…}` block from the
response body if the direct parse fails. Worst case, we return an empty
pair list rather than a 500 — the UI shows an explanatory message.

## 5. CORS and dev ergonomics

**Challenge.** React (port 5173) and FastAPI (port 8000) run on different
origins. We wanted hot reload without manually re-CORS-ing every endpoint.

**Solution.** Vite's `server.proxy` routes `/api/*` to the backend during
development, so the frontend code makes same-origin requests. In production,
`CORS_ORIGINS` env var controls the allowlist.

## 6. FAISS dimension detection at startup

**Challenge.** We don't want to hardcode the embedding dimension — it
differs between stub mode (384), `text-embedding-3-small` (1536), and
`text-embedding-3-large` (3072).

**Solution.** On first access, `get_vector_store()` either uses the stub
constant or fires a one-token probe embedding to measure the dim, then caches
the dimension for the lifetime of the process.
