---
title: "DocuMind — AI Technical Documentation Assistant"
subtitle: "Generative AI Final Project · RAG + Prompt Engineering + Synthetic Data + Autonomous Research Agent"
author: "Prathamesh Shukla"
date: "April 2026"
documentclass: article
geometry: margin=1in
fontsize: 11pt
linkcolor: blue
urlcolor: blue
toccolor: black
header-includes:
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \rhead{DocuMind}
  - \lhead{Technical Documentation}
  - \cfoot{\thepage}
---

\clearpage

# Project Overview

**DocuMind** is a production-quality, end-to-end Generative AI web application
that helps developers generate, understand, and enhance technical documentation
with inline citations, confidence scoring, and an autonomous research agent
that grows its own knowledge base.

The system integrates **three required rubric components plus a substantive
beyond-scope addition**:

1. **Prompt Engineering** — four role-separated system prompts with
   priority-ordered constraints, edge-case handling, and strict output
   contracts (Markdown for chat/docs, JSON for synthetic data and agent
   decisions).
2. **Retrieval-Augmented Generation (RAG)** — HTML scraping, semantic
   chunking, OpenAI embeddings, FAISS (cosine via L2-normalized inner
   product), top-k retrieval, and prompt injection with `[S#]` citations.
3. **Synthetic Data Generation** — diverse Q&A pair generation with
   category-forced diversity (factual / reasoning / edge-case / example),
   strict JSON schema, and a regex-fallback parser for defensive decoding.
4. **Bonus — Autonomous Research Agent** *(beyond scope)*: given only a
   natural-language topic, the agent plans diverse search queries, crawls
   DuckDuckGo, scrapes result pages, asks the LLM to judge each page's
   relevance, and auto-ingests the good ones. Progress is streamed to the
   UI live over Server-Sent Events.

## Stack

- **Backend** — FastAPI, Pydantic v2, OpenAI SDK, FAISS, BeautifulSoup,
  Tenacity (retries).
- **Frontend** — React 18, Vite, Tailwind CSS, Framer Motion, React
  Router, react-markdown.
- **Tests** — pytest + FastAPI `TestClient`; 19/19 passing, mocked
  network for agent tests.

## Demo

- **10-minute video demo**: <https://youtu.be/HR--Zm4KlT0>
- **GitHub repository**: <https://github.com/psshukla02/documind>
- **Runs offline without an API key** via deterministic stub mode — useful
  for graders without an OpenAI account.

This document compiles the rubric-alignment summary, architecture,
implementation details, autonomous agent design, performance metrics,
challenges encountered, ethical considerations, and future improvements.

\clearpage
