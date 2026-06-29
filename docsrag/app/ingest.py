"""Build the search index from a folder of documents.

Run as a module:  python -m app.ingest
"""
from __future__ import annotations

import os
import sys

from . import embeddings
from .chunking import split_markdown
from .config import get_settings
from .graph import ChunkGraph
from .schemas import Chunk
from .store import VectorStore

SUPPORTED = {".md", ".markdown", ".txt", ".pdf"}


def _read_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _discover(data_dir: str) -> list[str]:
    paths = []
    for root, _, files in os.walk(data_dir):
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() in SUPPORTED:
                paths.append(os.path.join(root, name))
    return paths


def build_index(data_dir: str | None = None, index_dir: str | None = None) -> int:
    settings = get_settings()
    data_dir = data_dir or settings.data_dir
    index_dir = index_dir or settings.index_dir

    paths = _discover(data_dir)
    if not paths:
        raise SystemExit(f"No documents found in {data_dir!r}")

    chunks: list[Chunk] = []
    for path in paths:
        source = os.path.relpath(path, data_dir)
        text = _read_file(path)
        for raw in split_markdown(text, source, settings.chunk_size, settings.chunk_overlap):
            chunks.append(
                Chunk(id=len(chunks), text=raw.text, source=raw.source, heading=raw.heading)
            )

    print(f"Embedding {len(chunks)} chunks from {len(paths)} documents...")
    vectors = embeddings.embed_texts([c.text for c in chunks])

    store = VectorStore()
    store.add(vectors, chunks)
    store.save(index_dir)

    print("Building chunk graph...")
    graph = ChunkGraph.build(chunks)
    graph.save(index_dir)

    edge_count = sum(len(v) for v in graph.edges.values()) // 2
    print(f"Indexed {len(chunks)} chunks · {edge_count} graph edges -> {index_dir}/")
    return len(chunks)


if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else None
    build_index(data_dir=data)
