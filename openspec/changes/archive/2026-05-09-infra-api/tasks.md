# Tasks: FastAPI Backend (infra-api)

## Phase 1: Dependencies & Config

- [x] 1.1 Install `fastapi`, `uvicorn[standard]`, `sse-starlette`, `httpx`
- [ ] 1.2 Add `api_host`, `api_port`, `cors_origins`, `api_workers`, `api_key` to `src/config/__init__.py`
- [ ] 1.3 Add `API_HOST`, `API_PORT`, `CORS_ORIGINS` defaults to `.env`

## Phase 2: Core Infrastructure

- [x] 2.1 Create `src/api/` package with `__init__.py`, `routes/`, `schemas/` subpackages
- [x] 2.2 Create `src/api/schemas/chat.py`: `ChatRequest`, `ChatResponse`, `Conversation`, `ConversationListItem`
- [x] 2.3 Create `src/api/schemas/status.py`: `StatusResponse`
- [x] 2.4 Create `src/api/app.py`: FastAPI factory with lifespan (orchestrator init/teardown) and CORS
- [x] 2.5 Create `src/api/deps.py`: `get_orchestrator()` singleton dependency, `get_conversations()` store dependency
- [x] 2.6 Create `src/api/state.py`: in-memory `dict[str, list[dict]]` conversation store with LRU eviction (max 1000)

## Phase 3: Middleware

- [x] 3.1 Create `src/api/middleware.py`: configure CORS from settings, add request logging middleware

## Phase 4: Routes

- [x] 4.1 Create `src/api/routes/health.py`: `GET /api/health` → `{"status":"ok"}` (R2)
- [x] 4.2 Create `src/api/routes/status.py`: `GET /api/status` → 200 when ready, 503 when not (R3)
- [x] 4.3 Create `src/api/routes/chat.py`: `POST /api/chat` → `asyncio.to_thread(orchestrator.ask)` → `ChatResponse` (R4)
- [x] 4.4 Extend `src/api/routes/chat.py`: `GET /api/chat/stream` → SSE via `sse-starlette`, yield tokens, final `{"done":true}` (R5, streaming-response R1-R4)
- [x] 4.5 Create `src/api/routes/conversations.py`: `POST/GET/DELETE /api/conversations[/{id}]` CRUD (R6)
- [x] 4.6 Wire all routers into `src/api/app.py` under `/api` prefix; include `POST /api/reset` (R7)

## Phase 5: Orchestrator Modification

- [ ] 5.1 Add optional `history: list[dict] | None` param to `orchestrator.ask()` signature
- [ ] 5.2 Implement temp `ConversationMemory` injection when `history` provided, restore original after `agent.run()`
- [ ] 5.3 Verify `ask(query)` without `history` behaves identically (Streamlit backward compat)

## Phase 6: Tests

- [ ] 6.1 `tests/test_api_health.py`: `test_health_returns_ok`, `test_health_latency_under_50ms` (R2)
- [ ] 6.2 `tests/test_api_chat.py`: `test_chat_with_query`, `test_chat_creates_conversation`, `test_chat_404_bad_id`, `test_chat_422_missing_query` (R4)
- [ ] 6.3 `tests/test_api_chat.py`: `test_stream_sse_format`, `test_stream_done_event`, `test_stream_timeout`, `test_stream_concurrent_clients` (R5, streaming-response R1-R4)
- [ ] 6.4 `tests/test_api_conversations.py`: `test_create`, `test_get`, `test_delete`, `test_list`, `test_404_missing` (R6)
- [ ] 6.5 `tests/test_api_integration.py`: `test_orchestrator_singleton_lifespan`, `test_status_before_init_503` (R1, R3)
- [ ] 6.6 `tests/test_api_integration.py`: `test_concurrent_chat_requests`, `test_cors_headers_allowed`, `test_cors_headers_blocked` (R1, R8, streaming-response R2)

## Phase 7: Smoke Test & Docs

- [ ] 7.1 Manual: `uvicorn src.api.app:create_app()` starts without errors
- [ ] 7.2 Manual: `GET /api/health` returns 200 within 50ms
- [ ] 7.3 Manual: `POST /api/chat` returns valid `ChatResponse`
- [ ] 7.4 Manual: Streamlit app (`src/ui/app.py`) runs unchanged alongside API
