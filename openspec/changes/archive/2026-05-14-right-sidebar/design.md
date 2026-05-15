# Design: Right Sidebar with Conversation History

## Technical Approach

Add `ConversationHistory` as third column following existing base-ui patterns. Desktop: `<aside>` at `lg+`. Mobile: `Sheet` popup triggered by clock icon in `Header`. Content extracted into `ConversationHistoryContent` (mirrors `SidebarContent` pattern) for reuse across desktop aside and mobile popup. Backend `list()` gains offset/limit via Supabase `.range()`.

## Architecture Decisions

### Self-contained component with shared Sheet Root

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Sheet Root at page level | Trigger in Header, Popup in ConversationHistory — shared context via base-ui Dialog context | ✅ |
| Floating trigger (like Sidebar) | Clock button overlaps Header's ThemeToggle/avatar at `top-3 right-3` | ❌ |
| Modify Sidebar visibility props | Invasive, breaks encapsulation | ❌ |

**Choice**: Page wraps layout in `<Sheet>` (base-ui context provider). Header renders `<SheetTrigger render={<Button><Clock />} />` with `lg:hidden`. `ConversationHistory` renders `<SheetPortal><SheetPopup>`. base-ui Dialog uses React context — descendants anywhere under Root consume it.

### Extract ConversationHistoryContent

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Shared content component | Single source of truth, mirrors `SidebarContent` | ✅ |
| Duplicate JSX | Diverges over time | ❌ |

### Backend pagination

| Option | Tradeoff | Decision |
|--------|----------|----------|
| offset/limit query params | Scope expansion vs proposal, required for lazy load | ✅ |
| Load all, slice client-side | No backend change, breaks at scale | ❌ |

Add `offset: int = Query(0, ge=0)`, `limit: int = Query(20, ge=1, le=100)` to `GET /api/conversations`. Uses Supabase `.range(offset, offset + limit - 1)`.

### Date grouping

Manual day-difference calculation (`diffDays === 0 → "Hoy"`, `=== 1 → "Ayer"`, `≤ 7 → "Esta semana"`, else `"Anteriores"`). Deterministic, no locale dependency.

## Data Flow

```
Page Mount → api.conversations.list(0, 20) → setConversations → grouped render
Scroll end → IntersectionObserver → list(20, 20) → appendConversations → append groups
Search input → debounce 300ms → useMemo filter by title → re-render
Click conv → handleSelectConversation(id) → close mobile sheet
Click clock → Sheet Root open=true → Portal renders Popup
```

## Component Tree

```
page.tsx (state: isRightSidebarOpen)
└── <Sheet>
    └── flex h-screen
        ├── <Sidebar />              (unchanged)
        ├── flex-1 min-w-0           (chat area)
        │   ├── <Header onToggleRightSidebar />
        │   ├── <MessageList />
        │   └── <ChatInput />
        └── <ConversationHistory>    (NEW)
            ├── [desktop] <aside hidden lg:flex w-80 border-l>
            │   └── <ConversationHistoryContent>
            │       ├── <ConversationSearch />
            │       ├── DateGroup[] → <ConversationItem />[]
            │       └── Footer + NewChatButton
            └── [mobile] <SheetPortal> → <SheetPopup side="right">
                └── <ConversationHistoryContent />  (same)
```

## File Changes

| Action | File | Description |
|--------|------|-------------|
| CREATE | `frontend/src/components/ConversationHistory.tsx` | Container: desktop aside + mobile Sheet popup |
| CREATE | `frontend/src/components/ConversationHistoryContent.tsx` | Shared inner: search, grouped list, footer |
| CREATE | `frontend/src/components/ConversationItem.tsx` | Row: truncated title, count badge, hover-delete |
| CREATE | `frontend/src/components/ConversationSearch.tsx` | Debounced search input |
| MODIFY | `frontend/src/app/chat/page.tsx` | 3-col layout, `<Sheet>` Root, `isRightSidebarOpen` state |
| MODIFY | `frontend/src/components/Header.tsx` | `onToggleRightSidebar` prop, `<SheetTrigger>` clock button |
| MODIFY | `frontend/src/api/routes/conversations.py` | offset/limit query params |
| MODIFY | `frontend/src/stores/chatStore.ts` | `appendConversations()` action |
| MODIFY | `src/api/state.py` | `list(offset, limit)` with `.range()` |
| MODIFY | `frontend/src/lib/api.ts` | `conversations.list()` accepts `offset` and `limit` params |

## Interfaces

```typescript
// NEW
interface ConversationHistoryContentProps {
  conversations: ConversationListItem[]; activeId?: string
  onSelect: (id: string) => void; onNew: () => void
}
// MODIFIED
interface HeaderProps { onToggleRightSidebar?: () => void }
// MODIFIED store
appendConversations: (convs: ConversationListItem[]) => void
```

```python
# state.py
async def list(self, offset: int = 0, limit: int = 20) -> list[dict]:
    # ... .range(offset, offset + limit - 1)

# routes/conversations.py
async def list_conversations(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), ...
):
```

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Python unit | `list()` pagination | pytest + TestClient: assert length ≤ limit |
| Python unit | Date grouping | Extract to `src/utils/dates.py`, test boundaries |
| Visual manual | Responsive layout, Sheet, search, active state | Browser devtools resize + click-through |

No frontend test framework (Jest/Vitest not configured). Frontend is manual QA for this change.

## Migration

Additive. Rollback: delete 4 new files, revert 6 modified.

## Open Questions

- **Scope expansion**: Proposal excluded server-side pagination; AD3 overrides — accepted.
- **base-ui vs shadcn**: Orchestrator samples use shadcn API (`asChild`); adapted to base-ui equivalents (`render` prop).
- **Mutual exclusion**: Specs (R1, modified R6) require opening one mobile Sheet closes the other. Sidebar manages its own Sheet state internally — coordination between left/right Sheets needs either a shared callback or ref-based approach during implementation.
