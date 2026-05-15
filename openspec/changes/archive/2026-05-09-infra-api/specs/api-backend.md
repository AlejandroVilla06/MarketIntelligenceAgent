# api-backend Specification

## Purpose

HTTP API layer that wraps the existing `MarketOrchestrator` behind a FastAPI application, exposing health checks, chat (single + streaming), conversation CRUD, and reset operations. Coexists with the Streamlit app without modifying it.

## Requirements

### Requirement: FastAPI Application (R1)

The system SHALL create a FastAPI application at `src/api/app.py` with lifespan-managed orchestrator initialization and CORS middleware.

The application SHALL use FastAPI's lifespan context to initialize `MarketOrchestrator` on startup and clean up on shutdown.

CORS middleware SHALL allow configurable origins. Default origin SHALL be `http://localhost:3000`.

#### Scenario: Application starts and initializes orchestrator
- GIVEN the `API_HOST` and `API_PORT` are configured
- WHEN the FastAPI application starts (e.g. via `uvicorn src.api.app:app`)
- THEN the lifespan startup handler SHALL create and configure a `MarketOrchestrator` instance
- AND the orchestrator SHALL be available as a dependency for all route handlers

#### Scenario: Application shuts down and cleans up orchestrator
- GIVEN the FastAPI application is running with an initialized orchestrator
- WHEN the application receives a shutdown signal
- THEN the lifespan shutdown handler SHALL clean up orchestrator resources
- AND ChromaDB connections SHALL be closed

#### Scenario: CORS allows configured origin
- GIVEN CORS origins are configured as `http://localhost:3000`
- WHEN a request with `Origin: http://localhost:3000` hits any endpoint
- THEN the response SHALL include `Access-Control-Allow-Origin: http://localhost:3000`

#### Scenario: CORS blocks unconfigured origin
- GIVEN CORS origins are configured as `http://localhost:3000`
- WHEN a request with `Origin: https://evil.com` hits any endpoint
- THEN the response SHALL NOT include `Access-Control-Allow-Origin`

---

### Requirement: Health Endpoint (R2)

The system SHALL provide a liveness check that does not depend on orchestrator readiness.

#### Scenario: Health check returns ok
- GIVEN the FastAPI server is running (startup may still be in progress)
- WHEN a client sends `GET /api/health`
- THEN the response SHALL be HTTP 200
- AND the body SHALL be `{"status": "ok"}`

#### Scenario: Health check is fast
- GIVEN the server is running
- WHEN a client sends `GET /api/health`
- THEN the endpoint SHALL respond within 50ms
- AND SHALL NOT invoke any orchestrator method

---

### Requirement: Status Endpoint (R3)

The system SHALL expose orchestrator initialization state and document counts.

#### Scenario: Status when orchestrator is ready
- GIVEN the orchestrator has been initialized with documents indexed
- WHEN a client sends `GET /api/status`
- THEN the response SHALL be HTTP 200
- AND the body SHALL include `is_setup: true`, `retriever_initialized: true`, `agent_initialized: true`
- AND the body SHALL include `counts` with document counts per collection

#### Scenario: Status when orchestrator is not yet ready
- GIVEN the orchestrator has NOT completed initialization (startup in progress)
- WHEN a client sends `GET /api/status`
- THEN the response SHALL be HTTP 503
- AND the body SHALL include `is_setup: false`
- AND a `detail` field SHALL explain the not-ready state

---

### Requirement: Chat Endpoint (R4)

The system SHALL accept queries and return orchestrator responses, creating or reusing conversations.

#### Scenario: Chat with a new query (no conversation_id)
- GIVEN the orchestrator is initialized
- WHEN a client sends `POST /api/chat` with body `{"query": "What is AAPL price?"}`
- THEN the system SHALL create a new conversation with a UUID
- THEN the system SHALL call `orchestrator.ask()` via `asyncio.to_thread()`
- THEN the response SHALL be HTTP 200 with `response` (string) and `conversation_id` (string)
- AND the query and response SHALL be stored in the conversation history

#### Scenario: Chat continuing an existing conversation
- GIVEN a conversation with ID `abc-123` exists and has prior messages
- WHEN a client sends `POST /api/chat` with body `{"query": "and MSFT?", "conversation_id": "abc-123"}`
- THEN the system SHALL retrieve the conversation and pass its message history to `orchestrator.ask()`
- AND the new message SHALL be appended to the conversation

#### Scenario: Chat with an invalid conversation_id
- GIVEN no conversation exists with ID `nonexistent`
- WHEN a client sends `POST /api/chat` with body `{"query": "hello", "conversation_id": "nonexistent"}`
- THEN the response SHALL be HTTP 404
- AND the body SHALL include `detail: "Conversation not found"`

