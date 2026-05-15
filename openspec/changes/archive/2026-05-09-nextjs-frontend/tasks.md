# Tasks: Next.js 14 Frontend

## Phase 1: Foundation

- [ ] 1.1 Run `npx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir=false`
- [ ] 1.2 Install deps: `@supabase/ssr`, `@supabase/supabase-js`, `zustand`, `next-themes`, `react-markdown`, `remark-gfm`, `lucide-react`
- [ ] 1.3 Create `frontend/.env.local` with `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`
- [ ] 1.4 Create `frontend/lib/types.ts` — TypeScript interfaces for `ChatRequest`, `ChatResponse`, `Message`, `Conversation`, `ConversationListItem`
- [ ] 1.5 Create `frontend/lib/supabase/client.ts` — `createBrowserClient()` for client components
- [ ] 1.6 Create `frontend/lib/supabase/server.ts` — `createServerClient()` for server components
- [ ] 1.7 Create `frontend/lib/supabase/middleware.ts` — `createServerClient()` with cookie session refresh
- [ ] 1.8 Create `frontend/middleware.ts` — redirect unauthenticated from `/chat` to `/login`

## Phase 2: Auth Pages

- [ ] 2.1 Create `frontend/app/layout.tsx` — root layout with SupabaseProvider + ThemeProvider
- [ ] 2.2 Create `frontend/components/Providers.tsx` — "use client" wrapper composing all providers
- [ ] 2.3 Create `frontend/app/page.tsx` — redirect authenticated → `/chat`, unauthenticated → `/login`
- [ ] 2.4 Create `frontend/app/login/page.tsx` — email/password form + Google/GitHub OAuth buttons
- [ ] 2.5 Create `frontend/app/signup/page.tsx` — registration form, redirect to `/login` on success
- [ ] 2.6 Create `frontend/app/auth/callback/route.ts` — OAuth code exchange, set session, redirect to `/chat`

## Phase 3: API Client & State

- [ ] 3.1 Create `frontend/lib/api.ts` — typed fetch wrapper injecting `Authorization: Bearer <jwt>`, handling 401 → logout
- [ ] 3.2 Create `frontend/stores/authStore.ts` — Zustand store: session, user, signIn, signOut, isLoading
- [ ] 3.3 Create `frontend/stores/chatStore.ts` — Zustand store: conversations, messages, streaming flag, addMessage, appendToken

## Phase 4: Chat UI

- [ ] 4.1 Create `frontend/app/chat/page.tsx` — protected page: Sidebar + MessageList + ChatInput + Header
- [ ] 4.2 Create `frontend/hooks/useChat.ts` — SSE via `fetch()` + `ReadableStream`, token accumulation, reconnect (max 3, exponential backoff)
- [ ] 4.3 Create `frontend/hooks/useConversations.ts` — CRUD for `/api/conversations` with JWT header
- [ ] 4.4 Create `frontend/components/ChatInput.tsx` — auto-resize textarea, Enter to send, Shift+Enter newline
- [ ] 4.5 Create `frontend/components/ChatMessage.tsx` — role-based bubble with `react-markdown` + `remark-gfm`
- [ ] 4.6 Create `frontend/components/MessageList.tsx` — scrollable container, auto-scroll to bottom on new messages

## Phase 5: Sidebar & Navigation

- [ ] 5.1 Create `frontend/components/Sidebar.tsx` — conversation list, new chat button, delete on hover, collapsible on mobile
- [ ] 5.2 Create `frontend/components/Header.tsx` — top bar with sidebar toggle, app title, ThemeToggle, UserMenu
- [ ] 5.3 Create `frontend/components/ThemeToggle.tsx` — dark/light switch via `next-themes`
- [ ] 5.4 Create `frontend/components/UserMenu.tsx` — avatar dropdown with settings link and logout

## Phase 6: shadcn/ui Components

- [ ] 6.1 Run `npx shadcn@latest init` in `frontend/` with default style, zinc base color
- [ ] 6.2 Add shadcn components: `button`, `input`, `card`, `dialog`, `dropdown-menu`, `sheet`

## Phase 7: Integration & Verification

- [ ] 7.1 Wire auth flow: login/signup → redirect `/chat`; `/chat` unauthenticated → `/login`
- [ ] 7.2 Wire sidebar → chat: click conversation loads messages; "New Chat" clears chat
- [ ] 7.3 Wire chat input → SSE: send message, tokens appear incrementally, `{"done":true}` finalizes
- [ ] 7.4 Add responsive styles: mobile sidebar Sheet, input visibility with keyboard, hamburger toggle
- [ ] 7.5 Smoke test end-to-end: login → chat → stream → sidebar → logout; verify spec scenarios R1–R9
