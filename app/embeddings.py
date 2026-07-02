"""Local embedding model wrapper (sentence-transformers).

Kept behind a tiny interface so the rest of the code never imports the model
directly — handy for swapping in a hosted embedding API later, and for keeping
the heavy import lazy (tests don't pay for it).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import get_settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(get_settings().embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings of shape (len(texts), dim)."""
    if not texts:
        return np.zeros((0, 384), dtype="float32")
    vecs = _model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vecs.astype("float32")


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]
