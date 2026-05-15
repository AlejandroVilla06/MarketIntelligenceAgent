# nextjs-frontend Specification

## Purpose

Next.js 14 App Router frontend consuming the Market Intelligence Agent backend: Supabase SSR auth, SSE chat streaming, conversation sidebar, API client with JWT auto-refresh, responsive layout, dark/light theme.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **Project Setup**: Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui in `frontend/`. `npm run dev` starts without errors. |
| R2 | **Auth Pages**: `/login` with email/password + Google/GitHub OAuth buttons. `/signup` with email/password. Errors displayed inline. Success redirects to `/chat`. |
| R3 | **Middleware**: Unauthenticated users redirected from `/chat` to `/login`. Authenticated users redirected from `/login` to `/chat`. Uses Supabase SSR session cookies. |
| R4 | **Chat Interface**: Messages as styled bubbles (user right-aligned, assistant left-aligned with markdown). Input fixed at bottom. Enter sends. |
| R5 | **SSE Streaming**: `fetch()` + `ReadableStream` (NOT EventSource) for Authorization headers. Tokens stream incrementally. Loading indicator until first token arrives. Code blocks syntax-highlighted. |
| R6 | **Conversation Sidebar**: Left sidebar with conversation list (title + delete). Click loads messages. "New Chat" creates conversation. Collapsible on mobile (<768px). |
| R7 | **API Client**: Typed client auto-attaches JWT from Supabase session. Handles 401 via token refresh + retry. Methods: chat stream, conversation CRUD, profile. |
| R8 | **Theme Toggle**: Dark/light toggle via next-themes. Persisted in localStorage. Defaults to dark mode. |
| R9 | **Responsive**: Usable at >=320px. Mobile (<768px): sidebar hidden by default, hamburger toggle. Chat input visible with keyboard open. |

## Scenarios

### R1: Project Setup

- GIVEN `frontend/` Next.js 14 project exists
- WHEN `npm run dev` is executed
- THEN dev server starts on port 3000 without compilation errors

### R2: Authentication Pages

- GIVEN registered user at `/login`
- WHEN valid email and password submitted
- THEN user is redirected to `/chat`

- GIVEN user at `/login`
- WHEN wrong password submitted
- THEN "Invalid credentials" error appears on the form

- GIVEN user at `/login`
- WHEN page renders
- THEN "Continue with Google" and "Continue with GitHub" OAuth buttons are visible

- GIVEN new user at `/signup`
- WHEN valid email and strong password (>=6 chars) submitted
- THEN user is redirected to `/chat`

### R3: Auth Middleware

- GIVEN no valid Supabase session
- WHEN navigating to `/chat`
- THEN redirected to `/login`

- GIVEN valid Supabase session
- WHEN navigating to `/login`
- THEN redirected to `/chat`

### R4: Chat Interface

- GIVEN user at `/chat` types "Hello" and presses Enter
- WHEN message appears
- THEN "Hello" is in a right-aligned bubble; assistant response is left-aligned

- GIVEN assistant response contains `**bold text**` and `- list item`
- WHEN message renders
- THEN markdown is rendered: bold text and bullet list

- GIVEN chat has messages exceeding viewport height
- WHEN user scrolls down
- THEN input bar remains fixed at the bottom

### R5: SSE Streaming

- GIVEN user sends a message
- WHEN backend streams `{"token":"Hi"}` then `{"token":" there"}`
- THEN "Hi" appears, then " there" appends incrementally in real-time

- GIVEN user sends a message
- WHEN stream is connected but no tokens received yet
- THEN a typing/loading indicator is visible in the chat

- GIVEN assistant response includes a fenced code block (```python ...)
- WHEN message renders
- THEN code block shows syntax highlighting

### R6: Conversation Sidebar

- GIVEN sidebar shows conversation "AAPL Analysis"
- WHEN user clicks it
- THEN chat area loads that conversation's messages

- GIVEN user clicks "New Chat" button
- WHEN conversation is created
- THEN sidebar adds a new entry; chat area clears to empty

- GIVEN viewport width < 768px
- WHEN `/chat` page loads
- THEN sidebar is hidden; hamburger menu icon is visible

### R7: API Client

- GIVEN valid Supabase session with access_token
- WHEN API client makes a request to `/api/conversations`
- THEN `Authorization: Bearer <token>` header is present

- GIVEN an API request returns HTTP 401
- WHEN the client intercepts the response
- THEN it calls `/api/auth/refresh`, stores new token, and retries the original request

### R8: Theme Toggle

- GIVEN dark mode is active
- WHEN user clicks the theme toggle
- THEN UI switches to light mode

- GIVEN user selected light mode
- WHEN the page is reloaded
- THEN theme remains light (persisted)

### R9: Responsive Design

- GIVEN viewport < 768px
- WHEN user taps the hamburger icon
- THEN sidebar slides in from the left

- GIVEN mobile user at `/chat` taps the chat input
- WHEN the virtual keyboard opens
- THEN the input field remains visible above the keyboard