#### Scenario: Chat with missing query field
- GIVEN the API is running
- WHEN a client sends `POST /api/chat` with body `{}` (no query)
- THEN the response SHALL be HTTP 422 (FastAPI validation error)
- AND the body SHALL describe the missing required field

#### Scenario: Orchestrator fails during chat
- GIVEN the orchestrator is initialized
- WHEN `orchestrator.ask()` raises an exception (e.g. ChromaDB down)
- AND a client sends `POST /api/chat`
- THEN the response SHALL be HTTP 500
- AND the body SHALL include `detail` with the error message
- AND the exception SHALL NOT crash the server

---

### Requirement: Chat Streaming Endpoint (R5)

The system SHALL stream orchestrator responses via Server-Sent Events.

#### Scenario: Stream returns tokens incrementally
- GIVEN the orchestrator is initialized
- WHEN a client sends `GET /api/chat/stream?query=Tell+me+about+TSLA`
- THEN the response content-type SHALL be `text/event-stream`
- AND the response SHALL stream multiple SSE events, each containing a `token` field
- AND a final event SHALL contain `done: true`

#### Scenario: Stream with existing conversation
- GIVEN a conversation with ID `abc-123` exists
- WHEN a client sends `GET /api/chat/stream?query=continue&conversation_id=abc-123`
- THEN the conversation history SHALL be passed to the orchestrator
- AND the streamed response SHALL be appended to the conversation

#### Scenario: Stream with missing query parameter
- GIVEN the API is running
- WHEN a client sends `GET /api/chat/stream` (no query param)
- THEN the response SHALL be HTTP 422
- AND the body SHALL describe the missing required parameter

---

### Requirement: Conversation Endpoints (R6)

The system SHALL provide CRUD operations for conversations stored in memory.

#### Scenario: Create a new conversation
- GIVEN the API is running
- WHEN a client sends `POST /api/conversations`
- THEN the response SHALL be HTTP 200
- AND the body SHALL include `id` (UUID string) and `messages` (empty array)

#### Scenario: List all conversations
- GIVEN two conversations exist (one empty, one with 3 messages)
- WHEN a client sends `GET /api/conversations`
- THEN the response SHALL be HTTP 200
- AND the body SHALL be an array with 2 entries
- AND each entry SHALL include `id`, `title`, `message_count`, and `created_at`

#### Scenario: Get a specific conversation
- GIVEN a conversation with ID `abc-123` and 2 messages
- WHEN a client sends `GET /api/conversations/abc-123`
- THEN the response SHALL be HTTP 200
- AND the body SHALL include `id: "abc-123"` and all messages with role/content

#### Scenario: Get a nonexistent conversation
- GIVEN no conversation with ID `nonexistent`
- WHEN a client sends `GET /api/conversations/nonexistent`
- THEN the response SHALL be HTTP 404
- AND the body SHALL include `detail: "Conversation not found"`

#### Scenario: Delete a conversation
- GIVEN a conversation with ID `abc-123` exists
- WHEN a client sends `DELETE /api/conversations/abc-123`
- THEN the response SHALL be HTTP 200
- AND subsequent `GET /api/conversations/abc-123` SHALL return 404

#### Scenario: Delete a nonexistent conversation
- GIVEN no conversation with ID `nonexistent`
- WHEN a client sends `DELETE /api/conversations/nonexistent`
- THEN the response SHALL be HTTP 404

---

### Requirement: Reset Endpoint (R7)

The system SHALL allow resetting the orchestrator (clear ChromaDB and re-index).

#### Scenario: Reset orchestrator
- GIVEN the orchestrator is initialized
- WHEN a client sends `POST /api/reset`
- THEN the orchestrator SHALL clear ChromaDB and re-index documents
- THEN the response SHALL be HTTP 200 with `{"message": "Orchestrator reset successfully"}`
- AND conversation state SHALL be cleared

#### Scenario: Reset when orchestrator is not ready
- GIVEN the orchestrator has NOT completed initialization
- WHEN a client sends `POST /api/reset`
- THEN the response SHALL be HTTP 503
- AND the body SHALL indicate the orchestrator is not ready

---

### Requirement: Error Handling (R8)

All endpoints SHALL return standardized JSON error responses.

#### Scenario: Catch-all for unhandled server errors
- GIVEN the API is running
- WHEN an unhandled exception occurs in any endpoint
- THEN the response SHALL be HTTP 500
- AND the body SHALL be `{"detail": "<error message>"}`

#### Scenario: 405 for wrong HTTP method
- GIVEN the API is running
- WHEN a client sends `POST /api/health` (health only supports GET)
- THEN the response SHALL be HTTP 405
- AND the body SHALL include `detail: "Method Not Allowed"`
