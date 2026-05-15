# streaming-response Specification

## Purpose

Server-Sent Events (SSE) streaming endpoint that delivers orchestrator responses token-by-token to the frontend. Supports concurrent clients, enforces timeout, and applies backpressure to avoid buffering entire responses.

## Requirements

### Requirement: SSE Stream Format (R1)

The stream SHALL use the Server-Sent Events protocol with structured JSON events.

#### Scenario: Stream delivers tokens as SSE events
- GIVEN a client connects to `GET /api/chat/stream?query=hello`
- AND the orchestrator generates response tokens `["Hi", " there", "!"]`
- WHEN the orchestrator yields tokens
- THEN the stream SHALL emit:
  - `data: {"token": "Hi"}\n\n`
  - `data: {"token": " there"}\n\n`
  - `data: {"token": "!"}\n\n`

#### Scenario: Stream signals completion with done event
- GIVEN a client receives all tokens from `GET /api/chat/stream`
- WHEN the orchestrator finishes generating the response
- THEN a final event SHALL be emitted: `data: {"done": true}\n\n`
- AND the connection SHALL close cleanly

#### Scenario: Stream returns correct content-type
- GIVEN a client connects to `GET /api/chat/stream?query=test`
- WHEN the server sends the response headers
- THEN the `Content-Type` header SHALL be `text/event-stream`
- AND `Cache-Control` SHALL be `no-cache`
- AND `Connection` SHALL be `keep-alive`

#### Scenario: Empty response still emits done
- GIVEN the orchestrator returns zero tokens (edge case: no content)
- WHEN a client connects to `GET /api/chat/stream?query=`
- THEN the stream SHALL emit: `data: {"done": true}\n\n`
- AND close the connection

---

### Requirement: Concurrent Streaming (R2)

The streaming endpoint SHALL handle multiple simultaneous clients without interference.

#### Scenario: Two streams run independently
- GIVEN client A requests `GET /api/chat/stream?query=Tell+me+about+AAPL`
- AND client B requests `GET /api/chat/stream?query=Tell+me+about+TSLA`
- WHEN both streams are active concurrently
- THEN client A SHALL receive only AAPL-related tokens
- AND client B SHALL receive only TSLA-related tokens
- AND the streams SHALL NOT block each other

#### Scenario: Many concurrent clients do not degrade
- GIVEN 10 clients connect simultaneously to `GET /api/chat/stream`
- WHEN all streams are active
- THEN each client SHALL receive its own independent stream
- AND no client's stream SHALL be delayed by another's completion

---

### Requirement: Streaming Timeout (R3)

The stream SHALL enforce an inactivity timeout to prevent hanging connections.

#### Scenario: Stream times out after 120 seconds of inactivity
- GIVEN a client has connected to `GET /api/chat/stream?query=long_query`
- AND the orchestrator produces no tokens for 120 seconds
- WHEN the timeout fires
- THEN the stream SHALL emit: `data: {"error": "timeout"}\n\n`
- AND the connection SHALL be closed

#### Scenario: Active stream does not time out
- GIVEN a client is receiving tokens every 30 seconds from the orchestrator
- AND the total response takes 180 seconds
- WHEN the stream completes
- THEN the timeout SHALL NOT fire
- AND all tokens SHALL be delivered successfully

---

### Requirement: Backpressure (R4)

The streaming endpoint SHALL NOT buffer the entire response before sending.

#### Scenario: Tokens are sent as they become available
- GIVEN the orchestrator takes 3 seconds to generate a 100-token response
- WHEN the orchestrator yields each token
- THEN the first token SHALL arrive at the client within 500ms of connection
- AND tokens SHALL arrive incrementally, NOT all at once after the full response is ready

#### Scenario: Large response does not cause memory pressure
- GIVEN the orchestrator generates a very long response (10,000+ tokens)
- WHEN the stream is active
- THEN the server SHALL NOT accumulate all tokens in memory before sending
- AND the memory footprint SHALL remain proportional to inflight tokens, not total tokens
