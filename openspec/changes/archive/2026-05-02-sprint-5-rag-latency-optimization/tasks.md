# Tasks: Sprint 5 - RAG Latency Optimization

## Phase 1: Foundation / Models

- [x] 1.1 Create `src/agents/cache/__init__.py` with module exports
- [x] 1.2 Create `src/agents/cache/models.py` with CacheEntry and LatencyMetrics dataclasses
- [x] 1.3 Add cache settings to `src/config.py`: cache_enabled, cache_ttl_seconds (default: 86400 = 24h), cache_similarity_threshold (default: 0.85)

## Phase 2: Core Implementation

### 2.1 Latency Tracking (Phase 1)
- [x] 2.1.1 Create `src/agents/cache/latency_tracker.py` with track_latency decorator
- [x] 2.1.2 Implement LatencyTracker class to aggregate metrics per query
- [x] 2.1.3 Add get_metrics_summary() method for p50/p90/p99 calculation

### 2.2 Semantic Cache (Phase 2)
- [x] 2.2.1 Create `src/agents/cache/chroma_cache_store.py` with ChromaDB-backed cache storage
- [x] 2.2.2 Implement _compute_similarity() using cosine similarity on embeddings
- [x] 2.2.3 Implement is_expired() method checking TTL vs created_at
- [x] 2.2.4 Create `src/agents/cache/semantic_cache.py` with SemanticCache class
- [x] 2.2.5 Implement get() with similarity threshold lookup (0.85 default)
- [x] 2.2.6 Implement set() storing query_embedding + response + metadata

## Phase 3: Integration / Wiring

- [x] 3.1 Modify `src/agents/chains/market_tools.py` to wrap each @tool with latency tracking
- [x] 3.2 Add cache lookup in query_all_tool before calling retriever.query_all()
- [x] 3.3 Add cache store after LLM response in `src/agents/query_agent.py` run() method
- [x] 3.4 Register cache as singleton: get_cache_instance() in __init__.py

## Phase 4: Testing

- [x] 4.1 Write unit tests for CacheEntry serialization/deserialization
- [x] 4.2 Write unit tests for similarity computation (embeddings vs threshold)
- [x] 4.3 Write unit tests for TTL expiration logic
- [x] 4.4 Write integration test: cache hit returns cached response without calling retriever
- [x] 4.5 Write integration test: cache miss executes full chain and stores result
- [x] 4.6 Create benchmark script: measure latency with/without cache enabled

## Phase 5: Cleanup / Documentation

- [x] 5.1 Add docstrings to all public methods in cache module
- [ ] 5.2 Update README with new cache configuration options
- [ ] 5.3 Remove any debug logging added during development