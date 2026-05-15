# Delta for api-backend

## Purpose

Delta specification describing how the existing API backend is modified to integrate Supabase authentication. All existing endpoints except `/api/health` and `/api/auth/*` now require a valid Bearer token. The FastAPI lifespan gains Supabase client initialization, and a new `get_current_user` dependency is introduced for per-route protection.

## MODIFIED Requirements

### Requirement: FastAPI Application (R1)

(Previously: Lifespan only initialized `MarketOrchestrator`. No auth router registered.)

The system SHALL create a FastAPI application at `src/api/app.py` with lifespan-managed orchestrator and Supabase client initialization, CORS middleware, and registered chat, conversation, and auth routers.

The lifespan SHALL initialize `MarketOrchestrator` AND the Supabase client singleton on startup. On shutdown, orchestrator resources and ChromaDB connections SHALL be closed, and the Supabase client SHALL be gracefully released.

CORS middleware SHALL allow configurable origins. Default origin SHALL be `http://localhost:3000`.

The application SHALL register an auth router at prefix `/api/auth` with tag `auth`.

#### Scenario: Application starts and initializes orchestrator and Supabase client

- GIVEN `API_HOST`, `API_PORT`, `SUPABASE_URL`, and `SUPABASE_KEY` are configured
- WHEN the FastAPI application starts (e.g. via `uvicorn src.api.app:app`)
- THEN the lifespan startup handler SHALL create and configure a `MarketOrchestrator` instance
- AND the lifespan startup handler SHALL create a Supabase client singleton
- AND both SHALL be available as dependencies for route handlers

#### Scenario: Application shuts down and cleans up

- GIVEN the FastAPI application is running
- WHEN the application receives a shutdown signal
- THEN the lifespan shutdown handler SHALL clean up orchestrator resources
- AND ChromaDB connections SHALL be closed
- AND the Supabase client SHALL be gracefully released

#### Scenario: Auth router appears in OpenAPI docs

- GIVEN the application is started
- WHEN OpenAPI docs (`/docs`) are accessed
- THEN endpoints under `/api/auth` (signup, login, oauth, me, logout, refresh) SHALL appear under the `auth` tag

#### Scenario: CORS allows configured origin

- GIVEN CORS origins are configured as `http://localhost:3000`
- WHEN a request with `Origin: http://localhost:3000` hits any endpoint
- THEN the response SHALL include `Access-Control-Allow-Origin: http://localhost:3000`

#### Scenario: CORS blocks unconfigured origin

- GIVEN CORS origins are configured as `http://localhost:3000`
- WHEN a request with `Origin: https://evil.com` hits any endpoint
- THEN the response SHALL NOT include `Access-Control-Allow-Origin`

---

### Requirement: Health Endpoint (R2) — UNCHANGED

`/api/health` remains publicly accessible without authentication. No delta required.

---

### Requirement: Status Endpoint (R3)

(Previously: Open endpoint, no auth required.)

The system SHALL expose orchestrator initialization state and document counts. This endpoint SHALL require a valid Bearer token via `Depends(get_current_user)`.

#### Scenario: Status with valid token when orchestrator is ready

- GIVEN a valid Bearer token and the orchestrator has been initialized
- WHEN a client sends `GET /api/status`
- THEN the response SHALL be HTTP 200
- AND the body SHALL include `is_setup: true`, `retriever_initialized: true`, `agent_initialized: true`
- AND the body SHALL include `counts` with document counts per collection

#### Scenario: Status without valid token

- GIVEN no Authorization header or an invalid token
- WHEN a client sends `GET /api/status`
- THEN the response SHALL be HTTP 401
- AND the body SHALL include `{"detail": "Not authenticated"}`

#### Scenario: Status when orchestrator is not yet ready

- GIVEN a valid Bearer token and the orchestrator has NOT completed initialization
- WHEN a client sends `GET /api/status`
- THEN the response SHALL be HTTP 503
- AND the body SHALL include `is_setup: false`
- AND a `detail` field SHALL explain the not-ready state

---

### Requirement: Chat Endpoint (R4)

(Previously: Open endpoint, no auth required. Conversations were global, not user-scoped.)

