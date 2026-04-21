"""Thin wrapper around the OpenAI SDK for chat + embeddings.

Centralizes retries, timeouts, and stub-mode fallback so the app still runs
for demos when no API key is configured.
"""
from __future__ import annotations

import hashlib
import os
import random
from typing import Iterable

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self) -> None:
        s = get_settings()
        self.settings = s
        self.stub_mode = not s.openai_api_key
        self._client: OpenAI | None = None
        if not self.stub_mode:
            self._client = OpenAI(api_key=s.openai_api_key, timeout=s.request_timeout)
            logger.info("LLM client ready: chat=%s embed=%s", s.openai_chat_model, s.openai_embed_model)
        else:
            logger.warning("OPENAI_API_KEY not set — running in STUB mode (deterministic fake outputs).")

    # -------- embeddings --------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=8))
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.stub_mode:
            return [_stub_embed(t) for t in texts]
        resp = self._client.embeddings.create(model=self.settings.openai_embed_model, input=texts)
        return [d.embedding for d in resp.data]

    # -------- chat --------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=8))
    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 900,
    ) -> dict:
        if self.stub_mode:
            return _stub_chat(system, user)

        resp = self._client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        msg = resp.choices[0].message.content or ""
        usage = resp.usage
        return {
            "text": msg,
            "tokens": getattr(usage, "total_tokens", None),
            "model": resp.model,
        }


# ---- Stub helpers: deterministic, dependency-free ----

_EMBED_DIM = 384


def _stub_embed(text: str) -> list[float]:
    """Hash-based pseudo-embedding for offline demos. Not semantically useful
    but keeps downstream code runnable without an API key."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    vec = [rng.uniform(-1, 1) for _ in range(_EMBED_DIM)]
    norm = sum(x * x for x in vec) ** 0.5 or 1.0
    return [x / norm for x in vec]


def _stub_chat(system: str, user: str) -> dict:
    preview = (user[:300] + "...") if len(user) > 300 else user
    body = (
        "[STUB MODE — OPENAI_API_KEY not configured]\n"
        "This is a deterministic fake response used for local demos.\n\n"
        f"System role summary: {system[:140]}...\n\n"
        f"Prompt echo: {preview}\n\n"
        "Answer (grounded in provided context if any):\n"
        "- Set OPENAI_API_KEY in backend/.env to get real LLM responses.\n"
        "- All retrieval, chunking, and UI flows still work end-to-end.\n"
    )
    return {"text": body, "tokens": None, "model": "stub"}


_singleton: LLMClient | None = None


def get_llm() -> LLMClient:
    global _singleton
    if _singleton is None:
        _singleton = LLMClient()
    return _singleton
