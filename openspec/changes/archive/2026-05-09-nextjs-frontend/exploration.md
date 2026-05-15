# Exploration: Next.js 14 Frontend for Market Intelligence Agent

## Current State

The project has a fully functional FastAPI backend at `src/api/` with:
- **Supabase auth**: email/password signup/login, OAuth (Google/GitHub), JWT validation (HS256 local, no network calls), token refresh, profile CRUD
- **SSE streaming**: `GET /api/chat/stream?query=...&conversation_id=...` — sends `data: {"token": "..."}` events, ends with `data: {"done": true}`
- **Conversation CRUD**: in-memory store (will migrate to Supabase later), `POST/GET/DELETE /api/conversations`
- **CORS**: already allows `http://localhost:3000`
- **Config**: `.env` already has `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_CHAT_ENDPOINT` vars

The current Streamlit UI (`src/ui/app.py`) provides a ChatGPT-style interface with sidebar, conversation management, and glassmorphism CSS. It communicates directly with the orchestrator (not via the API). The new Next.js frontend will communicate via the REST/SSE API.

## Affected Areas

- `frontend/` — new directory (entire Next.js project)
- `.env` — already has `next_public_api_url` and `next_public_chat_endpoint` (lines 55-56), may need `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `src/api/app.py` — CORS already configured for `localhost:3000`, no changes needed
- `src/ui/app.py` — untouched, coexists with new frontend

## Approaches

### 1. **Monorepo `frontend/` subdirectory** (Recommended)
- Next.js lives in `frontend/` alongside the Python project
- Shared `.env` (or `frontend/.env.local` for frontend-only vars)
- Single repo, single deploy pipeline
- Pros: Simple, one repo, easy to reference backend types, shared CI/CD
- Cons: Mixed tech stack in one repo, slightly larger repo

### 2. **Separate repository**
- Next.js in its own repo (e.g., `market-intelligence-frontend`)
- Independent versioning and deploy
- Pros: Clean separation, independent deploy cycles
- Cons: Two repos to manage, type drift between frontend/backend, harder to keep API contract in sync

**Recommendation: Option 1 (monorepo `frontend/`)**. The project is a single-developer effort, the backend is stable, and having the Pydantic schemas next to the TypeScript types makes contract alignment trivial.

---

### Auth Strategy: Supabase SSR vs Direct API Calls

#### A. **Supabase SSR package (`@supabase/ssr`)** (Recommended)
- Uses Supabase's official Next.js integration
- Cookies managed automatically (httpOnly, secure, sameSite)
- Server-side session validation in middleware
- Handles OAuth redirect flow natively
- Token refresh automatic via Supabase SDK
- Pros: Official, secure, handles edge cases, middleware-based route protection
- Cons: Slightly more setup, need to understand server/client component split

#### B. **Direct API calls to FastAPI auth endpoints**
- Call `/api/auth/login`, `/api/auth/signup` directly
- Store JWT in localStorage or cookies manually
- Manual token refresh on 401
- Pros: Simpler mental model, uses existing backend endpoints
- Cons: Less secure (localStorage XSS vulnerable), manual refresh logic, reinventing what Supabase SSR already does

**Recommendation: Option A (Supabase SSR)**. Here's the key insight — the backend already uses Supabase for auth. The Next.js frontend should use the SAME Supabase project directly via `@supabase/ssr`. This means:
1. Login/signup happens via Supabase SDK (not via the FastAPI endpoints)
2. Supabase issues the JWT
3. The frontend sends that JWT as `Authorization: Bearer <token>` to the FastAPI backend
4. The backend validates it with `SUPABASE_JWT_SECRET` (already implemented)
5. OAuth redirects go through Supabase → Next.js callback route → sets cookies → redirects to chat

The FastAPI auth endpoints (`/api/auth/signup`, `/api/auth/login`) become fallbacks for non-browser clients (CLI, mobile apps). The Next.js frontend uses Supabase directly.

---

### SSE Streaming on the Client

The backend streams via `GET /api/chat/stream?query=...` with `text/event-stream` content type.

**Client implementation approach:**
```typescript
// Use native EventSource or fetch + ReadableStream
const response = await fetch(`${API_URL}/api/chat/stream?query=${encodeURIComponent(query)}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader!.read();
  if (done) break;
  const text = decoder.decode(value);
  // Parse SSE: "data: {\"token\": \"...\"}\n\n"
  // Accumulate tokens into message state
}
```

**Key detail**: `EventSource` doesn't support custom headers (no `Authorization`). Must use `fetch` with `ReadableStream` instead. This is a well-known limitation.

---

### Component Architecture

```
app/
├── layout.tsx              ← Root layout: ThemeProvider, SupabaseProvider
├── page.tsx                ← Chat page (main view, protected)
├── login/page.tsx          ← Login page (public)
├── signup/page.tsx         ← Signup page (public)
├── settings/page.tsx       ← Settings page (protected, shell)
├── auth/callback/route.ts  ← OAuth callback handler (API route)
├── auth/confirm/route.ts   ← Email confirmation handler
components/
├── ui/                     ← shadcn/ui primitives (Button, Input, ScrollArea, etc.)
├── chat/
│   ├── ChatMessage.tsx     ← Message bubble (user right, assistant left)
│   ├── ChatInput.tsx       ← Input area with send button
│   ├── ChatView.tsx        ← Main chat container (messages + input)
│   └── WelcomeScreen.tsx   ← Empty state with suggestions
├── sidebar/
│   ├── Sidebar.tsx         ← Conversation list + new chat button
│   ├── ConversationItem.tsx ← Single conversation entry
│   └── SidebarToggle.tsx   ← Mobile hamburger toggle
├── settings/
│   └── SettingsShell.tsx   ← Settings page shell (future)
└── providers/
    └── ThemeProvider.tsx   ← next-themes wrapper
lib/
├── supabase/
│   ├── client.ts           ← Browser Supabase client (createBrowserClient)
│   ├── server.ts           ← Server Supabase client (createServerClient)
│   └── middleware.ts       ← Middleware helper for session refresh
├── api.ts                  ← Fetch wrapper with JWT, auto-refresh on 401
├── types.ts                ← TypeScript types matching Pydantic models
└── hooks/
    ├── useChat.ts          ← Chat state management (messages, streaming)
    └── useConversations.ts ← Conversation list management
```

---

### Data Flow

#### Auth Flow (Login)
```
User → Login Page → Supabase SDK signInWithPassword()
  → Supabase returns access_token + refresh_token
  → Next.js sets httpOnly cookies via @supabase/ssr
  → Redirect to / (chat page)
  → Middleware validates session on each request
```

#### Auth Flow (OAuth)
```
User → Login Page → "Continue with Google"
  → Supabase SDK signInWithOAuth({ provider: 'google' })
  → Redirect to Google → Google redirects to /auth/callback
  → /auth/callback/route.ts exchanges code for session
  → Sets cookies → Redirect to /
```

#### Chat Flow (Non-streaming)
```
User types message → POST /api/chat { query, conversation_id }
  → Authorization: Bearer <supabase_jwt>
  → Backend validates JWT, runs orchestrator, returns response
  → Frontend appends both messages to state
```

#### Chat Flow (Streaming)
```
User types message → GET /api/chat/stream?query=...&conversation_id=...
  → Authorization: Bearer <supabase_jwt>
  → Backend streams SSE tokens
  → Frontend accumulates tokens in real-time
  → On {"done": true}, finalize message in state
  → POST to conversations endpoint to persist (if needed)
```

---

### Styling Approach

- **Tailwind CSS** for utility-first styling
- **shadcn/ui** for pre-built accessible components (built on Radix UI)
- **next-themes** for dark/light mode toggle
- **CSS variables** for theme tokens (shadcn default)
- Responsive: mobile-first, sidebar collapses to hamburger on small screens

The current Streamlit glassmorphism aesthetic can be approximated with Tailwind's backdrop-blur and gradient utilities, but the priority is a clean ChatGPT-like interface, not replicating the Streamlit look.

---

## Package Choices

| Package | Purpose | Why |
|---------|---------|-----|
| `next` (14.x) | Framework | App Router, Server Components, SSR |
| `react` + `react-dom` (18.x) | UI library | Required by Next.js |
| `typescript` | Type safety | Catch errors at compile time |
| `tailwindcss` | Styling | Utility-first, fast development |
| `@supabase/ssr` | Auth | Official SSR integration, cookie management |
| `@supabase/supabase-js` | Supabase client | Auth, future DB access |
| `shadcn/ui` + `@radix-ui/*` | Components | Accessible, composable, ChatGPT-like |
| `react-markdown` | Markdown rendering | Agent responses contain markdown |
| `remark-gfm` | GitHub Flavored Markdown | Tables, strikethrough, etc. |
| `react-syntax-highlighter` | Code blocks | Agent responses may contain code |
| `lucide-react` | Icons | Clean, consistent icon set |
| `next-themes` | Dark/light mode | System preference detection, toggle |
| `zustand` | State management | Lightweight, no boilerplate (for chat state) |

---

## Files to Create

### Foundation (Phase 1)
```
frontend/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── .env.local                    ← NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
├── .gitignore
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  ← Redirects to /login or shows chat
│   ├── globals.css               ← Tailwind directives + shadcn theme vars
│   ├── login/
│   │   └── page.tsx
│   ├── signup/
│   │   └── page.tsx
│   ├── auth/
│   │   ├── callback/route.ts     ← OAuth callback
│   │   └── confirm/route.ts      ← Email confirmation
│   └── (chat)/                   ← Route group for chat layout
│       ├── layout.tsx            ← Sidebar + main area
│       └── page.tsx              ← Chat interface
├── components.json               ← shadcn/ui config
├── components/
│   ├── ui/                       ← shadcn/ui generated components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── scroll-area.tsx
│   │   ├── avatar.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── sheet.tsx             ← Mobile sidebar
│   │   └── separator.tsx
│   ├── chat/
│   │   ├── ChatView.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   ├── WelcomeScreen.tsx
│   │   └── MarkdownRenderer.tsx
│   ├── sidebar/
│   │   ├── Sidebar.tsx
│   │   ├── ConversationItem.tsx
│   │   └── SidebarToggle.tsx
│   └── providers/
│       └── ThemeProvider.tsx
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── middleware.ts
│   ├── api.ts
│   ├── types.ts
│   └── utils.ts                  ← cn() helper, etc.
├── hooks/
│   ├── useChat.ts
│   └── useConversations.ts
└── middleware.ts                  ← Supabase session refresh + route protection
```

### Settings Page (Phase 2 — shell only in this change)
```
frontend/app/settings/
└── page.tsx                      ← Account, Appearance, Privacy, Logout (shell)
```

---

## In Scope vs Deferred

### In Scope
- Next.js 14 project setup with App Router + TypeScript + Tailwind
- Supabase SSR auth integration (login, signup, OAuth, middleware protection)
- Chat interface with SSE streaming
- Conversation sidebar (list, create, switch, delete)
- Markdown rendering in messages
- Dark/light theme toggle
- Responsive layout (mobile sidebar collapse)
- API client with JWT auto-refresh
- TypeScript types matching backend Pydantic models

### Deferred
- Settings page full implementation (shell only)
- Right sidebar (agent tools, sources panel) — dedicated change
- Performance tuning (lazy loading, code splitting optimization) — dedicated change
- Deployment pipeline (Vercel config) — dedicated change
- E2E tests (Playwright) — dedicated change
- Conversation persistence to Supabase (backend change needed first)
- User profile editing from frontend

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pages Router vs App Router | **App Router** | Pages Router is deprecated in Next.js 14. App Router is the future. |
| Supabase auth approach | **Direct SDK** (not via FastAPI endpoints) | Same Supabase project, JWT compatible, SSR cookie management built-in |
| State management | **Zustand** | Lightweight, no boilerplate, perfect for chat state. Redux is overkill. |
| SSE client | **fetch + ReadableStream** | `EventSource` doesn't support custom headers (no Auth). fetch is universal. |
| Styling | **Tailwind + shadcn/ui** | Industry standard, ChatGPT-like out of the box, accessible |
| Monorepo vs separate repo | **Monorepo `frontend/`** | Single developer, shared contract, simpler CI/CD |
| Markdown rendering | **react-markdown + remark-gfm + react-syntax-highlighter** | Agent returns markdown with code blocks, tables |

---

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Supabase JWT secret mismatch between frontend SDK and backend validation | Low | Both use same Supabase project — JWTs are compatible by design |
| SSE connection drops on mobile/network switch | Medium | Implement reconnection logic with exponential backoff in `useChat` hook |
| `react-markdown` XSS via agent responses | Low | react-markdown sanitizes by default; `remark-gfm` is safe |
| Next.js 14 App Router learning curve (server vs client components) | Medium | Keep components simple — "use client" for interactive, default for static |
| Conversation state lost on page refresh (in-memory backend) | High | Backend limitation — conversations are in-memory. Accept for now. Will fix when backend migrates to Supabase. |
| CORS issues with SSE streaming | Low | CORS already configured for `localhost:3000`, SSE uses same origin in dev |

---

## Ready for Proposal

**Yes** — the exploration is complete. The backend is fully ready for a Next.js frontend. All auth endpoints, SSE streaming, and conversation CRUD are implemented and documented. The CORS configuration already allows `localhost:3000`. The `.env` already has the required `NEXT_PUBLIC_*` variables.

**What the orchestrator should tell the user:**
1. The backend needs zero changes — it's ready
2. The auth flow uses Supabase SDK directly (not the FastAPI auth endpoints) for the best SSR experience
3. The SSE streaming requires `fetch` + `ReadableStream` (not `EventSource`) because of the Authorization header requirement
4. The `frontend/` directory approach is recommended over a separate repo
5. Streamlit coexists without conflicts — both can run simultaneously
