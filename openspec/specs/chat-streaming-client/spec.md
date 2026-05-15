# chat-streaming-client Specification

## Purpose

Client-side SSE streaming utility using `fetch()` + `ReadableStream` (not EventSource) to support JWT-authenticated, token-by-token streaming from the backend chat endpoint.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **Fetch-Based SSE**: The client SHALL use `fetch()` with a POST request, including `Authorization: Bearer <token>`. The response body SHALL be read as a `ReadableStream`. Each SSE `data:` line SHALL be parsed as JSON. |
| R2 | **Token Accumulation**: Each received `{"token":"..."}` SHALL be appended to the current assistant message. The UI SHALL update in real-time. Previously accumulated tokens SHALL NOT be re-rendered. |
| R3 | **Stream Completion**: The stream SHALL end with a `{"done":true}` event. On receipt, the full message SHALL be saved to the conversation and the typing indicator SHALL stop. |
| R4 | **Error Handling**: HTTP 401 SHALL trigger a token refresh and retry. Connection drops SHALL trigger reconnection (max 3 attempts with exponential backoff). Network and timeout errors SHALL display user-facing error messages. |

## Scenarios

### R1: Fetch-Based SSE

- GIVEN a POST request to `/api/chat/stream` with `Authorization: Bearer <token>`
- WHEN `response.body.getReader()` reads the SSE stream
- THEN each `data: {"token": "..."}\n\n` line is parsed as a valid JSON object

- GIVEN a valid Supabase JWT in the session
- WHEN the SSE fetch request is constructed
- THEN the `Authorization: Bearer <token>` header is included in the request

### R2: Token Accumulation

- GIVEN the stream emits tokens `["The ", "stock ", "price"]`
- WHEN each token is received and parsed
- THEN the message state accumulates sequentially: "The " → "The stock " → "The stock price"

- GIVEN token " there" arrives after previous tokens were rendered
- WHEN the UI updates
- THEN only " there" is appended; previously rendered tokens are not re-rendered

### R3: Stream Completion

- GIVEN the stream emits `{"done": true}` as its final event
- WHEN the client receives this event
- THEN the full accumulated message is saved to the conversation
- AND the typing indicator is removed
- AND the stream connection is closed

### R4: Error Handling

- GIVEN the SSE fetch returns HTTP 401 (expired token)
- WHEN the client detects the 401 response
- THEN it SHALL call the token refresh endpoint, store the new token, and retry the stream request once

- GIVEN the SSE connection drops mid-stream (network interruption)
- WHEN the client detects the disconnection
- THEN it SHALL attempt reconnection up to 3 times with exponential backoff

- GIVEN the network is unavailable
- WHEN the SSE fetch is attempted
- THEN "Connection error. Please check your network." SHALL be displayed to the user

- GIVEN no tokens are received for the configured timeout duration (e.g. 120 seconds)
- WHEN the timeout fires
- THEN "Response timed out. Please try again." SHALL be displayed to the user