POST /api/chat SHALL require a valid Bearer token via `Depends(get_current_user)`. The authenticated `user_id` SHALL be passed to the conversation store for user-scoped operations. The system SHALL create or reuse conversations scoped to the authenticated user. All other behavior (orchestrator invocation, message storage, error handling) remains unchanged.

#### Scenario: Chat without valid token

- GIVEN no Authorization header or an expired/invalid token
- WHEN a client sends `POST /api/chat` with body `{"query": "What is AAPL price?"}`
- THEN the response SHALL be HTTP 401

#### Scenario: Chat with valid token creates a user-scoped conversation

- GIVEN a valid Bearer token for user `abc-123` and the orchestrator is initialized
- WHEN a client sends `POST /api/chat` with body `{"query": "What is AAPL price?"}`
- THEN the system SHALL create a new conversation associated with `user_id: "abc-123"`
- AND the response SHALL be HTTP 200 with `response` and `conversation_id`

#### Scenario: Chat continuing an existing conversation

- GIVEN a valid token and a conversation with ID `conv-1` belonging to user `abc-123`
- WHEN a client sends `POST /api/chat` with body `{"query": "and MSFT?", "conversation_id": "conv-1"}`
- THEN the system SHALL retrieve the conversation and pass its history to `orchestrator.ask()`

#### Scenario: Chat with an invalid conversation_id

- GIVEN a valid token and no conversation exists with ID `nonexistent`
- WHEN a client sends `POST /api/chat` with body `{"query": "hello", "conversation_id": "nonexistent"}`
- THEN the response SHALL be HTTP 404

#### Scenario: Chat with missing query field

- GIVEN a valid token
- WHEN a client sends `POST /api/chat` with body `{}` (no query)
- THEN the response SHALL be HTTP 422

#### Scenario: Orchestrator fails during chat

- GIVEN a valid token and `orchestrator.ask()` raises an exception
- WHEN a client sends `POST /api/chat`
- THEN the response SHALL be HTTP 500 with an error detail

---

### Requirement: Chat Streaming Endpoint (R5)

(Previously: Open endpoint, no auth required.)

GET /api/chat/stream SHALL require a valid Bearer token via `Depends(get_current_user)`. Conversation context SHALL be scoped to the authenticated user. Streaming behavior (SSE, token-by-token, final `done: true`) remains unchanged.

#### Scenario: Stream without valid token

- GIVEN no Authorization header
- WHEN a client sends `GET /api/chat/stream?query=Tell+me+about+TSLA`
- THEN the response SHALL be HTTP 401

#### Scenario: Stream with valid token returns tokens incrementally

- GIVEN a valid Bearer token and the orchestrator is initialized
- WHEN a client sends `GET /api/chat/stream?query=Tell+me+about+TSLA`
- THEN the response content-type SHALL be `text/event-stream`
- AND SSE events SHALL stream tokens with a final `done: true` event

#### Scenario: Stream with existing user conversation

- GIVEN a valid token and a conversation `conv-1` owned by the authenticated user
- WHEN a client sends `GET /api/chat/stream?query=continue&conversation_id=conv-1`
- THEN the conversation history SHALL be passed to the orchestrator
- AND the streamed response SHALL be appended to the conversation

#### Scenario: Stream with missing query parameter

- GIVEN a valid token
- WHEN a client sends `GET /api/chat/stream` (no query param)
- THEN the response SHALL be HTTP 422

---

### Requirement: Conversation Endpoints (R6)

(Previously: Open endpoints, no auth. Conversations were global — all users shared the same store.)

All conversation endpoints SHALL require a valid Bearer token via `Depends(get_current_user)`. Listing conversations SHALL return only those belonging to the authenticated user. Accessing another user's conversation SHALL return 404. All other CRUD behavior remains unchanged.

#### Scenario: Create a new user-scoped conversation

- GIVEN a valid Bearer token for user `abc-123`
- WHEN a client sends `POST /api/conversations`
- THEN the response SHALL be HTTP 200
- AND the body SHALL include `id` (UUID) and `messages` (empty array)
- AND the conversation SHALL be scoped to `user_id: "abc-123"`

#### Scenario: List returns only authenticated user's conversations

