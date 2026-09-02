"""Embed user questions with the same model used in policy_rag (384 dims)."""

from __future__ import annotations

import os
from functools import lru_cache

# Avoid TensorFlow/Keras import issues on some Python setups
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """Return a 384-dim embedding for similarity search in Supabase."""
    vector = _model().encode(text.strip(), normalize_embeddings=True)
    return vector.tolist()
