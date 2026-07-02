import numpy as np

from app.schemas import Chunk
from app.store import VectorStore


def _chunk(i: int, text: str) -> Chunk:
    return Chunk(id=i, text=text, source="s.md", heading="")


def test_search_ranks_closest_vector_first():
    store = VectorStore()
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]], dtype="float32")
    # normalise the diagonal one
    vectors[2] /= np.linalg.norm(vectors[2])
    store.add(vectors, [_chunk(0, "x-axis"), _chunk(1, "y-axis"), _chunk(2, "diag")])

    hits = store.search(np.array([1.0, 0.0], dtype="float32"), k=2)
    assert hits[0][0] == 0          # exact match ranks first
    assert len(hits) == 2
    assert hits[0][1] >= hits[1][1]  # scores sorted descending


def test_save_and_load_roundtrip(tmp_path):
    store = VectorStore()
    vectors = np.eye(3, dtype="float32")
    store.add(vectors, [_chunk(i, f"c{i}") for i in range(3)])
    store.save(str(tmp_path))

    loaded = VectorStore.load(str(tmp_path))
    assert len(loaded.chunks) == 3
    assert loaded.chunks[1].text == "c1"
    assert np.allclose(loaded.vectors, vectors)
