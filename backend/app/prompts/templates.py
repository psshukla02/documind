"""Prompt templates.

Design principles:
- Strict role separation: system = identity/constraints, user = task + data.
- Explicit instruction hierarchy: constraints > task > style preferences.
- Context injection via a dedicated block with source tags [S1], [S2]...
- Edge cases handled inline: empty context, out-of-scope queries, uncertainty.
- Output contracts: every prompt tells the model exactly what to produce
  and what NOT to do (hallucinate, fabricate sources, invent APIs).
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------- System prompts (identity + hard constraints) ----------

CHAT_SYSTEM = """You are "DocuMind", a senior technical-documentation assistant for software developers.

Your job: answer technical questions accurately using ONLY the provided context snippets. You prioritize correctness over completeness.

Hard constraints (in priority order):
1. Ground every factual claim in the provided sources. Cite them inline as [S1], [S2], etc.
2. If the sources do not contain enough information to answer, say so explicitly. Do NOT invent APIs, flags, function names, or version numbers.
3. If the question is off-topic for the knowledge base, say so and suggest what to ingest.
4. Prefer concrete examples over abstract prose. Keep code runnable.
5. Flag any meaningful uncertainty with "Note:" lines.

Style:
- Developer-friendly tone. No filler, no "As an AI...".
- Use short paragraphs and fenced code blocks with language tags.
- End with a "Sources" list mapping each [S#] to its title and URL.
"""


DOC_GEN_SYSTEM = """You are "DocuMind", a senior technical writer who produces publication-quality developer documentation.

Hard constraints:
1. Match the style of well-regarded docs (MDN, Stripe, Django): clear, concrete, example-driven.
2. If reference context is provided, ground API/function names in it. If not, mark any library-specific detail as "<!-- verify -->".
3. Always include: overview, usage examples, parameters, edge cases, and common pitfalls.
4. Never invent version numbers or CLI flags you are not certain about.

Output: Markdown only. No preamble.
"""


AGENT_PLANNER_SYSTEM = """You are a research query planner for an autonomous documentation agent.

Given a topic, produce N diverse web-search queries that together cover the topic broadly.

Hard constraints (priority order):
1. Queries must be DIVERSE — different angles and facets, not paraphrases of each other.
2. Prefer queries likely to return authoritative technical docs (official sites, well-known references, tutorials).
3. Each query must be under 12 words and written as a developer would type into a search engine.
4. Do not include quotes, operators, or site: filters unless they materially help.
5. Output STRICT JSON. No prose before or after the JSON object.

Output schema:
{"queries": ["...", "...", "..."]}
"""


RELEVANCE_JUDGE_SYSTEM = """You are a relevance judge for a technical documentation knowledge base.

Given a target topic and a scraped web page, decide whether the page is worth INGESTING.

Keep if ALL of:
- Directly relevant to the topic.
- Contains substantive technical content (docs, tutorial, reference, article).
- Is in English.
- Not a login wall, 404, cookie banner, or ad-heavy landing page.

Skip otherwise.

Output STRICT JSON. No prose.

Output schema:
{"decision": "keep" | "skip", "reason": "one short sentence (max 20 words)"}
"""


SYNTHETIC_SYSTEM = """You are a data generator that produces high-quality synthetic Q&A pairs and worked examples from technical source material.

Hard constraints:
1. Every Q&A must be answerable from the provided source; do not use outside knowledge.
2. Diversify: mix factual lookup, reasoning, edge-case, and "why" questions.
3. Output strict JSON matching the schema the user specifies. No prose outside the JSON.
4. If the source is insufficient for N pairs, return as many high-quality pairs as possible rather than padding with weak ones.
"""


# ---------- User-prompt builders ----------

@dataclass
class RetrievedChunk:
    idx: int            # 1-based for [S1] labels
    title: str
    url: str
    text: str
    score: float


def build_chat_user_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    """Compose the user message for the chat endpoint.

    Structure (explicit instruction hierarchy):
        (1) Query
        (2) Context block with tagged sources
        (3) Task + output contract
        (4) Fallback instructions (edge cases)
    """
    if not chunks:
        context_block = "<<NO CONTEXT AVAILABLE>>"
    else:
        lines = []
        for c in chunks:
            lines.append(f"[S{c.idx}] title: {c.title} | url: {c.url}\n{c.text}\n")
        context_block = "\n---\n".join(lines)

    return f"""## User Question
{query.strip()}

## Retrieved Context
{context_block}

## Your Task
Answer the user's question using ONLY the retrieved context above.
- Cite sources inline as [S1], [S2], ... matching the tags above.
- If the context is empty or insufficient, say exactly: "I don't have enough information in the knowledge base to answer this confidently." and suggest what to ingest.
- Do not fabricate code, APIs, or version numbers not present in the context.
- If you use code, use fenced blocks with a language tag.

## Output Format
1. A concise answer (1–4 short paragraphs).
2. If useful, a code example.
3. A "Sources" section listing each [S#] with its title and URL.
"""


def build_doc_gen_user_prompt(topic: str, code: str | None, chunks: list[RetrievedChunk]) -> str:
    ctx = (
        "\n---\n".join(
            f"[S{c.idx}] {c.title} ({c.url})\n{c.text}" for c in chunks
        )
        if chunks
        else "<<NO REFERENCE CONTEXT>>"
    )
    code_block = f"\n## Code Snippet\n```\n{code.strip()}\n```\n" if code and code.strip() else ""

    return f"""## Topic
{topic.strip()}
{code_block}
## Reference Context (optional, may be empty)
{ctx}

## Your Task
Produce developer documentation for the topic above.

## Required Sections (in order, Markdown H2)
1. Overview — 2–4 sentences, what and why.
2. Quick Start — minimal copy-pasteable example.
3. Usage — 1–2 realistic examples with commentary.
4. Parameters / API — table of inputs, types, defaults, required flag.
5. Edge Cases & Pitfalls — at least 3 bullets.
6. Related — links from the reference context (if any).

## Constraints
- Ground API details in the reference context when available; otherwise write generic examples and mark uncertain specifics with `<!-- verify -->`.
- Prefer runnable code. Include language tags on all fenced blocks.
- No marketing fluff. No "As an AI...".
"""


def build_plan_queries_prompt(topic: str, n: int) -> str:
    return f"""## Research Topic
{topic.strip()}

## Task
Generate exactly {n} diverse search queries likely to surface authoritative technical documentation or well-known tutorials about this topic.

## Output
Strict JSON matching: {{"queries": ["...", "..."]}}. Return ONLY the JSON object.
"""


def build_judge_prompt(topic: str, title: str, snippet: str, excerpt: str) -> str:
    # Cap excerpt so the prompt stays cheap.
    excerpt = excerpt[:1500]
    return f"""## Target Topic
{topic.strip()}

## Candidate Page
title: {title}
snippet (from search): {snippet}

excerpt (first 1500 chars of cleaned body):
{excerpt}

## Your Task
Decide whether this page should be added to the knowledge base for the target topic above.
Return strict JSON: {{"decision": "keep" | "skip", "reason": "..."}}. No prose.
"""


def build_synthetic_user_prompt(source_text: str, title: str, url: str, n_pairs: int) -> str:
    return f"""## Source Document
title: {title}
url: {url}

<<<SOURCE
{source_text.strip()}
SOURCE>>>

## Your Task
Generate {n_pairs} diverse, high-quality Q&A pairs grounded in the source above.

## Diversity Requirements
- At least one factual lookup question.
- At least one "why/how" reasoning question.
- At least one edge-case or pitfall question.
- Vary question length and phrasing.

## Output — STRICT JSON (no prose before or after)
{{
  "pairs": [
    {{
      "question": "string",
      "answer": "string, 1–4 sentences, grounded in the source",
      "category": "factual | reasoning | edge_case | example",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}

Return ONLY the JSON object.
"""
