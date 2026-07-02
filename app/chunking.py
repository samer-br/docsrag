"""Markdown-aware chunking.

Splits a document by headings first (so chunks stay topically coherent), then
packs paragraphs into ~chunk_size character windows with a small overlap so that
context isn't lost at chunk boundaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


@dataclass
class RawChunk:
    text: str
    source: str
    heading: str


def _split_by_heading(text: str) -> list[tuple[str, str]]:
    """Return (heading, body) sections. Text before the first heading -> ''."""
    sections: list[tuple[str, str]] = []
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("", text)]

    if matches[0].start() > 0:
        sections.append(("", text[: matches[0].start()]))

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((heading, text[start:end]))
    return sections


def _pack(paragraphs: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if not para:
            continue
        if len(current) + len(para) + 2 <= chunk_size or not current:
            current = f"{current}\n\n{para}".strip()
        else:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{para}".strip()
    if current:
        chunks.append(current)
    return chunks


def split_markdown(text: str, source: str, chunk_size: int, overlap: int) -> list[RawChunk]:
    out: list[RawChunk] = []
    for heading, body in _split_by_heading(text):
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        for piece in _pack(paragraphs, chunk_size, overlap):
            out.append(RawChunk(text=piece, source=source, heading=heading))
    return out
