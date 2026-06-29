"""Graph-based retrieval expansion.

Plain top-k vector search is great at finding chunks that look like the question,
but it misses chunks that are *related* to a good hit without sharing its
wording — the classic multi-hop failure. We build a lightweight chunk graph
where two chunks are linked if they share enough salient terms, then expand the
vector hits with their strongest neighbours before generation.

This is a public, data-free version of the graph retrieval idea I work on at
Ericsson; here it runs on extracted keywords instead of a curated ontology.
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict

from .schemas import Chunk

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{2,}")

_STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "with", "this", "that",
    "from", "have", "has", "was", "were", "they", "them", "their", "what",
    "which", "when", "where", "how", "can", "all", "any", "our", "your", "its",
    "into", "than", "then", "out", "use", "used", "using", "via", "per", "may",
    "will", "shall", "must", "each", "also", "such", "these", "those", "about",
}


def _keywords(text: str) -> set[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    return {t for t in tokens if t not in _STOPWORDS}


def _salient_terms(chunks: list[Chunk], top_n: int = 12) -> list[set[str]]:
    """Pick the most distinctive terms per chunk using a tf-idf weighting."""
    doc_freq: Counter[str] = Counter()
    per_chunk_counts: list[Counter[str]] = []
    for c in chunks:
        counts = Counter(t.lower() for t in _TOKEN_RE.findall(c.text)
                         if t.lower() not in _STOPWORDS)
        per_chunk_counts.append(counts)
        for term in counts:
            doc_freq[term] += 1

    n = max(len(chunks), 1)
    salient: list[set[str]] = []
    for counts in per_chunk_counts:
        scored = {
            term: tf * math.log(n / (1 + doc_freq[term]))
            for term, tf in counts.items()
        }
        top = sorted(scored, key=scored.get, reverse=True)[:top_n]
        salient.append(set(top))
    return salient


class ChunkGraph:
    def __init__(self, edges: dict[int, dict[int, float]] | None = None) -> None:
        self.edges: dict[int, dict[int, float]] = edges or {}

    @classmethod
    def build(cls, chunks: list[Chunk], min_shared: int = 2) -> "ChunkGraph":
        salient = _salient_terms(chunks)
        edges: dict[int, dict[int, float]] = defaultdict(dict)
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                shared = salient[i] & salient[j]
                if len(shared) >= min_shared:
                    union = salient[i] | salient[j]
                    weight = len(shared) / len(union)        # Jaccard
                    edges[i][j] = weight
                    edges[j][i] = weight
        return cls(dict(edges))

    def neighbours(self, node: int, k: int) -> list[int]:
        if node not in self.edges:
            return []
        ranked = sorted(self.edges[node].items(), key=lambda kv: kv[1], reverse=True)
        return [n for n, _ in ranked[:k]]

    def expand(self, seeds: list[int], per_seed: int) -> list[int]:
        """Return seed chunks plus their top neighbours, de-duplicated, seeds first."""
        ordered: list[int] = list(seeds)
        seen = set(seeds)
        for s in seeds:
            for n in self.neighbours(s, per_seed):
                if n not in seen:
                    seen.add(n)
                    ordered.append(n)
        return ordered

    # --- persistence -----------------------------------------------------
    def save(self, index_dir: str) -> None:
        os.makedirs(index_dir, exist_ok=True)
        serialisable = {str(k): v for k, v in self.edges.items()}
        with open(os.path.join(index_dir, "graph.json"), "w", encoding="utf-8") as f:
            json.dump(serialisable, f)

    @classmethod
    def load(cls, index_dir: str) -> "ChunkGraph":
        path = os.path.join(index_dir, "graph.json")
        if not os.path.exists(path):
            return cls({})
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        edges = {int(k): {int(n): w for n, w in v.items()} for k, v in raw.items()}
        return cls(edges)
