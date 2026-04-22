# DocuMind — AI Technical Documentation Assistant

A production-quality, end-to-end Generative AI web application for developers.
It combines **Retrieval-Augmented Generation (RAG)**, **Synthetic Data
Generation**, and **structured Prompt Engineering** to help developers generate,
improve, and query technical documentation — with inline citations and
confidence scoring.

> Built for a university Generative AI final project. Real code, real
> dependencies, real endpoints — no pseudo-implementations.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Setup](#setup)
5. [Running the App](#running-the-app)
6. [API Usage](#api-usage)
7. [Example Queries](#example-queries)
8. [Example Outputs](#example-outputs)
9. [Project Structure](#project-structure)
10. [Evaluation Metrics](#evaluation-metrics)
11. [License](#license)

---

## Features

- **Autonomous research agent** — give it a topic (no URL required), and
  it plans diverse search queries, crawls DuckDuckGo, LLM-judges each
  candidate page for relevance, and auto-ingests the good ones. Live
  progress streams to the UI over Server-Sent Events.
- **RAG pipeline** — scrape URLs, chunk intelligently, embed with OpenAI,
  store in FAISS, retrieve top-k, inject into prompts.
- **Chat with citations** — every answer carries `[S#]` markers linking to
  the source document, with per-answer confidence and latency.
- **Documentation generator** — produce publication-quality Markdown docs
  from a topic or a code snippet, optionally grounded in the KB.
- **Synthetic data generator** — produce diverse Q&A pairs (factual /
  reasoning / edge-case / example) from any ingested document.
- **Prompt engineering** — role-separated system/user prompts, explicit
  instruction hierarchy, edge-case handling, output contracts.
- **Live metrics dashboard** — latency, retrieval score, token usage,
  event log — refreshed every 5 s.
- **Stub mode** — when `OPENAI_API_KEY` is missing, the app runs with
  deterministic fake embeddings and fake LLM responses so you can
  demo the entire UI + pipeline offline.
- **Polished UI** — dark dashboard, sidebar navigation, Markdown rendering,
  citation pills, copy buttons, loading states, empty states, error states.

---

## Tech Stack

| Layer            | Technology                                              |
| ---------------- | ------------------------------------------------------- |
| Backend          | Python 3.10+, FastAPI, Uvicorn, Pydantic v2             |
| LLM / Embeddings | OpenAI (`gpt-4o-mini`, `text-embedding-3-small`)        |
| Vector store     | FAISS (`IndexFlatIP`, cosine via L2 normalization)      |
| Scraping         | `requests` + BeautifulSoup (lxml parser)                |
| Frontend         | React 18, Vite, React Router, Tailwind CSS              |
| Markdown         | `react-markdown` + `remark-gfm`                         |
| Testing          | `pytest`, FastAPI `TestClient`                          |

All dependencies are real, installable, and pinned.

---

## Architecture

```
┌─────────────┐   HTTP/JSON    ┌────────────────────────────────────────┐
│   React UI  │ ─────────────► │  FastAPI  (CORS, routers, schemas)     │
│  (Vite)     │ ◄───────────── │                                        │
└─────────────┘                │  ┌──────────────────────────────────┐  │
                               │  │ RAG pipeline                     │  │
                               │  │  scrape → chunk → embed → store  │  │
                               │  │  retrieve → prompt → LLM         │  │
                               │  └────────┬──────────────┬──────────┘  │
                               │           │              │             │
                               │           ▼              ▼             │
                               │  ┌─────────────┐   ┌──────────────┐    │
                               │  │ OpenAI API  │   │   FAISS      │    │
                               │  │  (chat +    │   │  (vectors +  │    │
                               │  │  embed)     │   │   metadata)  │    │
                               │  └─────────────┘   └──────────────┘    │
                               └────────────────────────────────────────┘
```

See `docs/architecture.md` for a full Mermaid diagram and sequence flows.

---

## Setup

### Prerequisites

- Python **3.10+**
- Node.js **18+**
- An OpenAI API key (optional — see *Stub mode* below)

### 1. Clone and enter the project

```bash
cd Final_Project
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-... (or leave blank for stub mode)

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd ../frontend
npm install
```

---

## Running the App

Open **two terminals**.

**Terminal 1 — backend:**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
# or simply: ./run.sh
```

Open `http://localhost:8000/docs` for auto-generated Swagger UI.

**Terminal 2 — frontend:**

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

Vite proxies `/api/*` to the backend automatically.

### Stub mode

If `OPENAI_API_KEY` is unset, the backend starts in **stub mode**:
- Embeddings are deterministic hash-based pseudo-vectors.
- Chat returns a templated fake response.
- All routing, retrieval, metrics, and UI flows still work end-to-end.

This lets you demo the full application without an API key. The sidebar
shows a ⚠️ indicator when stub mode is active.

---

## API Usage

Base URL: `http://localhost:8000/api`

### `POST /ingest`

Scrape a URL and add it to the knowledge base.

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://fastapi.tiangolo.com/"}'
```

Response:
```json
{ "doc_id": "…", "source": "https://…", "title": "FastAPI",
  "chunks": 18, "latency_ms": 2134.7 }
```

### `POST /ingest/text`

Ingest raw text directly.

```bash
curl -X POST http://localhost:8000/api/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"title": "Pydantic notes", "text": "…long text…"}'
```

### `POST /chat`

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?"}'
```

Response:
```json
{
  "answer": "FastAPI is a modern, fast web framework… [S1]",
  "citations": [
    { "id": "S1", "title": "FastAPI", "url": "https://fastapi.tiangolo.com/", "score": 0.78 }
  ],
  "confidence": 0.71,
  "retrieval_score": 0.72,
  "latency_ms": 1824.3,
  "tokens": 612,
  "model": "gpt-4o-mini"
}
```

### `POST /generate-docs`

```bash
curl -X POST http://localhost:8000/api/generate-docs \
  -H "Content-Type: application/json" \
  -d '{"topic": "How to define a Pydantic model", "use_retrieval": true}'
```

### `POST /agent/research` · `GET /agent/stream`

The autonomous research agent. Give it a topic, and it does the rest —
plans queries, searches, scrapes, judges relevance, ingests.

```bash
# Synchronous: returns the full event log + summary after the run completes
curl -X POST http://localhost:8000/api/agent/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "FastAPI dependency injection", "num_queries": 3, "per_query": 3}'

# Streaming: Server-Sent Events, one JSON object per `data:` line
curl -N "http://localhost:8000/api/agent/stream?topic=FastAPI%20DI&num_queries=2&per_query=2"
```

Event types the stream emits: `start`, `plan`, `search_start`,
`search_results`, `scrape_start`, `scrape_done`, `scrape_failed`,
`judge`, `ingest`, `ingest_failed`, `skip`, `done`, `error`.

### `POST /synthetic-data`

```bash
curl -X POST http://localhost:8000/api/synthetic-data \
  -H "Content-Type: application/json" \
  -d '{"n_pairs": 5}'
```

### `GET /knowledge-base` · `DELETE /knowledge-base`

List indexed documents, or clear all.

### `GET /metrics` · `GET /health`

System observability and liveness.

---

## Example Queries

Good test URLs to ingest:

- `https://fastapi.tiangolo.com/`
- `https://docs.pydantic.dev/latest/`
- `https://react.dev/learn`
- `https://tailwindcss.com/docs/utility-first`

After ingestion, try:

- "What is FastAPI and what problem does it solve?"
- "How do I define a Pydantic model with a required field?"
- "What is the difference between a component and a hook in React?"
- "When should I *not* use Tailwind's `@apply` directive?"
- *(off-topic test)* "What's the capital of Iceland?" → should return "I don't have enough information…"

---

## Example Outputs

**Chat answer** (abbreviated):

> FastAPI is a modern, high-performance Python web framework for building APIs
> based on standard Python type hints [S1]. It uses Starlette under the hood
> for the web parts and Pydantic for data validation [S1].
>
> ```python
> from fastapi import FastAPI
> app = FastAPI()
>
> @app.get("/")
> def root():
>     return {"ok": True}
> ```
>
> **Sources**
> - [S1] FastAPI — https://fastapi.tiangolo.com/

**Synthetic pair** (abbreviated):

```json
{
  "question": "What happens when a FastAPI path operation has no return type annotation?",
  "answer": "The response is still returned as JSON, but no response_model validation or schema documentation is generated for it.",
  "category": "edge_case",
  "difficulty": "medium"
}
```

---

## Project Structure

```
Final_Project/
├── backend/
│   ├── app/
│   │   ├── core/          # config, logging, metrics
│   │   ├── prompts/       # prompt templates (the heart of the system)
│   │   ├── routers/       # FastAPI routes
│   │   ├── services/      # llm, scraper, chunker, vector_store, rag
│   │   ├── main.py
│   │   └── schemas.py
│   ├── requirements.txt
│   ├── .env.example
│   └── run.sh
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/    # Card, Button, Markdown, etc.
│   │   ├── pages/         # Chat, KnowledgeBase, DocsGen, Synthetic, Metrics
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── data/                  # persisted FAISS index + sample corpora
├── docs/                  # architecture, implementation, ethics, future work
├── tests/                 # pytest suite + sample_urls.json
├── website/               # project landing page (static HTML)
└── README.md
```

---

## Evaluation Metrics

The `/api/metrics` endpoint tracks:

- **Retrieval quality** — mean cosine similarity of retrieved chunks.
- **Latency** — per-request wall time (chat, ingest, docs, synthetic).
- **Token usage** — from OpenAI response `usage.total_tokens`.
- **Counters** — requests per endpoint, error count.
- **Recent events** — rolling window of the last 200 operations.

These are visualized in real time on the **Metrics** page.

A simple offline evaluation script lives at `tests/eval_retrieval.py`.

---

## License

MIT — see top of each source file. For educational use.
