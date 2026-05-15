# Design: Supabase Persistence for Conversations

## Technical Approach

Replace the in-memory `ConversationStore` (dict + LRU, volatile, global scope) with a `SupabaseConversationStore` backed by PostgreSQL via postgrest. Each request gets a fresh store instance scoped to the authenticated `user_id`. All DB calls wrap `asyncio.to_thread()` — extending the pattern already used for `orch.ask()`. No caching layer; single-instance app makes direct DB reads acceptable.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| **Storage backend** | Direct Supabase (no cache) | Write-through cache, Redis | Single worker, no invalidation complexity, RLS provides defense-in-depth |
| **Store lifecycle** | Per-request via Depends | Global singleton | `user_id` scoping requires fresh instance; eliminates shared mutable state |
| **ID format** | Full UUID (from `gen_random_uuid()`) | 8-char truncated | DB generates proper UUIDs; truncation was cosmetic and risks collisions |
| **Async strategy** | `asyncio.to_thread()` for ALL DB calls | Switch to asyncpg | Consistency with existing `orch.ask()` pattern; no new dependencies |
| **RLS for isolation** | DB-enforced (`auth.uid() = user_id`) | App-level filtering | Defense in depth — even buggy app code can't leak data across users |
| **Title generation** | First user message truncated to 42 chars | Separate title field | Preserves existing UX; same logic now in `SupabaseConversationStore.add_message()` |

## Data Flow

### Chat Request (POST /api/chat)

```
Client ──POST──→ FastAPI ──Depends(get_current_user)──→ JWT → {sub, email}
                │
                ├── Depends(get_supabase_client) ──→ Client singleton
                │
                ├── SupabaseConversationStore(client, user["sub"])
                │
                ├── store.get(cid) or store.create()     ←─ DB (via to_thread)
                ├── store.add_message(cid, "user", q)    ←─ DB IMMEDIATE
                ├── orch.ask(q, history)                 ←─ to_thread (sync LLM)
                ├── store.add_message(cid, "assistant")  ←─ DB ON COMPLETE
                │
                └── ChatResponse ──→ Client
```

### Streaming (GET /api/chat/stream)

Same flow but assistant message persisted AFTER the stream completes. On stream error, the user message is already saved but the assistant message is intentionally NOT — avoids partial/corrupt data.

### Cross-Session History (CalculationExecutor)

```
CalculationExecutor.get_recent_history(user_id)
  ├── supabase.table("conversations").eq("user_id")...limit(10)  ←─ to_thread
  └── per conv: supabase.table("messages").eq("conversation_id") ←─ to_thread
```

The LLM prompt template includes historical context when the user asks for comparative or trend analysis.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `sql/002_conversations.sql` | **Create** | Tables, RLS policies, indexes, `updated_at` trigger |
| `sql/init.sql` | Modify | Append `\i 002_conversations.sql` at end |
| `src/api/persistence.py` | **Create** | `SupabaseConversationStore` class with async interface |
| `src/api/state.py` | **Keep** | Retain as fallback behind feature flag |
| `src/api/deps.py` | Modify | New `get_supabase_store(user)` dependency; keep `get_conversations()` for fallback |
| `src/api/routes/conversations.py` | Modify | Swap `ConversationStore` → `SupabaseConversationStore`; user-scoped queries |
| `src/api/routes/chat.py` | Modify | Same swap; stream persists at end; handle `to_thread` properly |
| `src/market_orchestrator/python_repl.py` | Modify | Add `get_recent_history(user_id)` method |
| `tests/conftest.py` | Modify | Mock Supabase table chain for conversations/messages |
| `tests/test_api_conversations.py` | Modify | User isolation tests, DB mock verification |
| `tests/test_api_chat.py` | Modify | Persistence tests, streaming save verification |

## Interfaces / Contracts

**`SupabaseConversationStore`** — same interface shape as `ConversationStore` but async:

```python
class SupabaseConversationStore:
    def __init__(self, supabase: Client, user_id: str): ...
    async def create(self, title: str = "Nueva conversación") -> dict: ...
    async def get(self, cid: str) -> dict | None: ...
    async def delete(self, cid: str) -> bool: ...
    async def list(self) -> list[dict]: ...
    async def add_message(self, cid: str, role: str, content: str) -> bool: ...
```

**Return shape** from `get()`:
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",  # Full UUID
    "title": "¿Cuál es el NPV de este proyecto?",
    "messages": [{"role": "user", "content": "...", "created_at": "..."}, ...],
    "created_at": "2026-05-14T22:00:00Z",
    "updated_at": "2026-05-14T22:01:00Z"
}
```

**`get_recent_history(user_id, limit) → list[dict]`** — new method on `CalculationExecutor`.

**Feature flag**: `USE_SUPABASE_PERSISTENCE` env var (default `true`). When `false`, `deps.py` returns the old `ConversationStore` singleton.

## Testing Strategy

| Layer | Test | Approach |
|-------|------|----------|
| Unit | `SupabaseConversationStore` CRUD | Mock `supabase.table().insert/select/delete().execute()` returning fixtures |
| Unit | User isolation | Two stores with different `user_id` — `get()` returns `None` for other user's conv |
| Unit | RLS simulation | Mock `.eq("user_id", ...)` chain — verify it's called on every query |
| Integration | Full chat flow with DB mock | `POST /chat` → verify messages table insert called |
| Integration | Stream persistence | SSE stream → verify user message immediate, assistant after stream end |
| Integration | Cross-session history | `CalculationExecutor.get_recent_history()` → verify DB queries with user_id filter |

## Migration / Rollout

**Migration**: Existing conversations are ephemeral by design (in-memory). No data to migrate. New conversations start persisting immediately upon deploy. `sql/002_conversations.sql` is additive — run once in Supabase SQL Editor.

**Rollback**: Set `USE_SUPABASE_PERSISTENCE=false` → restores old in-memory `ConversationStore`. Drop tables: `DROP TABLE messages CASCADE; DROP TABLE conversations CASCADE;`.

## Open Questions

- [ ] Frontend: does the UI display conversation IDs? Full UUIDs may need CSS truncation.
- [ ] Per-user conversation limit? Currently unbounded — add check in `create()` or DB function.
- [ ] Message pagination for long conversations? `get()` currently fetches all messages.
