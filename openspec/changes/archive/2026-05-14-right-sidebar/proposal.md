# Proposal: Right Sidebar with Conversation History

## Intent

Add a responsive right sidebar that presents full conversation history grouped by date (Hoy/Ayer/Esta semana/Anteriores), with client-side search/filter. The current left sidebar provides quick navigation; the right sidebar gives chronological context. This reduces cognitive load when switching conversations and makes historical context discoverable without scrolling a flat list.

## Scope

### In Scope
- `ConversationHistory.tsx` — Right sidebar container with date-grouped list
- `ConversationItem.tsx` — Individual conversation entry with title, date, message count
- `ConversationSearch.tsx` — Client-side search/filter input
- 3-column responsive layout in `chat/page.tsx`
- Header clock-icon toggle for mobile right sidebar
- Responsive breakpoints per exploration table

### Out of Scope
- Changes to `chatStore.ts`, `api.ts`, or `types.ts` (consume existing store/API as-is)
- Server-side search or pagination (client-side filter only)
- Conversation creation/deletion from right sidebar (left sidebar owns those actions)
- Real-time collaborative editing

## Capabilities

### New Capabilities
- `conversation-history-sidebar`: Date-grouped conversation history panel with client-side search, responsive Sheet/fixed layout, and user footer. Consumes `chatStore.conversations` and `api.conversations.list()`.

### Modified Capabilities
- `nextjs-frontend`: Layout changes (3-column), Header gets clock-icon mobile trigger for right sidebar, responsiveness extends beyond current R6/R9.

## Approach

Restructure `chat/page.tsx` from 2-column (`Sidebar | Chat`) to 3-column (`Sidebar | Chat | ConversationHistory`). Desktop: both sidebars visible. Tablet: left sidebar becomes hamburger, right stays. Mobile: both become sheet overlays with distinct triggers (hamburger = left, clock = right). Open one Sheet closes the other. Use shadcn `Sheet` for mobile, Tailwind responsive classes for desktop visibility. Date grouping via `created_at` with `Intl.RelativeTimeFormat`. Visual consistency via `Card`, `Badge`, `Skeleton`, `cn()`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/chat/page.tsx` | Modified | 3-column layout wrapping Sidebar + Chat + ConversationHistory |
| `frontend/src/components/Header.tsx` | Modified | Add clock-icon toggle button, right sidebar open state prop |
| `frontend/src/components/ConversationHistory.tsx` | New | Right sidebar container |
| `frontend/src/components/ConversationItem.tsx` | New | Single conversation row |
| `frontend/src/components/ConversationSearch.tsx` | New | Search input with client-side filter |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Chat too narrow on medium screens | Medium | Hide left sidebar < 1280px, right sidebar < 768px |
| Duplicate conv lists (left + right) | Low | Left = quick nav + actions; Right = history + search — different purpose |
| Two mobile sheets conflict | Medium | Different triggers (hamburger vs clock); opening one closes the other |
| Grouping logic edge cases | Low | Use `Intl.RelativeTimeFormat` with explicit date boundaries |

## Rollback Plan

Remove the 3-column layout, revert `chat/page.tsx` to 2-column, delete `ConversationHistory.tsx`, `ConversationItem.tsx`, `ConversationSearch.tsx`, revert `Header.tsx`. All changes are additive; rollback is pure deletion.

## Dependencies

- Existing `conversation-persistence` API (GET /api/conversations with `created_at` field)
- shadcn/ui `Sheet` component (already installed)
- Tailwind responsive utilities

## Success Criteria

- [ ] Right sidebar renders conversation list from Supabase via `api.conversations.list()`
- [ ] Click conversation loads history into `chatStore`
- [ ] Search/filter works client-side
- [ ] Groups by date (Hoy/Ayer/Esta semana/Anteriores)
- [ ] Responsive: works on mobile (< 768px), tablet (768–1279px), desktop (≥ 1280px)
- [ ] Visual consistency with generative widgets (Card, Badge, Skeleton, cn())
- [ ] Build passes with no type errors