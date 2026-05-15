# Design: Next.js 14 Frontend

## Technical Approach

Next.js 14 App Router monorepo in `frontend/` consuming the existing FastAPI backend via REST + SSE. Auth through Supabase SSR SDK directly (not FastAPI auth endpoints), sending the same JWT as `Authorization: Bearer` to protected routes. Streaming uses `fetch()` + `ReadableStream` because `EventSource` cannot send custom headers. State managed with Zustand, UI built with Tailwind + shadcn/ui. Streamlit coexists unchanged.

## Architecture Decisions

| Decision | Choice | Rejected | Rationale |
|----------|--------|----------|-----------|
| **Auth** | `@supabase/ssr` direct | Proxy through FastAPI `/api/auth/*` | Same JWT secret — SSR handles cookies, middleware, token refresh natively. FastAPI endpoints remain for non-browser clients. |
| **SSE streaming** | `fetch()` + `ReadableStream` | `EventSource` | `EventSource` API has no `headers` parameter — cannot send `Authorization`. |
| **State** | Zustand | Redux, React Context | <1KB, TypeScript-native, works with RSC. Redux is overkill for ~2 stores. |
| **Styling** | Tailwind + shadcn/ui | CSS modules, MUI | shadcn/ui is copy-paste (not a package), accessible, ChatGPT-like aesthetic. |
| **Markdown** | react-markdown + remark-gfm | Custom parser | Agent responses contain tables, code blocks — GFM support is required. |
| **Project location** | Monorepo `frontend/` | Separate repo | Shared `.env`, close to Pydantic models for type alignment, single CI/CD. |

## Data Flow

**Auth flow:**
```
Login page ──→ supabase.auth.signInWithPassword() ──→ Supabase
     ←── session cookies set by @supabase/ssr ──┘
Middleware reads cookies → isAuthenticated → /chat
Chat page → session.access_token → API client → Authorization header
```

**Chat streaming flow:**
```
ChatInput → useChat.send(message)
  ├─→ Add user message to Zustand store (immediate UI)
  ├─→ POST /api/conversations (if new conv)
  └─→ GET /api/chat/stream?query=...&conversation_id=...
       Header: Authorization: Bearer <jwt>
       ←── SSE: {"token": "Hola"} {"token": " mundo"} {"done": true}
       └─→ appendToken() per event → real-time re-render
       └─→ {"done": true} → finalize message in store
```

## File Structure

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Create | Next.js 14, React 18, Supabase SSR, Zustand, Tailwind, shadcn/ui, react-markdown |
| `frontend/app/layout.tsx` | Create | Root layout: SupabaseProvider, ThemeProvider, html/body shell |
| `frontend/app/page.tsx` | Create | Redirect: authenticated → /chat, unauthenticated → /login |
| `frontend/app/login/page.tsx` | Create | Email/password form + OAuth buttons, redirects if authenticated |
| `frontend/app/signup/page.tsx` | Create | Registration form with redirect to /login on success |
| `frontend/app/auth/callback/route.ts` | Create | OAuth code exchange → session → redirect to /chat |
| `frontend/app/chat/page.tsx` | Create | Protected: Sidebar + ChatView, redirect to /login if no session |
| `frontend/components/ChatMessage.tsx` | Create | Role-based bubble: user (right, accent bg), assistant (left, card + markdown) |
| `frontend/components/ChatInput.tsx` | Create | Auto-resize textarea, Enter to send, Shift+Enter for newline |
| `frontend/components/MessageList.tsx` | Create | Virtualized scroll container, auto-scroll to bottom on new messages |
| `frontend/components/Sidebar.tsx` | Create | Conversation list, new chat button, delete on hover, mobile collapse |
| `frontend/components/Header.tsx` | Create | Top bar: sidebar toggle, app title, ThemeToggle, UserMenu |
| `frontend/components/Providers.tsx` | Create | "use client" wrapper composing SupabaseProvider + ThemeProvider |
| `frontend/hooks/useChat.ts` | Create | SSE streaming via fetch + ReadableStream, token accumulation, reconnection |
| `frontend/hooks/useConversations.ts` | Create | CRUD operations on /api/conversations with JWT header |
| `frontend/lib/supabase/client.ts` | Create | `createBrowserClient()` for client components |
| `frontend/lib/supabase/server.ts` | Create | `createServerClient()` for server components/actions |
| `frontend/lib/supabase/middleware.ts` | Create | `createServerClient()` for middleware session refresh |
| `frontend/lib/api.ts` | Create | Fetch wrapper with JWT injection from session, 401 auto-logout |
| `frontend/lib/types.ts` | Create | TypeScript interfaces: ChatRequest, ChatResponse, Message, Conversation, UserProfile |
| `frontend/stores/authStore.ts` | Create | Zustand: session, user, signIn, signOut, isLoading |
| `frontend/stores/chatStore.ts` | Create | Zustand: conversations, messages, streaming flag, addMessage, appendToken |
| `frontend/middleware.ts` | Create | Route protection: /chat → check session → redirect /login if unauthenticated |
| `frontend/.env.local` | Create | NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_KEY, NEXT_PUBLIC_API_URL |
| `.env` | Modify | Add NEXT_PUBLIC_SUPABASE_URL (already present as supabase_url) |

## Interfaces / Contracts

TypeScript types mirroring backend Pydantic schemas from `src/api/schemas/chat.py`:

```typescript
// lib/types.ts
interface ChatRequest { query: string; conversation_id?: string }
interface ChatResponse { response: string; conversation_id: string }
interface Message { role: "user" | "assistant"; content: string; timestamp: string }
interface Conversation { id: string; title: string; messages: Message[]; created_at: string; updated_at: string }
interface ConversationListItem { id: string; title: string; message_count: number; created_at: string }

// lib/api.ts — API surface
const api = {
  chat: (req: ChatRequest): Promise<ChatResponse>              // POST /api/chat
  chatStream: (query: string, convId?: string): Promise<ReadableStream>  // GET /api/chat/stream (returns body)
  listConversations: (): Promise<ConversationListItem[]>       // GET /api/conversations
  createConversation: (): Promise<{ id: string }>              // POST /api/conversations
  getConversation: (id: string): Promise<Conversation>         // GET /api/conversations/:id
  deleteConversation: (id: string): Promise<void>              // DELETE /api/conversations/:id
}
```

All calls inject `Authorization: Bearer <access_token>` from Supabase session. On 401, auto-logout and redirect to `/login`.

## Testing Strategy

| Layer | Scope | Approach |
|-------|-------|----------|
| Manual smoke | Every page | `npm run dev`, verify login/signup/chat/streaming/theme/responsive |
| Component | **Deferred** | Jest + React Testing Library in a future change |
| E2E | **Deferred** | Playwright in a future change |

## Migration / Rollback

No migration — pure addition. Rollback: delete `frontend/`, revert `.env` additions. Streamlit continues working on `localhost:8501` without any interruption.

## Open Questions
- None — all architectural decisions resolved.
