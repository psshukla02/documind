# Future Improvements

## Retrieval

- **Hybrid search.** Combine dense (embeddings) with sparse (BM25) for
  better recall on proper nouns and rare tokens. `rank_bm25` adds ~10
  lines of code and one dependency.
- **Query rewriting.** A cheap LLM rewrite step ("expand abbreviations,
  split compound questions") can improve top-k hit rate without
  changing the retriever.
- **Cross-encoder re-ranking.** After the FAISS top-20, re-rank with
  a cross-encoder (e.g. `bge-reranker-base`) before feeding top-k to
  the LLM. Expected gain: +5–10 points on retrieval precision.
- **Per-document deletion.** Currently `DELETE /knowledge-base` clears
  everything; add a `DELETE /knowledge-base/{doc_id}` route and
  corresponding UI action.
- **Chunk-level deletion** so failed ingests can be rolled back.

## Prompt Engineering

- **Few-shot from synthetic data.** Export high-quality synthetic Q&A
  pairs and inject the top 2–3 as few-shot examples in the chat system
  prompt. The infrastructure for this already exists — the Synthetic
  page has a Copy JSON button for the same reason.
- **Self-consistency.** For high-stakes queries, call the LLM 3× with
  temperature 0.7 and pick the answer with the highest citation
  coverage.
- **Structured output.** Migrate doc generation to OpenAI's
  response-format JSON mode so the UI can render richer, sectioned
  documentation with guaranteed schema.
- **Conversation memory.** Chat currently sends a single query. A
  small conversation-history window would let follow-ups work
  naturally.

## Research Agent

- **Multi-hop research.** Let the agent follow interesting links from
  an ingested page, bounded by a budget. Current agent is one-hop.
- **Iterative refinement.** After the first pass, ask the LLM which
  sub-topics are still weak and plan a second round of queries.
- **Quality filter on ingestion.** Reject documents whose average
  retrieval score on their own chunks is low (suggests incoherent
  content).
- **Source diversity.** Enforce a rule that at most two URLs per host
  are ingested per run, preventing one site from dominating.

## UX

- **Streaming chat responses.** Swap `/api/chat` for an SSE endpoint.
  The agent page already has the client-side plumbing for this.
- **Document explorer.** Click a citation in chat to jump to that
  chunk in the Knowledge Base viewer.
- **Saved sessions.** Persist conversation history in `localStorage`
  so refreshes do not lose context.
- **Mobile polish.** The layout stacks reasonably on mobile, but the
  sidebar should collapse into a hamburger on narrow screens.

## Evaluation

- **Golden-set harness.** Ship *N* synthetic Q&A pairs per ingested
  doc, measure retrieval hit@k and answer-contains-expected on every
  PR.
- **Track evaluation scores over time.** Extend the Metrics page with
  a time-series chart.
- **A/B on prompt variants.** Small `prompts/variants/*.py` directory
  + a `PROMPT_VARIANT` env var would let us compare.

## Productionization

- **Auth.** Currently open; add a simple API-key guard or OAuth
  proxy.
- **Persistent vector store.** Swap FAISS on-disk for Qdrant /
  pgvector for multi-process deployments.
- **Docker Compose.** Single `docker compose up` to run backend +
  frontend.
- **Observability.** Replace in-memory metrics with Prometheus +
  Grafana.
- **CI.** GitHub Actions workflow running pytest + `npm run build` on
  every push.
- **Rate limiting.** Per-IP token bucket on `/api/*` to prevent abuse
  if the app is ever exposed publicly.
