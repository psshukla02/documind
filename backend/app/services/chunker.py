"""Semantic-ish chunker.

Splits on paragraph/heading boundaries first, then packs paragraphs into
windows of approximately `chunk_size` characters with `chunk_overlap` char
overlap between adjacent chunks. Keeps chunks coherent without requiring a
token tokenizer in the hot path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


_PARA_SPLIT = re.compile(r"\n\s*\n")
_HEADING = re.compile(r"^(#{1,6}\s|\d+\.\s|[A-Z][A-Za-z0-9 ]{0,60}:\s*$)")


@dataclass
class Chunk:
    text: str
    ordinal: int


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[Chunk]:
    paragraphs = [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    buf: list[str] = []
    buf_len = 0

    def flush():
        nonlocal buf, buf_len
        if buf:
            chunks.append("\n\n".join(buf).strip())
            buf = []
            buf_len = 0

    for para in paragraphs:
        p_len = len(para) + 2

        # Oversized paragraph: hard-split
        if p_len > chunk_size:
            flush()
            for i in range(0, len(para), chunk_size - chunk_overlap):
                chunks.append(para[i : i + chunk_size])
            continue

        # Heading-ish boundary: try to start a new chunk if we already have content
        if _HEADING.match(para) and buf_len > chunk_size // 2:
            flush()

        if buf_len + p_len > chunk_size:
            flush()

        buf.append(para)
        buf_len += p_len

    flush()

    # Add overlap: append tail of previous chunk to head of next
    overlapped: list[str] = []
    for i, c in enumerate(chunks):
        if i == 0:
            overlapped.append(c)
            continue
        prev_tail = chunks[i - 1][-chunk_overlap:]
        overlapped.append(prev_tail + "\n" + c)

    return [Chunk(text=t, ordinal=i) for i, t in enumerate(overlapped)]
