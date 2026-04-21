# Architecture

## High-Level View

```mermaid
flowchart LR
    U[User / Developer] --> UI[React UI<br/>Vite + Tailwind]
    UI -->|HTTP/JSON /api/*| API[FastAPI<br/>CORS, routers, schemas]
    UI -->|SSE /agent/stream| API

    subgraph AGENT[Autonomous Agent]
        direction TB
        PLAN[Planner<br/>LLM: N diverse queries] --> SRCH[DDG HTML search<br/>no API key]
        SRCH --> JUDGE[Relevance Judge<br/>LLM: keep or skip]
        JUDGE -->|keep| ING
    end

    subgraph RAG[RAG Pipeline]
        direction TB
        ING[Scraper<br/>requests + BS4] --> CHK[Chunker<br/>semantic windows]
        CHK --> EMB[Embedder<br/>OpenAI text-embedding-3-small]
        EMB --> VS[(FAISS<br/>IndexFlatIP)]
        VS --> RET[Retriever<br/>top-k cosine]
        RET --> PR[Prompt Composer<br/>system + user templates]
        PR --> LLM[OpenAI Chat<br/>gpt-4o-mini]
    end

    API --> AGENT
    API --> RAG
    API --> MET[Metrics Store<br/>in-memory rolling]

    LLM --> API
    MET --> API
    API --> UI
```

## Request Sequence — Chat

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as FastAPI
    participant E as Embeddings
    participant V as FAISS
    participant L as Chat LLM

    U->>F: Types question
    F->>B: POST /api/chat {query}
    B->>E: embed(query)
    E-->>B: query vector
    B->>V: search(vector, k=4)
    V-->>B: top-k chunks + scores
    B->>B: build_chat_user_prompt(query, chunks)
    B->>L: chat(system=CHAT_SYSTEM, user=prompt)
    L-->>B: answer + usage
    B->>B: compute confidence + record metrics
    B-->>F: {answer, citations, confidence, latency, tokens}
    F-->>U: Renders Markdown + citation pills
```

## Request Sequence — Ingestion

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as FastAPI
    participant S as Scraper
    participant C as Chunker
    participant E as Embeddings
    participant V as FAISS

    U->>F: Submits URL
    F->>B: POST /api/ingest {url}
    B->>S: scrape_url(url)
    S-->>B: ScrapedPage(title, text)
    B->>C: chunk_text(text)
    C-->>B: list[Chunk]
    B->>E: embed(chunks)
    E-->>B: vectors
    B->>V: add(doc_id, vectors, metadata)
    V-->>B: ok
    B-->>F: {doc_id, chunks, latency_ms}
```

## Module Responsibilities

| Module                         | Responsibility                                               |
| ------------------------------ | ------------------------------------------------------------ |
| `app/core/config.py`           | Env-based settings via `pydantic-settings`                   |
| `app/core/metrics.py`          | Thread-safe rolling metrics                                  |
| `app/services/llm.py`          | OpenAI wrapper with retries + stub-mode fallback             |
| `app/services/search.py`       | DuckDuckGo HTML search, link unwrap, blacklist filter         |
| `app/services/agent.py`        | Autonomous research loop (plan → search → scrape → judge → ingest) |
| `app/services/scraper.py`      | Fetch + clean HTML (strips scripts, nav, footer, etc.)       |
| `app/services/chunker.py`      | Paragraph + heading-aware semantic chunking with overlap     |
| `app/services/vector_store.py` | FAISS index + JSON metadata, disk-persisted                  |
| `app/services/rag.py`          | End-to-end RAG: ingest, chat, generate-docs, synthetic       |
| `app/prompts/templates.py`     | System and user prompt builders                              |
| `app/routers/*`                | Thin FastAPI route handlers; validation via `schemas.py`     |
| `frontend/src/pages/*`         | Chat, KB, DocsGen, Synthetic, Metrics                        |
| `frontend/src/components/*`    | Reusable UI primitives (Card, Button, Spinner, Markdown…)    |
