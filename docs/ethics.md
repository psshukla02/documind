# Ethical Considerations

## Bias

- **Source bias.** The assistant is only as representative as the documents
  ingested. If a team only ingests blog posts from one vendor, answers will
  reflect that vendor's opinions. We surface the source URL on every citation
  so the user can audit the provenance.
- **Model bias.** `gpt-4o-mini` inherits whatever biases exist in OpenAI's
  training data. Our system prompts minimize free-form opinions ("Hard
  constraint: ground every factual claim in the provided sources") but
  cannot eliminate them.

## Hallucination

- We never rely on the model to be honest by default. The prompt contract
  requires inline citations; the UI highlights missing citations via the
  confidence bar; the retrieval-score display makes it obvious when the
  model is answering from thin context.
- Even so, the system **can** still produce plausible-sounding wrong
  answers. Users must treat every output as a draft to be verified, not a
  ground truth. The README and Chat empty-state explicitly frame the tool
  that way.

## Data Privacy

- Ingested content is stored locally in `data/vector_store/`. Nothing is
  exfiltrated except the prompts sent to OpenAI at query time.
- **Do not ingest proprietary or PII-containing documents without
  understanding OpenAI's data retention policy** (API traffic is retained
  for abuse monitoring for 30 days by default; zero-retention agreements
  are available on enterprise plans).
- The scraper uses a bot-identifying User-Agent and respects standard HTTP
  semantics (no parallel hammering, 30-second timeout). It does not attempt
  to bypass paywalls or authentication.

## Misuse

Risks and mitigations:

| Risk                                          | Mitigation                                                                 |
| --------------------------------------------- | -------------------------------------------------------------------------- |
| Generating fake docs to impersonate a library | Citations and confidence scoring make unverified outputs obvious.          |
| Mass scraping of third-party sites            | No built-in crawler — single-URL ingestion only.                           |
| Prompt injection via scraped content          | System prompt runs first; user-visible citations expose injected content.  |
| Leaking API keys in logs                      | Logger formats never include env vars; `.env` is gitignored.               |

## Responsible Use Checklist

- ✅ Do ingest public documentation, your team's internal wikis, or source
  code you own.
- ✅ Do treat generated docs as drafts requiring human review.
- ❌ Don't ingest medical, legal, or financial documents and rely on the
  output without a qualified professional.
- ❌ Don't strip citations before sharing generated content — they're the
  user's audit trail.
