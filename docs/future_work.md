# Future Improvements

## Retrieval

- **Hybrid search.** Combine dense (embeddings) with sparse (BM25) for
  better recall on proper nouns and rare tokens.
- **Query rewriting.** A cheap rewrite step ("expand abbreviations, split
  compound questions") improves top-k hit rate without changing the
  retriever.
- **Re-ranking.** Add a cross-encoder re-ranker (e.g. `bge-reranker-base`)
  on the top-20 FAISS results before feeding top-k to the LLM.
- **Per-document deletion.** Currently `DELETE /knowledge-base` clears
  everything; add a `DELETE /knowledge-base/{doc_id}` route.

## Prompt Engineering

- **Few-shot from synthetic data.** Export high-quality synthetic Q&A pairs
  and inject the top 2–3 as few-shot examples into the chat system prompt.
- **Self-consistency.** For high-stakes queries, call the LLM 3× with
  temperature 0.7 and pick the answer with the highest citation coverage.
- **Structured output.** Migrate doc generation to OpenAI's response-format
  JSON mode so the UI can render richer, sectioned documentation.

## UX

- **Streaming responses.** Swap `/api/chat` for an SSE endpoint; the UI
  already has a code shape that supports incremental rendering.
- **Document explorer.** Click a citation in chat to jump to that chunk in
  the Knowledge Base viewer.
- **Saved sessions.** Persist conversation history in `localStorage` so
  refreshes don't lose context.

## Evaluation

- Ship a proper **golden-set evaluation harness**: N synthetic Q&A pairs
  per ingested doc, measure retrieval hit@k and answer-contains-expected.
- Track **evaluation scores over time** in the metrics page.

## Productionization

- **Auth.** Currently open; add a simple API-key guard or OAuth proxy.
- **Persistent vector store.** Swap FAISS on-disk for Qdrant / pgvector for
  multi-process deployments.
- **Docker Compose.** Single `docker compose up` to run backend + frontend.
- **Observability.** Replace in-memory metrics with Prometheus + Grafana.
