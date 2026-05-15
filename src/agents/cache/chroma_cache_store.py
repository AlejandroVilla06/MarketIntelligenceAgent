"""
ChromaDB Cache Store - ChromaDB-backed storage for Semantic Cache
===================================================

ChromaDB-backed storage layer for query cache entries.

Usage:
    from src.agents.cache.chroma_cache_store import ChromaCacheStore
    store = ChromaCacheStore()
    store.put(entry)
    entry = store.get_similar(query_embedding, threshold=0.85)
"""

from __future__ import annotations

import time
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError

from src.agents.cache.models import CacheEntry
from src.config import settings


COLLECTION_NAME: str = "semantic_cache"


class ChromaCacheStore:
    """
    ChromaDB-backed store for cache entries.
    
    Stores cache entries with embeddings for similarity lookup.
    
    Usage:
        store = ChromaCacheStore()
        entry = CacheEntry(...)
        store.put(entry)
        
        similar = store.get_similar(embedding, threshold=0.85)
    """
    
    def __init__(
        self,
        persist_directory: str | None = None,
    ) -> None:
        """
        Initialize ChromaDB cache store.
        
        Args:
            persist_directory: ChromaDB persistence directory.
        """
        self.persist_directory = persist_directory or str(settings.chromadb_persist_dir)
        
        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Get or create cache collection
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
        )
        
        # Embedding function (shared singleton)
        from src.agents.embedding import get_embedding_model
        self._embedding_function = get_embedding_model()
    
    def _embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings.
            
        Returns:
            List of embedding vectors.
        """
        return self._embedding_function.encode(texts).tolist()
    
    def _compute_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.
            
        Returns:
            Cosine similarity (0.0 to 1.0).
        """
        import math
        
        # Cosine similarity
        dot = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def put(self, entry: CacheEntry) -> None:
        """
        Store a cache entry.
        
        Args:
            entry: CacheEntry to store.
        """
        # Generate ID from timestamp + query hash
        import hashlib
        
        query_hash = hashlib.md5(entry.query.encode()).hexdigest()[:8]
        entry_id = f"cache_{entry.model_id}_{query_hash}_{int(entry.created_at)}"
        
        # Format document
        document = f"query: {entry.query} | model: {entry.model_id}"
        
        # Metadata (serialize response as JSON)
        import json
        metadata = {
            "query": entry.query,
            "model_id": entry.model_id,
            "model_params": json.dumps(entry.model_params),
            "created_at": entry.created_at,
            "ttl_seconds": entry.ttl_seconds,
            "response": json.dumps(entry.response),
        }
        
        # Add to ChromaDB
        self._collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[entry_id],
            embeddings=[entry.query_embedding],
        )
    
    def get_similar(
        self,
        query_embedding: list[float],
        threshold: float = 0.85,
    ) -> CacheEntry | None:
        """
        Find most similar cache entry.
        
        Args:
            query_embedding: Query embedding vector.
            threshold: Minimum similarity threshold.
            
        Returns:
            Most similar CacheEntry, or None if none above threshold.
        """
        # Query with enough results
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
        )
        
        if not results.get("documents") or not results["documents"][0]:
            return None
        
        import json
        
        best_entry: CacheEntry | None = None
        best_similarity: float = threshold
        
        for i, doc in enumerate(results["documents"][0]):
            # Get embedding
            embeddings = results.get("embeddings")
            if not embeddings or not embeddings[0]:
                continue
            stored_embedding = embeddings[0][i]
            
            # Compute similarity
            similarity = self._compute_similarity(query_embedding, stored_embedding)
            
            if similarity > best_similarity:
                # Get metadata
                metadatas = results.get("metadatas", [[]])
                meta = metadatas[0][i] if metadatas else {}
                
                # Check TTL expiration
                created_at = meta.get("created_at", 0)
                ttl = meta.get("ttl_seconds", 86400)
                if ttl > 0 and (time.time() - created_at) > ttl:
                    continue  # Expired
                
                # Build CacheEntry
                try:
                    response = json.loads(meta.get("response", "{}"))
                    model_params = json.loads(meta.get("model_params", "{}"))
                except json.JSONDecodeError:
                    response = meta.get("response")
                    model_params = {}
                
                best_entry = CacheEntry(
                    query=meta.get("query", ""),
                    query_embedding=stored_embedding,
                    response=response,
                    model_id=meta.get("model_id", ""),
                    model_params=model_params,
                    created_at=created_at,
                    ttl_seconds=ttl,
                )
                best_similarity = similarity
        
        return best_entry
    
    def delete_expired(self) -> int:
        """
        Delete all expired entries.
        
        Returns:
            Number of entries deleted.
        """
        # This is expensive - iterate all and check
        # For production, consider a separate index
        return 0  # Simplified - rely on TTL check in get_similar
    
    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self._client.delete_collection(name=COLLECTION_NAME)
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
            )
        except NotFoundError:
            pass
    
    def __repr__(self) -> str:
        count = self._collection.count()
        return f"ChromaCacheStore(entries={count})"


__all__ = [
    "ChromaCacheStore",
    "COLLECTION_NAME",
]