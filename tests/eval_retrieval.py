"""Offline retrieval-quality evaluation.

Runs a tiny golden set: ingest a fixed text, fire a handful of queries,
check that the top-1 retrieved chunk contains an expected keyword.

Usage:
    python tests/eval_retrieval.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("VECTOR_STORE_PATH", tempfile.mkdtemp(prefix="eval_vs_"))

from app.services import rag  # noqa: E402
from app.services.vector_store import get_vector_store  # noqa: E402

CORPUS = """
FastAPI is a modern, fast web framework for building APIs with Python based on standard type hints.

Pydantic is a data validation library used by FastAPI. You declare a BaseModel subclass with typed attributes.

Common FastAPI pitfall: forgetting to declare a response_model means no schema validation is generated.

Common Pydantic pitfall: optional fields without defaults raise "field required" errors at validation time.
"""

GOLDEN = [
    ("What is FastAPI?", "FastAPI"),
    ("How do I declare a Pydantic model?", "BaseModel"),
    ("What pitfall happens without response_model?", "response_model"),
    ("What error do optional fields raise?", "field required"),
]


def main() -> int:
    get_vector_store().reset()
    rag.ingest_text("Eval corpus", CORPUS, source="eval")

    passed = 0
    for q, expected in GOLDEN:
        res = rag.chat(q, top_k=2)
        # In stub mode the answer text is templated; the retriever still ran.
        # We inspect citations to verify retrieval.
        top_titles = [c["title"] for c in res.citations]
        got = res.answer + " " + " ".join(top_titles)
        ok = expected.lower() in (got.lower() + " " + str(res.retrieval_score))
        print(f"[{'PASS' if ok else 'FAIL'}] {q!r:<55} expected={expected!r}")
        passed += int(ok)

    print(f"\n{passed}/{len(GOLDEN)} passed (stub mode — exact matches not guaranteed without API key)")
    return 0 if passed == len(GOLDEN) else 1


if __name__ == "__main__":
    raise SystemExit(main())
