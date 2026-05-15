# Proposal: FastAPI Backend (infra-api)

## Intent

Enable the migration from Streamlit to Next.js by creating a FastAPI backend that wraps the existing `MarketOrchestrator`. This is the foundational change — future changes will add auth (Supabase) and the Next.js frontend. The API must coexist with the current Streamlit app without breaking it.

## Scope

### In Scope
- FastAPI application with lifespan-managed singleton orchestrator
- REST endpoints: health, status, chat (single + SSE streaming)
- Conversation state management (CRUD) externalized from agent memory
- `asyncio.to_thread()` bridge for sync orchestrator calls
- Optional `history` param on `orchestrator.ask()` for external memory injection
- CORS middleware configured for Next.js origin
- API configuration fields in `src/config/__init__.py` (host, port, CORS origins, workers, API key)
- Pydantic request/response schemas

### Out of Scope
- Authentication/authorization (Supabase — future change)
- Next.js frontend (future change)
- Database-backed persistence (conversations stored in-memory initially)
- Modifying `src/ui/app.py` (Streamlit continues unchanged)
- Load balancing or rate limiting

## Capabilities

### New Capabilities
- **api-backend**: FastAPI app, lifespan, dependency injection, routes, middleware, schemas — the full HTTP layer wrapping the orchestrator
- **streaming-response**: SSE streaming endpoint that yields orchestrator responses token-by-token to the frontend

### Modified Capabilities
- None. No existing specs require requirement-level changes. The `history` param on `ask()` is additive and backward-compatible.

## Approach

Create `src/api/` package with a layered FastAPI app:
- **Lifespan**: initializes `MarketOrchestrator` singleton on startup, tears down on shutdown
- **Routes**: separate routers for `/api/health`, `/api/status`, `/api/chat`, `/api/chat/stream`, `/api/conversations`, `/api/reset`
- **Schemas**: Pydantic models for request/response validation
- **Conversation state**: in-memory dict keyed by UUID, storing message lists — injected into `orchestrator.ask()` via optional `history` param
- **Streaming**: `sse-starlette` for SSE; orchestrator call runs in `asyncio.to_thread()`, yielding chunks via `asyncio.Queue`
- **CORS**: allow configurable origins (default: `http://localhost:3000`)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/api/` | New | FastAPI app, routes, schemas, middleware, deps |
| `src/config/__init__.py` | Modified | Add API settings (host, port, CORS, workers, API key) |
| `src/agents/orchestrator.py` | Modified | Add optional `history: list[dict]` param to `ask()` |
| `.env` / `.env.example` | Modified | Add `API_HOST`, `API_PORT`, `CORS_ORIGINS` |
| `requirements.txt` | Modified | Add `fastapi`, `uvicorn[standard]`, `sse-starlette`, `httpx` |
| `src/ui/app.py` | Unchanged | Streamlit continues working as-is |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Sync orchestrator blocks async event loop | Medium | `asyncio.to_thread()` wrapper for all sync calls |
| ChromaDB concurrent access from Streamlit + API | Low | Singleton orchestrator per process; Streamlit runs separately |
| SSE connection drops on long queries | Medium | Timeout config + reconnection guidance in API docs |
| In-memory conversation state lost on restart | High | Documented as known limitation; persistence deferred to auth change |

## Rollback Plan

1. Remove `src/api/` package
2. Revert `src/config/__init__.py` and `src/agents/orchestrator.py` changes
3. Remove added dependencies from `requirements.txt`
4. Streamlit app continues working — zero blast radius since nothing in `src/ui/` changed

## Dependencies

- `fastapi` >= 0.100
- `uvicorn[standard]` >= 0.23
- `sse-starlette` >= 1.6
- `httpx` (for async test client)
- Python 3.11+ (already required)

## Success Criteria

- [ ] `GET /api/health` returns 200 within 50ms
- [ ] `POST /api/chat` accepts a query and returns an answer
- [ ] `GET /api/chat/stream` yields SSE events with answer chunks
- [ ] `POST /api/conversations` creates a conversation; `GET /api/conversations/{id}` retrieves it
- [ ] Orchestrator `ask(query)` still works without `history` (backward compatible)
- [ ] `asyncio.to_thread()` prevents event loop blocking during orchestrator calls
- [ ] Streamlit app runs unchanged alongside the API
- [ ] All API endpoints have Pydantic request/response schemas