- GIVEN user A has 2 conversations and user B has 3 conversations
- WHEN user A sends `GET /api/conversations` with a valid token
- THEN the response SHALL contain exactly 2 conversations (only user A's)

#### Scenario: Get a specific conversation belonging to the user

- GIVEN a valid token for user `abc-123` and conversation `conv-1` owned by `abc-123`
- WHEN a client sends `GET /api/conversations/conv-1`
- THEN the response SHALL be HTTP 200 with all messages

#### Scenario: Get another user's conversation returns 404

- GIVEN user A's token and conversation `conv-B` owned by user B
- WHEN user A sends `GET /api/conversations/conv-B`
- THEN the response SHALL be HTTP 404

#### Scenario: Conversation endpoints without token

- GIVEN no Authorization header
- WHEN any `/api/conversations` endpoint is called (GET, POST, DELETE)
- THEN the response SHALL be HTTP 401

---

### Requirement: Reset Endpoint (R7)

(Previously: Open endpoint, no auth required.)

POST /api/reset SHALL require a valid Bearer token via `Depends(get_current_user)`.

#### Scenario: Reset without valid token

- GIVEN no Authorization header
- WHEN a client sends `POST /api/reset`
- THEN the response SHALL be HTTP 401

#### Scenario: Reset with valid token

- GIVEN a valid Bearer token and the orchestrator is initialized
- WHEN a client sends `POST /api/reset`
- THEN the orchestrator SHALL clear ChromaDB and re-index documents
- AND the response SHALL be HTTP 200 with `{"message": "Orchestrator reset successfully"}`

#### Scenario: Reset when orchestrator is not ready

- GIVEN a valid Bearer token and the orchestrator has NOT completed initialization
- WHEN a client sends `POST /api/reset`
- THEN the response SHALL be HTTP 503

---

### Requirement: Error Handling (R8)

(Previously: Handled 500 and 405 errors. No authentication errors.)

All endpoints SHALL return standardized JSON error responses. Authentication failures (missing token, invalid signature, expired token) SHALL return HTTP 401 with a descriptive `detail` field.

#### Scenario: Unauthorized access to protected endpoint

- GIVEN any protected endpoint (all except `/api/health` and `/api/auth/*`)
- WHEN accessed without a valid Bearer token
- THEN the response SHALL be HTTP 401
- AND the body SHALL be `{"detail": "<specific reason>"}` (e.g., "Not authenticated", "Token expired", "Invalid token")

#### Scenario: Catch-all for unhandled server errors

- GIVEN the API is running with a valid token
- WHEN an unhandled exception occurs in any endpoint
- THEN the response SHALL be HTTP 500
- AND the body SHALL be `{"detail": "<error message>"}`

#### Scenario: 405 for wrong HTTP method

- GIVEN the API is running
- WHEN a client sends `POST /api/health` (health only supports GET)
- THEN the response SHALL be HTTP 405
- AND the body SHALL include `detail: "Method Not Allowed"`

## ADDED Requirements

### Requirement: Auth Dependency Injection (R9)

The system SHALL provide a `get_current_user()` FastAPI dependency that validates the Bearer token from the `Authorization` header, decodes the JWT locally using `SUPABASE_JWT_SECRET` with HS256, and returns the user's `id` (from `sub` claim) and `email`. Protected routes SHALL inject this via `Depends(get_current_user)`. Unprotected routes (`/api/health`, `/api/auth/*`) SHALL NOT include this dependency.

#### Scenario: Protected route receives authenticated user context

- GIVEN a route handler defined as `async def chat(query: str, user: dict = Depends(get_current_user))`
- WHEN a request with a valid Bearer JWT for user `abc-123` is received
- THEN `user["id"]` SHALL be `"abc-123"`
- AND `user["email"]` SHALL be the email from the JWT claims
- AND the route handler SHALL execute normally

#### Scenario: Health endpoint remains publicly accessible

- GIVEN the `/api/health` route does NOT include `Depends(get_current_user)`
- WHEN a request without Authorization header is received
- THEN the response SHALL be HTTP 200 with `{"status": "ok"}`

#### Scenario: Invalid token is rejected at dependency level

- GIVEN a route with `Depends(get_current_user)`
- WHEN a request with an expired or malformed JWT is received
- THEN the dependency SHALL raise `HTTPException(401)` before the route handler executes
- AND the response SHALL be HTTP 401
