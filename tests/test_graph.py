from app.graph import ChunkGraph
from app.schemas import Chunk


def _chunk(i: int, text: str) -> Chunk:
    return Chunk(id=i, text=text, source="s.md", heading="")


def test_graph_links_chunks_that_share_salient_terms():
    chunks = [
        _chunk(0, "The Atlas-7 robot battery lasts nine hours on a charge."),
        _chunk(1, "Charging the Atlas-7 battery takes eighty minutes at the dock."),
        _chunk(2, "Vacation policy grants thirty paid days every calendar year."),
    ]
    graph = ChunkGraph.build(chunks, min_shared=2)
    # 0 and 1 both talk about the Atlas-7 battery -> linked.
    assert 1 in graph.neighbours(0, k=5)
    # The vacation chunk shares nothing salient with the battery chunks.
    assert 2 not in graph.neighbours(0, k=5)


def test_expand_keeps_seeds_first_and_dedupes():
    chunks = [_chunk(i, t) for i, t in enumerate([
        "alpha beta gamma shared terms here",
        "alpha beta gamma shared terms again",
        "completely unrelated content entirely",
    ])]
    graph = ChunkGraph.build(chunks, min_shared=2)
    expanded = graph.expand([0], per_seed=3)
    assert expanded[0] == 0          # seed stays first
    assert len(expanded) == len(set(expanded))
