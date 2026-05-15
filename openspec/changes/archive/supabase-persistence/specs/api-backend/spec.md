# Delta for api-backend

## MODIFIED Requirements

### Requirement: Chat Endpoint (R4)

POST /api/chat SHALL require a valid Bearer token via `Depends(get_current_user)`. The authenticated `user_id` SHALL be passed to the store for user-scoped operations. The system SHALL persist the user message to Supabase **before** calling the orchestrator. The system SHALL persist the assistant message to Supabase **after** the orchestrator responds. The system SHALL create or reuse conversations scoped to the authenticated user. All other behavior (orchestrator invocation, error handling) remains unchanged.

(Previously: messages were stored in-memory with no explicit persistence-timing contract.)

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

#### Scenario: User message persisted before orchestrator call

- GIVEN a valid token and POST /api/chat with query "AAPL?"
- WHEN the endpoint begins processing
- THEN the user message SHALL be written to Supabase BEFORE `orchestrator.ask()` is invoked

#### Scenario: Assistant message persisted after orchestrator responds

- GIVEN a valid token and the orchestrator returns "AAPL is $150"
- WHEN the orchestrator response completes successfully
- THEN the assistant message SHALL be persisted to Supabase with `role='assistant'`

---

### Requirement: Chat Streaming Endpoint (R5)

GET /api/chat/stream SHALL require a valid Bearer token via `Depends(get_current_user)`. The system SHALL persist the user message to Supabase **before** starting the SSE stream. The system SHALL persist the complete assistant message to Supabase **after** the stream concludes. Conversation context SHALL be scoped to the authenticated user. Streaming behavior (SSE, token-by-token, final `done: true`) remains unchanged.

(Previously: messages were appended in-memory with no explicit persistence timing for streams.)

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

#### Scenario: User message persisted before stream starts

- GIVEN a valid token and GET /api/chat/stream?query=AAPL
- WHEN the endpoint begins processing
- THEN the user message SHALL be persisted to Supabase BEFORE the first SSE event is emitted

#### Scenario: Assistant message persisted after stream completes

- GIVEN a valid token and a streaming response that concludes with `done: true`
- WHEN all tokens have been emitted and the stream closes
- THEN the complete assistant message SHALL be persisted to Supabase

---

### Requirement: Conversation Endpoints (R6)

All conversation endpoints SHALL require a valid Bearer token via `Depends(get_current_user)`. Listing conversations SHALL return only those belonging to the authenticated user. Conversation IDs SHALL be returned as full UUIDs (not truncated). POST /api/conversations SHALL return the full conversation object from the database. Accessing another user's conversation SHALL return 403. All other CRUD behavior remains unchanged.

(Previously: conversation IDs were 8-char truncated; POST returned a lightweight object; cross-user access returned 404.)

#### Scenario: Create a new user-scoped conversation

- GIVEN a valid Bearer token for user `abc-123`
- WHEN a client sends `POST /api/conversations`
- THEN the response SHALL be HTTP 200
- AND the body SHALL include `id` (full UUID), `title`, `user_id`, and all DB fields
- AND the conversation SHALL be scoped to `user_id: "abc-123"`

#### Scenario: List returns only authenticated user's conversations

- GIVEN user A has 2 conversations and user B has 3 conversations
- WHEN user A sends `GET /api/conversations` with a valid token
- THEN the response SHALL contain exactly 2 conversations (only user A's)
- AND each conversation SHALL include its full UUID

#### Scenario: Get a specific conversation belonging to the user

- GIVEN a valid token for user `abc-123` and conversation `conv-1` owned by `abc-123`
- WHEN a client sends `GET /api/conversations/conv-1`
- THEN the response SHALL be HTTP 200 with all messages

#### Scenario: Get another user's conversation returns 403

- GIVEN user A's token and conversation `conv-B` owned by user B
- WHEN user A sends `GET /api/conversations/conv-B`
- THEN the response SHALL be HTTP 403 with a detail indicating forbidden

#### Scenario: Delete another user's conversation returns 403

- GIVEN user A's token and conversation `conv-B` owned by user B
- WHEN user A sends `DELETE /api/conversations/conv-B`
- THEN the response SHALL be HTTP 403 with a detail indicating forbidden

#### Scenario: Conversation endpoints without token

- GIVEN no Authorization header
- WHEN any `/api/conversations` endpoint is called (GET, POST, DELETE)
- THEN the response SHALL be HTTP 401
