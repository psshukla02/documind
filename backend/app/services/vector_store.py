"""FAISS-backed vector store with JSON-persisted metadata.

- Cosine similarity via L2-normalized inner product.
- One global index, persisted to disk under `vector_store_path`.
- Metadata (chunk text, source url, title, ordinal) stored alongside.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from typing import Any

import faiss
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DocRecord:
    id: str
    doc_id: str
    source: str
    title: str
    ordinal: int
    text: str


@dataclass
class SearchHit:
    record: DocRecord
    score: float


class VectorStore:
    def __init__(self, dim: int, path: str):
        self.dim = dim
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.index_path = os.path.join(path, "index.faiss")
        self.meta_path = os.path.join(path, "meta.json")
        self._lock = threading.Lock()
        self._index: faiss.IndexFlatIP
        self._records: list[DocRecord] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self._index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._records = [DocRecord(**r) for r in data]
            logger.info("Loaded vector store: %d vectors", self._index.ntotal)
        else:
            self._index = faiss.IndexFlatIP(self.dim)
            self._records = []
            logger.info("Initialized empty vector store (dim=%d)", self.dim)

    def _persist(self) -> None:
        faiss.write_index(self._index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self._records], f)

    def _normalize(self, vecs: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms

    def add(
        self,
        doc_id: str,
        source: str,
        title: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks/embeddings length mismatch")
        if not chunks:
            return 0

        vecs = np.array(embeddings, dtype="float32")
        if vecs.shape[1] != self.dim:
            raise ValueError(f"embedding dim {vecs.shape[1]} != store dim {self.dim}")
        vecs = self._normalize(vecs)

        with self._lock:
            self._index.add(vecs)
            for i, c in enumerate(chunks):
                self._records.append(
                    DocRecord(
                        id=str(uuid.uuid4()),
                        doc_id=doc_id,
                        source=source,
                        title=title,
                        ordinal=i,
                        text=c,
                    )
                )
            self._persist()
        return len(chunks)

    def search(self, embedding: list[float], k: int = 4) -> list[SearchHit]:
        if self._index.ntotal == 0:
            return []
        q = np.array([embedding], dtype="float32")
        q = self._normalize(q)
        k = min(k, self._index.ntotal)
        scores, idxs = self._index.search(q, k)
        hits: list[SearchHit] = []
        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            if idx < 0 or idx >= len(self._records):
                continue
            hits.append(SearchHit(record=self._records[idx], score=float(score)))
        return hits

    def list_documents(self) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for r in self._records:
            g = grouped.setdefault(
                r.doc_id,
                {"doc_id": r.doc_id, "source": r.source, "title": r.title, "chunks": 0},
            )
            g["chunks"] += 1
        return sorted(grouped.values(), key=lambda x: x["title"].lower())

    def get_document_chunks(self, doc_id: str) -> list[DocRecord]:
        return [r for r in self._records if r.doc_id == doc_id]

    def reset(self) -> None:
        with self._lock:
            self._index = faiss.IndexFlatIP(self.dim)
            self._records = []
            self._persist()

    @property
    def size(self) -> int:
        return self._index.ntotal


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        from app.services.llm import _EMBED_DIM, get_llm

        llm = get_llm()
        # For real OpenAI embeddings we probe once to discover the dim.
        if llm.stub_mode:
            dim = _EMBED_DIM
        else:
            probe = llm.embed(["dimension probe"])
            dim = len(probe[0])
        _store = VectorStore(dim=dim, path=get_settings().vector_store_path)
    return _store
