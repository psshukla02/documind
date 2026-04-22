# Rubric Alignment

This project targets the *Generative AI Final Project* rubric. The rubric
requires at least **two** of the five core components; DocuMind implements
**three** deeply, plus a substantial beyond-scope addition.

## Core Components — 3 of 5 Implemented

| # | Component              | Status   | Primary Evidence                                                         |
|---|------------------------|----------|--------------------------------------------------------------------------|
| 1 | Prompt Engineering     | **Done** | `backend/app/prompts/templates.py` — 4 role-separated system prompts, priority-ordered constraints, output contracts, edge-case fallbacks, regex-fallback parsers. |
| 2 | Fine-Tuning            | —        | *Not pursued; rubric floor is two components.*                           |
| 3 | RAG                    | **Done** | `backend/app/services/{scraper, chunker, vector_store, rag}.py` — scrape → chunk → embed → FAISS → retrieve → compose → cite. |
| 4 | Multimodal             | —        | *Not pursued; text-only by design.*                                      |
| 5 | Synthetic Data         | **Done** | `backend/app/services/rag.py::generate_synthetic` + `SYNTHETIC_SYSTEM` prompt; diversity-forced categories, strict JSON contract. |

## Beyond Scope — Autonomous Research Agent

This is a fully independent capability *not required by the rubric*:

- **Goal.** Turn a natural-language topic into a self-expanding knowledge
  base without human URL curation.
- **Location.** `backend/app/services/agent.py` + `backend/app/routers/agent.py`
  + `backend/app/services/search.py` + `frontend/src/pages/AgentPage.jsx`.
- **Capabilities:**
    - LLM-planned diverse search queries (`AGENT_PLANNER_SYSTEM`).
    - DuckDuckGo HTML scraping (no API key required).
    - Domain + extension blacklist (video, social, binary files).
    - LLM relevance judge per page (`RELEVANCE_JUDGE_SYSTEM`,
      strict-JSON decision).
    - Automatic chunking + embedding + storage.
    - De-duplication against the existing vector store.
    - Server-Sent Events live progress stream to the UI.

A single agent run on the topic *"FastAPI framework"* autonomously
discovers the official FastAPI site and the FastAPI ReadTheDocs tutorial,
judges them both as relevant, and ingests **105 chunks in 9.8 seconds** —
no URL provided by the user.

## Supporting Requirements

| Rubric Item                         | Evidence                                                                   |
|-------------------------------------|----------------------------------------------------------------------------|
| GitHub repo with source             | <https://github.com/psshukla02/documind> — 75+ files, all deps pinned.      |
| Setup instructions                  | `README.md` §Setup, `backend/run.sh`, `.env.example`.                      |
| Testing scripts                     | `tests/` — 5 pytest modules, 19 tests, 100% pass; offline `eval_retrieval.py`. |
| Example outputs                     | `README.md` §Example Outputs, `tests/sample_urls.json`.                    |
| Knowledge base                      | Runtime-persisted to `data/vector_store/` (FAISS index + JSON metadata).   |
| Documentation PDF                   | This document.                                                             |
| 10-minute demo video                | <https://youtu.be/HR--Zm4KlT0>.                                            |
| Web page                            | `website/index.html` (dark, polished landing page).                         |
| Evaluation metrics                  | `/api/metrics` endpoint + live dashboard (`frontend/src/pages/MetricsPage.jsx`). |

## Design Highlights

- **Hallucination mitigation** is built in, not bolted on: required inline
  citations, retrieval-score-weighted confidence bar, mandatory fallback
  phrase when context is thin.
- **Stub mode** ships with the application: if `OPENAI_API_KEY` is absent,
  embeddings are deterministic hash-seeded vectors and LLM outputs are
  templated — the full pipeline (search, retrieval, UI, metrics, SSE
  streaming) still runs end-to-end for graders without an API key.
- **Every answer is auditable.** Citations, source URLs, chunk scores,
  retrieval average, latency, and token count are surfaced per response.
- **Live observability.** A rolling in-memory metrics store powers a
  5-second auto-refresh dashboard — counters, averages, and recent events.

\clearpage
