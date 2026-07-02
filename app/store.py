"""A small, dependency-light vector store.

For a knowledge base of a few thousand chunks, an in-memory normalised matrix
with a cosine (dot-product) search is faster to reason about than standing up a
vector DB, and it persists to a single .npz + .json pair. Swap in pgvector or
Chroma when the corpus outgrows memory — the interface is intentionally narrow.
"""
from __future__ import annotations

import json
import os

import numpy as np

from .schemas import Chunk


class VectorStore:
    def __init__(self) -> None:
        self.vectors: np.ndarray | None = None        # (n, dim), L2-normalised
        self.chunks: list[Chunk] = []

    def add(self, vectors: np.ndarray, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        self.vectors = vectors.astype("float32")

    def search(self, query_vec: np.ndarray, k: int) -> list[tuple[int, float]]:
        if self.vectors is None or len(self.chunks) == 0:
            return []
        scores = self.vectors @ query_vec            # cosine, both sides normalised
        k = min(k, len(scores))
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [(int(i), float(scores[i])) for i in top]

    # --- persistence -----------------------------------------------------
    def save(self, index_dir: str) -> None:
        os.makedirs(index_dir, exist_ok=True)
        np.savez(os.path.join(index_dir, "vectors.npz"), vectors=self.vectors)
        with open(os.path.join(index_dir, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in self.chunks], f, ensure_ascii=False)

    @classmethod
    def load(cls, index_dir: str) -> "VectorStore":
        store = cls()
        with np.load(os.path.join(index_dir, "vectors.npz")) as data:
            store.vectors = data["vectors"]
        with open(os.path.join(index_dir, "chunks.json"), encoding="utf-8") as f:
            store.chunks = [Chunk(**c) for c in json.load(f)]
        return store

    @staticmethod
    def exists(index_dir: str) -> bool:
        return os.path.exists(os.path.join(index_dir, "vectors.npz"))
