# Design: FastAPI Backend (infra-api)

## Technical Approach

Create `src/api/` package wrapping the sync `MarketOrchestrator` behind FastAPI. Lifespan-managed singleton, `asyncio.to_thread()` bridge for all sync calls, in-memory conversation store. Zero changes to Streamlit codebase.

## Architecture Decisions

| ID | Decision | Choice | Alternatives Rejected | Rationale |
|----|----------|--------|----------------------|-----------|
| DD1 | Orchestrator lifecycle | Module-level singleton initialized in FastAPI `lifespan` | Per-request init (~5-15s overhead), lazy init (latency on first request) | ChromaDB `PersistentClient` supports multithreaded reads; LLM is stateless; one-time setup amortized |
| DD2 | Sync-to-async bridge | `asyncio.to_thread()` for all orchestrator calls | Rewrite agents to async (disruptive), `run_in_executor` raw (same thing, more verbose) | Zero agent changes; default thread pool handles I/O-bound LLM calls efficiently; minimal overhead |
| DD3 | Conversation state | In-memory `dict[str, list[dict]]` keyed by UUID, LRU eviction, max 1000 | Supabase (future change), Redis (overkill for MVP) | Zero dependencies; trivial to migrate persistence layer later; documented limitation: data lost on restart |
| DD4 | Externalized memory | Add optional `history: list[dict] \| None` to `orchestrator.ask()`; when provided, inject into agent's `ConversationMemory` before `run()`, restore after | Modify agent to accept history param directly (touches more code), separate prompt-building path (duplication) | API manages state externally; Streamlit continues using internal memory; single injection point |
| DD5 | SSE streaming | Phase 1: run full `ask()` in thread, yield result token-by-token from API layer | True LLM streaming via LangChain callbacks (requires query_agent refactor) | Deferred to performance optimization change; SSE contract works, just delayed first token; documented known limitation |
| DD6 | Cache thread safety | `asyncio.Lock` on cache write operations only | Global lock on all cache ops (unnecessary contention), thread-local caches (memory waste) | Cache reads are 100x more frequent than writes; ChromaDB reads are safe concurrently; lock only write path |
| DD7 | API config | Add to existing `Settings(BaseSettings)`: `api_host`, `api_port`, `cors_origins`, `api_workers`, `api_key` | Separate config file (fragmentation), hardcoded defaults (inflexible) | Single source of truth; Pydantic validation; `.env` overridable; follows existing pattern |
| DD8 | Startup sequence | Config load → CORS middleware → lifespan startup (`await asyncio.to_thread(orch.setup)`) → register routes | Sync startup in `@app.on_event("startup")` (deprecated in FastAPI), lazy init on first request | Lifespan is the modern FastAPI pattern; startup blocks until orchestrator ready; surfacing init errors early |

## Data Flow

**Health check**: `GET /api/health` → `{"status": "ok"}` (no orchestrator needed)

**Chat**: `POST /api/chat` → `to_thread(orchestrator.ask(query, history))` → `ChatResponse`

**Stream**: `GET /api/chat/stream?query=...&id=...` → `to_thread(orchestrator.ask(...))` → yield `data: {chunk}\n\n` → `data: [DONE]\n\n`

**CRUD**: `POST /api/conversations` → `uuid4()` → store `{id: [], title: "..."}` → `GET/DELETE /api/conversations/{id}` → read/delete dict entry

```
Client ──→ FastAPI route ──→ asyncio.to_thread ──→ MarketOrchestrator.ask()
                                                           │
                                              MarketQueryAgent.run()
                                                    │
                                         ChromaDB (reads/writes)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/api/__init__.py` | Create | Package init, exports `create_app` |
| `src/api/app.py` | Create | FastAPI app factory: lifespan, CORS, router includes |
| `src/api/deps.py` | Create | `get_orchestrator()` → singleton, `get_conversations()` → dict |
| `src/api/routes/__init__.py` | Create | Router aggregation |
| `src/api/routes/health.py` | Create | `GET /api/health`, `GET /api/status` |
| `src/api/routes/chat.py` | Create | `POST /api/chat`, `GET /api/chat/stream` (SSE) |
| `src/api/routes/conversations.py` | Create | CRUD: `POST/GET/DELETE /api/conversations` |
| `src/api/schemas/__init__.py` | Create | Schema exports |
| `src/api/schemas/chat.py` | Create | `ChatRequest`, `ChatResponse`, `Conversation`, `ConversationListItem` |
| `src/api/state.py` | Create | Conversation store: `dict[str, list[dict]]` with LRU eviction |
| `src/api/streaming.py` | Create | SSE helper: token-by-token yield |
| `src/config/__init__.py` | Modify | Add `api_host`, `api_port`, `cors_origins`, `api_workers`, `api_key` |
| `src/agents/orchestrator.py` | Modify | Add `history: list[dict] \| None` param to `ask()` |

## Interfaces / Contracts

### Chat schemas
```python
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None
    history: list[dict] | None = None  # [{"role":"user","content":"..."},...]

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

class Conversation(BaseModel):
    id: str
    title: str
    messages: list[dict]
    created_at: datetime
    updated_at: datetime
```

### Orchestrator signature change
```python
# Before:
def ask(self, query: str) -> str:

# After:
def ask(self, query: str, history: list[dict] | None = None) -> str:
```

Implementation: when `history is not None`, populate temp `ConversationMemory` from history list, inject into `self.agent.memory`, call `agent.run(query)`, restore original memory.

## Testing Strategy

| Layer | Tests | Tool | Verify |
|-------|-------|------|--------|
| Unit | `test_health_returns_ok`, `test_chat_*`, `test_conversation_crud`, `test_streaming_endpoint`, `test_orchestrator_singleton`, `test_status_before_init` | `pytest` + `fastapi.testclient.TestClient` | Endpoints, schemas, error codes |
| Unit | `test_chat_with_mock_orch`, `test_chat_without_query` | Mock orchestrator via `TestClient` dependency override | Request validation, response format |
| Integration | `test_chroma_concurrent` | `asyncio.gather()` multiple chat requests | No race conditions on ChromaDB |
| Integration | `test_cors_headers` | `TestClient` with `Origin` header | `Access-Control-*` headers present |
| Unit | `test_ask_with_history_param` | Mock agent, verify memory injection/restoration | DD4 backward compatibility |

**Test infrastructure**: `tests/api/` directory, `conftest.py` with `TestClient` fixture and orchestrator mock override.

## Migration / Rollout

- `history` param on `ask()` is backward-compatible (defaults to `None` → existing behavior)
- No data migration needed (in-memory state)
- Rollback: delete `src/api/`, revert `orchestrator.py` and `config/__init__.py`, remove deps. Streamlit unaffected.

## Open Questions

- None. All decisions resolved in this document.
