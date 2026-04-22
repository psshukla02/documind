# Ethical Considerations

## Bias

- **Source bias.** The assistant is only as representative as the
  documents ingested. If a team only ingests blog posts from one
  vendor, answers will reflect that vendor's opinions. We surface the
  source URL on every citation so the user can audit the provenance.
- **Model bias.** `gpt-4o-mini` inherits whatever biases exist in
  OpenAI's training data. Our system prompts minimize free-form
  opinions — *"Hard constraint: ground every factual claim in the
  provided sources"* — but cannot eliminate them.
- **Retrieval bias.** Top-k retrieval will over-represent pages with
  dense, keyword-matching prose. Blog posts with lots of signposting
  can beat better-but-sparser reference docs. Mitigation: the UI
  shows *all* retrieved source titles and scores, so the user sees
  the full set, not just what was quoted.

## Hallucination

- We never rely on the model to be honest by default. The prompt
  contract requires inline citations; the UI highlights missing
  citations via the confidence bar; the retrieval-score display makes
  it obvious when the model is answering from thin context.
- Even so, the system **can** still produce plausible-sounding wrong
  answers. Users must treat every output as a draft to be verified,
  not ground truth. The README and chat empty-state frame the tool
  that way explicitly.

## Data Privacy

- Ingested content is stored locally in `data/vector_store/`. Nothing
  is exfiltrated except the prompts sent to OpenAI at query time.
- **Do not ingest proprietary or PII-containing documents without
  understanding OpenAI's data-retention policy** (API traffic is
  retained for abuse monitoring for 30 days by default; zero-retention
  agreements are available on enterprise plans).
- The scraper uses a bot-identifying User-Agent and a 30-second
  timeout. It does not attempt to bypass paywalls or authentication.
  It does not crawl recursively — one URL per ingest, or one topic
  per agent run.

## Misuse

Risks and mitigations:

| Risk                                          | Mitigation                                                                 |
| --------------------------------------------- | -------------------------------------------------------------------------- |
| Generating fake docs to impersonate a library | Citations and confidence scoring make unverified outputs obvious.          |
| Mass scraping of third-party sites            | No built-in crawler — single-URL ingestion only, agent is one-hop.         |
| Prompt injection via scraped content          | System prompt runs first; user-visible citations expose injected content.  |
| Leaking API keys in logs                      | Logger formats never include env vars; `.env` is gitignored.               |
| Knowledge-base pollution from bad sources     | Relevance judge + blacklist + dedup + admin "Clear All" button.            |

## Intellectual Property

- Ingested text is stored verbatim in the vector store's metadata.
  The UI surfaces the source URL next to every quote, so
  attribution is preserved end-to-end.
- Generated outputs will paraphrase ingested text. This is a
  derivative use that under fair-use doctrine is generally acceptable
  for research, education, and internal engineering, but it is **not**
  automatically cleared for redistribution. Users should check the
  license of the original source before publishing generated docs.

## Responsible Use Checklist

- ✅ Do ingest public documentation, your team's internal wikis, or
  source code you own.
- ✅ Do treat generated docs as drafts requiring human review.
- ✅ Do clear the knowledge base when switching projects — stale
  context leaks across domains.
- ❌ Don't ingest medical, legal, or financial documents and rely on
  the output without a qualified professional.
- ❌ Don't strip citations before sharing generated content — they're
  the user's audit trail.
- ❌ Don't point the agent at sites whose terms of service prohibit
  automated access.

## Environmental Considerations

LLM inference has a non-trivial energy cost. Mitigations baked in:

- `gpt-4o-mini` (smaller model) as default, not `gpt-4o`.
- `temperature=0.2` for chat, minimizing regeneration cycles.
- Token caps on every prompt (`max_tokens` 900 / 1200 / 1400) to
  prevent runaway outputs.
- Stub mode for development and grading so contributors can test
  without burning real compute.
