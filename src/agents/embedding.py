"""
Embedding — Singleton for SentenceTransformer
==============================================

Shared embedding model instance to avoid loading the 80MB model
multiple times across retriever, cache, and cache store.

Usage:
    from src.agents.embedding import get_embedding_model
    model = get_embedding_model()
    embeddings = model.encode(["text"]).tolist()
"""

from __future__ import annotations

import functools

EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
"""Default embedding model for vectorization (~80MB)."""


@functools.lru_cache(maxsize=1)
def get_embedding_model():
    """Load SentenceTransformer once and cache it.
    
    Returns:
        SentenceTransformer instance (cached, ~80MB RAM).
        Same instance across all callers.
    """
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.
    
    Uses the shared singleton model.
    
    Args:
        texts: List of text strings to embed.
    
    Returns:
        List of embedding vectors as Python lists.
    """
    model = get_embedding_model()
    return model.encode(texts).tolist()


__all__ = [
    "get_embedding_model",
    "embed_texts",
    "EMBEDDING_MODEL_NAME",
]
