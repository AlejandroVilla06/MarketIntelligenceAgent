# Proposal: Next.js 14 Frontend

## Intent

Replace the Streamlit UI (`src/ui/app.py`) with a production-grade Next.js 14 App Router frontend. The backend has 8 REST endpoints with SSE streaming and Supabase JWT auth ready — the frontend needs to consume these APIs with proper auth flow and real-time streaming.

## Scope

### In Scope
- Next.js 14 App Router project in `frontend/` (TypeScript, Tailwind, shadcn/ui)
- Supabase SSR auth integration (login, signup, OAuth callbacks, middleware)
- Chat interface with SSE streaming via fetch + ReadableStream
- Conversation list sidebar (create, switch, delete)
- API client with JWT token management and auto-refresh
- TypeScript types mapped from backend Pydantic models
- Dark/light theme toggle (next-themes)
- Responsive layout (mobile sidebar collapse)

### Out of Scope
- Settings page (separate change: user-settings)
- Right sidebar / tools panel (separate change: right-sidebar)
- Performance optimization / code splitting (separate change: performance-opt)
- Deployment configuration (separate concern)
- E2E tests beyond basic smoke tests
- Conversation persistence to Supabase (backend change needed first)

## Capabilities

### New Capabilities
- `nextjs-frontend`: Chat interface, auth pages, API client, Supabase SSR integration, conversation management, theme toggle
- `chat-streaming-client`: Client-side SSE streaming via fetch + ReadableStream (not EventSource) with JWT auth headers

### Modified Capabilities
None — this change only adds a new frontend consuming existing backend APIs.

## Approach

**Architecture**: Next.js 14 App Router + Supabase SSR + Tailwind + shadcn/ui

**Auth flow**: Supabase SSR SDK directly (NOT via FastAPI `/api/auth/*`). Login/signup and OAuth use Supabase SDK; the resulting JWT is sent as `Authorization: Bearer <token>` to FastAPI endpoints. FastAPI validates with the same `SUPABASE_JWT_SECRET`.

**Streaming**: `fetch()` + `ReadableStream` — `EventSource` CANNOT send custom Authorization headers, which is required since all chat endpoints are JWT-protected.

**State**: Zustand for chat state; Supabase session handles auth state.

**Page structure**: `/login` (public), `/signup` (public), `/auth/callback` (OAuth handler), `/chat` (protected, main view), `/` → redirects to `/chat` or `/login`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/` | New | Entire Next.js project (~40 files) |
| `.env.example` | Modified | Add NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY |
| `src/api/` | None | Already CORS-configured for localhost:3000 |
| `src/ui/app.py` | None | Coexists unchanged |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| EventSource can't send auth headers | Certain | Use fetch + ReadableStream instead |
| SSE connection drops on mobile | Medium | Reconnection logic with exponential backoff in useChat hook |
| App Router server/client component confusion | Medium | Interactive components use "use client", static as server defaults |
| Large dependency count (shadcn/radix) | Low | Tree-shaking eliminates unused code |

## Rollback Plan

Delete `frontend/` directory and revert `.env.example` changes. Streamlit app continues working unchanged — zero risk rollback.

## Dependencies

- Next.js ^14.2, React ^18.3, TypeScript ^5
- @supabase/ssr ^0.5, @supabase/supabase-js ^2
- Tailwind ^3.4, shadcn/ui + Radix primitives
- zustand ^5 (chat state), next-themes ^0.3, react-markdown ^9, lucide-react

## Success Criteria

- [ ] `npm run dev` starts without errors
- [ ] Login page renders, email/password auth works via Supabase
- [ ] Chat page shows conversation list in left sidebar
- [ ] User can type a message and see streaming response token-by-token
- [ ] Markdown renders correctly in assistant messages
- [ ] Theme toggle switches between dark and light
- [ ] Protected routes redirect to /login when unauthenticated
- [ ] OAuth (Google, GitHub) login flow works
- [ ] Responsive on mobile (< 768px)