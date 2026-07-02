"""The RAG pipeline: retrieve (vector + graph), build a grounded prompt, generate."""
from __future__ import annotations

import time

from . import embeddings, llm
from .config import get_settings
from .graph import ChunkGraph
from .schemas import AskResponse, Chunk, Citation
from .store import VectorStore

SYSTEM_PROMPT = (
    "You answer questions using ONLY the provided context passages. "
    "Be concise and specific. Cite the passages you used with their bracket "
    "numbers, e.g. [1], [2]. If the context does not contain the answer, say "
    "you don't have that information — never invent facts."
)


class RagEngine:
    """Holds the loaded index and answers questions against it."""

    def __init__(self, store: VectorStore, graph: ChunkGraph) -> None:
        self.store = store
        self.graph = graph

    @classmethod
    def load(cls, index_dir: str | None = None) -> "RagEngine":
        index_dir = index_dir or get_settings().index_dir
        return cls(VectorStore.load(index_dir), ChunkGraph.load(index_dir))

    def retrieve(
        self, question: str, top_k: int | None = None, use_graph: bool | None = None
    ) -> list[tuple[Chunk, float]]:
        settings = get_settings()
        top_k = top_k or settings.top_k
        use_graph = settings.use_graph_retrieval if use_graph is None else use_graph

        q_vec = embeddings.embed_query(question)
        hits = self.store.search(q_vec, top_k)
        scores = {idx: score for idx, score in hits}
        ordered = [idx for idx, _ in hits]

        if use_graph and ordered:
            expanded = self.graph.expand(ordered, settings.graph_expansion)
            for idx in expanded:
                scores.setdefault(idx, 0.0)        # neighbours have no vector score
            ordered = expanded

        return [(self.store.chunks[i], scores[i]) for i in ordered]

    def answer(
        self, question: str, top_k: int | None = None, use_graph: bool | None = None
    ) -> AskResponse:
        start = time.perf_counter()
        retrieved = self.retrieve(question, top_k, use_graph)
        contexts = [c for c, _ in retrieved]

        prompt = _build_prompt(question, contexts)
        answer = llm.generate(SYSTEM_PROMPT, prompt)

        citations = [
            Citation(source=c.source, heading=c.heading, score=round(s, 4))
            for c, s in retrieved
        ]
        latency_ms = int((time.perf_counter() - start) * 1000)
        return AskResponse(
            answer=answer, citations=citations, contexts=contexts, latency_ms=latency_ms
        )


def _build_prompt(question: str, contexts: list[Chunk]) -> str:
    blocks = []
    for i, c in enumerate(contexts, start=1):
        blocks.append(f"[{i}] ({c.label()})\n{c.text}")
    context_text = "\n\n".join(blocks) if blocks else "(no context retrieved)"
    return f"Context passages:\n\n{context_text}\n\nQuestion: {question}\n\nAnswer:"
