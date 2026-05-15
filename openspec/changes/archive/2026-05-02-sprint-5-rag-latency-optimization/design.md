# Design: Sprint 5 - RAG Latency Optimization

## Technical Approach

Phase 1 implementa instrumentación de latencia para establecer baseline medible. Phase 2 integra SemanticCache como wrapper de la cadena RAG existente, usando el mismo embedding model (sentence-transformers/all-MiniLM-L6-v2) para buscar similaridad semántica.

La arquitectura sigue el patrón **Cache-Aside**: consulta cache primero, si hay hit retornar inmediatamente, si no ejecutar cadena completa y almacenar resultado.

## Architecture Decisions

### Decision: Cache Layer Location

**Choice**: Cache se integra a nivel de LangChain Chain, no dentro del retriever
**Alternatives considered**: 
- Embed cache dentro de MarketRAGRetriever (rechazado: acopla cache a storage, difìcil testing)
- Cache a nivel de tool individual (rechazado: cada tool crea su propia instancia, cache no compartiría contexto)
**Rationale**: LangChain Chain es el punto donde query entra y respuesta sale — ideal para interceptar y cachear la respuesta completa del LLM.

### Decision: Embedding Model Reuse

**Choice**: Usar el mismo embedding model del retriever (all-MiniLM-L6-v2) para cache queries
**Alternatives considered**:
- Embedding diferente para cache (rechazado: overhead de mantener 2 modelos)
- No usar embeddings, solo exact match (rechazado: no cumple spec de similaridad semántica)
**Rationale**: El embedding model ya está inicializado en el retriever — reusarlo evita overhead y asegura consistencia en el espacio de búsqueda.

### Decision: Model-Agnostic Cache Key

**Choice**: Cache key incluye (query_vector + model_id + model_params), no solo la query
**Alternatives considered**:
- Solo query como key (rechazado: misma query con temperatura diferente = diferente respuesta)
- Query string + modelo (rechazado: params como temperatura, top_p afectan output)
**Rationale**: El spec requiere considerar parámetros del modelo como parte de la key.

## Data Flow

```
User Query
    │
    ▼
┌─────────────────────────┐
│   Latency Tracker       │  ← Phase 1: instrumenta cada etapa
│   (timing decorators)   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   Semantic Cache        │  ← Phase 2: busca por similaridad
│   (threshold 0.85)      │
└──────────┬──────────────┘
           │
      ┌────┴────┐
      │HIT      │MISS
      ▼         ▼
Return Cache  Execute Chain
              (retriever → prompt → LLM)
                   │
                   ▼
              Store in Cache
              (query_embedding + response + metadata)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/agents/cache/semantic_cache.py` | Create | Core cache implementation con similarity lookup |
| `src/agents/cache/latency_tracker.py` | Create | Decoradores y utilities para medir latencia |
| `src/agents/cache/models.py` | Create | Data classes para cache entries y metrics |
| `src/agents/cache/__init__.py` | Create | Module exports |
| `src/agents/chains/market_tools.py` | Modify | Integrar latency tracker en cada tool |
| `src/config.py` | Modify | Agregar settings para cache (ttl, threshold, enabled) |

## Interfaces / Contracts

```python
# src/agents/cache/models.py
from dataclasses import dataclass
from typing import Any
from datetime import datetime

@dataclass
class CacheEntry:
    query_embedding: list[float]
    response: str
    model_id: str
    model_params: dict[str, Any]
    created_at: datetime
    ttl_seconds: int
    collections_accessed: list[str]  # para invalidación

@dataclass
class LatencyMetrics:
    query_id: str
    retrieval_ms: float
    prompt_processing_ms: float
    generation_ms: float
    ttft_ms: float  # Time to First Token
    total_ms: float
    cache_hit: bool
```

```python
# src/agents/cache/semantic_cache.py
from abc import ABC, abstractmethod

class CacheStrategy(ABC):
    """Interface extensible para estrategias de cache."""
    
    @abstractmethod
    def get(self, query_embedding: list[float], model_id: str, model_params: dict) -> str | None:
        ...
    
    @abstractmethod
    def set(self, query_embedding: list[float], response: str, model_id: str, model_params: dict) -> None:
        ...

class SemanticCache:
    """Cache con lookup por similaridad semántica."""
    
    SIMILARITY_THRESHOLD: float = 0.85
    
    def __init__(self, strategy: CacheStrategy):
        self._strategy = strategy
        self._embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

```python
# src/agents/cache/latency_tracker.py
from functools import wraps
import time

def track_latency(component: str):
    """Decorador para instrumentar métodos con tracking de latencia."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            # Store metric en thread-local o passed context
            return result
        return wrapper
    return decorator
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | SemanticCache similarity lookup, CacheEntry serialization | pytest con fixtures de embeddings |
| Unit | LatencyTracker timing accuracy | Mock time, verificar cálculos |
| Integration | Cache hit/miss con ChromaDB real | Integration tests con data real |
| Integration | Latency metrics collection | Verificar que metrics se graben |
| E2E | End-to-end latency reduction | Benchmark script comparando con/sin cache |

## Migration / Rollout

No migration required. La implementación es additive — el cache es opt-in via settings.

**Feature flags en config**:
- `cache.enabled`: Boolean para habilitar/deshabilitar cache
- `cache.ttl_seconds`: TTL por defecto (sugerido: 3600 = 1 hora)
- `cache.similarity_threshold`: Threshold para cache hit (default: 0.85)
- `latency_tracking.enabled`: Boolean para instrumentación

**Rollout**:
1. Deploy Phase 1 (latency tracking) primero — sin cambios funcionales, solo métricas
2. Observar baseline por 24-48h
3. Deploy Phase 2 (cache) con cache deshabilitado inicialmente
4. Habilitar cache gradualmente, monitorear hit rate

## Open Questions

- [ ] ¿ChromaDB como storage del cache o SQLite simple? ChromaDB permite queries de similaridad nativas pero overhead mayor. SQLite con cosine similarity manual es más liviano.
- [ ] ¿Invalidación por collection es necesaria ahora o puede ser V2? Por ahora implementar invalidación manual por endpoint, automático por TTL.
- [ ] ¿El cache debe ser compartido entre múltiples instancias del agente? Por ahora singleton local — distributed cache queda para V2.