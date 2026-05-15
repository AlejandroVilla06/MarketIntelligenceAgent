# Exploration: Supabase Persistence for Conversations

**Date**: 2026-05-14
**Status**: Complete
**Change**: supabase-persistence

---

## Current State

### In-Memory ConversationStore (`src/api/state.py`)

The store is a simple dict-based implementation with LRU eviction:

```python
class ConversationStore:
    _conversations: dict[str, dict]  # cid → conversation dict
    _access_order: list[str]         # LRU tracking
    _MAX_CONVERSATIONS = 1000
```

**Methods used by API routes**:
| Method | Called by | Purpose |
|--------|----------|---------|
| `create(title)` | `conversations.py`, `chat.py` | Create new conversation |
| `get(cid)` | `conversations.py`, `chat.py` | Get conversation by ID |
| `delete(cid)` | `conversations.py` | Delete conversation |
| `list()` | `conversations.py` | List all conversations (reversed LRU) |
| `add_message(cid, role, content)` | `chat.py` | Add message to conversation |

**Data structure per conversation**:
```python
{
    "id": str,           # UUID[:8] — 8-char truncated UUID
    "title": str,        # Auto-set from first user message (42 chars max)
    "messages": list,    # [{role, content, timestamp}]
    "created_at": datetime,
    "updated_at": datetime,
}
```

**Singleton instantiation** (`src/api/deps.py`):
```python
async def get_conversations() -> ConversationStore:
    global _conversation_store
    async with _conversation_store_lock:
        if _conversation_store is None:
            _conversation_store = ConversationStore()
    return _conversation_store
```

**LRU eviction logic**:
- `_touch(cid)` moves CID to end of `_access_order`
- `_enforce_limit()` pops oldest when `len > 1000`
- Called on `create()` and `get()`

### Critical Gap: No User Scoping

**All conversations are shared globally.** The `user` dict from JWT is available in routes but NEVER used for filtering. Any user can see/delete any other user's conversations. This MUST be fixed in the migration.

### Supabase Client Availability

`src/api/auth/supabase_client.py` already provides:
```python
def get_supabase_client() -> Client:
    # Singleton, initialized in lifespan
```

Used by auth routes via `supabase.table("profiles").select("*").eq("id", user_id).execute()` — same pattern works for conversations/messages.

**Async constraint**: `supabase-py` is synchronous (uses httpx internally). FastAPI endpoints are async. Solution: `asyncio.to_thread()` wrapper, same pattern used for `orch.ask()` in chat.py.

### Streaming Endpoint

`GET /api/chat/stream` (chat.py):
1. Gets/creates conversation
2. Adds user message immediately
3. Streams tokens via SSE
4. **At stream end**: `store.add_message(conv["id"], "assistant", full_response)` — this is where DB persistence must happen

---

## Affected Areas

- `src/api/state.py` — Replace or wrap with Supabase-backed store
- `src/api/deps.py` — Update `get_conversations()` to inject Supabase client
- `src/api/routes/conversations.py` — Add `user_id` filtering to all queries
- `src/api/routes/chat.py` — Persist messages to DB, handle async
- `src/api/schemas/chat.py` — May need updates for DB-sourced data (UUID format, etc.)
- `sql/init.sql` — Add conversations + messages tables, RLS policies
- `tests/conftest.py` — Mock Supabase table calls for conversations
- `tests/test_api_conversations.py` — Update for user-scoped tests
- `tests/test_api_chat.py` — Update for DB-backed store

---

## Approaches

### Option A: Direct Replacement — ConversationStore talks to Supabase

Replace the in-memory dict with Supabase queries. Simplest approach.

| Aspect | Details |
|--------|---------|
| **Pros** | Simple, single source of truth, no cache invalidation |
| **Cons** | Every read hits DB (~50-100ms latency per request) |
| **Effort** | Low |
| **Risk** | Higher latency on list/get operations |

### Option B: Write-Through Cache — Write to both, read from memory

Write to Supabase AND in-memory. Reads from memory first, falls back to DB.

| Aspect | Details |
|--------|---------|
| **Pros** | Fast reads (memory), durable writes (DB), best UX |
| **Cons** | Cache invalidation complexity, memory still bounded |
| **Effort** | Medium |
| **Risk** | Cache staleness on multi-instance deployments |

### Option C: Supabase + Redis Cache (future-proof)

Same as Option B but with Redis instead of in-memory dict.

| Aspect | Details |
|--------|---------|
| **Pros** | Shared cache across instances, production-ready |
| **Cons** | Extra infrastructure dependency, over-engineering for current scale |
| **Effort** | High |
| **Risk** | Unnecessary complexity for single-instance app |

---

## Recommendation: Option A (Direct Replacement)

**Why**:
1. **Single instance** — The app runs on one server (api_workers=1). No need for shared cache.
2. **Supabase is fast** — PostgREST queries on indexed columns are < 20ms typically.
3. **Simplicity** — No cache invalidation, no dual-write, no consistency bugs.
4. **User scoping** — DB-level filtering via RLS is more secure than in-memory filtering.
5. **LRU eviction unnecessary** — Supabase handles storage. Can add per-user limits later.

**The in-memory dict adds complexity for negligible benefit at current scale.** If latency becomes an issue later, Option B can be layered on top without changing the DB layer.

---

## Database Schema

```sql
-- =============================================================================
-- Conversations & Messages — Supabase Migration
-- =============================================================================

-- 1. Conversations table
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'Nueva conversación',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Messages table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON public.conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(conversation_id, created_at);

-- 4. Auto-update updated_at on conversation changes
CREATE OR REPLACE FUNCTION public.update_conversation_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.conversations
    SET updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_message_insert
    AFTER INSERT ON public.messages
    FOR EACH ROW
    EXECUTE FUNCTION public.update_conversation_timestamp();
```

---

## RLS Policies

```sql
-- =============================================================================
-- Row Level Security
-- =============================================================================

-- Conversations: users can only access their own
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own conversations" ON public.conversations;
CREATE POLICY "Users can view own conversations" ON public.conversations
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own conversations" ON public.conversations;
CREATE POLICY "Users can create own conversations" ON public.conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own conversations" ON public.conversations;
CREATE POLICY "Users can update own conversations" ON public.conversations
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own conversations" ON public.conversations;
CREATE POLICY "Users can delete own conversations" ON public.conversations
    FOR DELETE USING (auth.uid() = user_id);

-- Messages: users can only access messages in their conversations
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own messages" ON public.messages;
CREATE POLICY "Users can view own messages" ON public.messages
    FOR SELECT USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert own messages" ON public.messages;
CREATE POLICY "Users can insert own messages" ON public.messages
    FOR INSERT WITH CHECK (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete own messages" ON public.messages;
CREATE POLICY "Users can delete own messages" ON public.messages
    FOR DELETE USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );
```

---

## Migration Approach: Memory → DB

### Phase 1: Database Setup
1. Add conversation/message tables to `sql/init.sql`
2. Run migration in Supabase SQL Editor
3. Verify RLS policies work

### Phase 2: New SupabaseConversationStore
1. Create `src/api/persistence.py` with `SupabaseConversationStore` class
2. Same interface as `ConversationStore` but backed by Supabase
3. All methods wrapped in `asyncio.to_thread()` for async compatibility
4. User ID passed to constructor for scoping

### Phase 3: Update Dependencies
1. Modify `deps.py` to create `SupabaseConversationStore` with user context
2. Update route signatures to pass `user_id` to store

### Phase 4: Update Routes
1. `conversations.py` — All queries scoped by `user_id`
2. `chat.py` — Persist messages to DB, streaming endpoint saves at end

### Phase 5: Cleanup
1. Remove old `state.py` (or keep as fallback behind feature flag)
2. Update tests with Supabase mocks

### Data Loss Note
Existing in-memory conversations are **ephemeral by design** (lost on restart). No migration of existing data needed. New conversations will be persisted.

---

## Async Handling Strategy

```python
class SupabaseConversationStore:
    def __init__(self, supabase: Client, user_id: str):
        self._supabase = supabase
        self._user_id = user_id

    async def create(self, title: str = "Nueva conversación") -> dict:
        return await asyncio.to_thread(self._sync_create, title)

    def _sync_create(self, title: str) -> dict:
        result = self._supabase.table("conversations").insert({
            "user_id": self._user_id,
            "title": title,
        }).execute()
        return result.data[0]
```

All public methods are `async`, all internal implementations are sync (wrapped with `asyncio.to_thread()`).

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `sql/init.sql` | **Modify** | Add conversations + messages tables, RLS |
| `src/api/persistence.py` | **Create** | `SupabaseConversationStore` class |
| `src/api/deps.py` | **Modify** | Inject user-scoped store |
| `src/api/routes/conversations.py` | **Modify** | Use new store, add user scoping |
| `src/api/routes/chat.py` | **Modify** | Use new store, persist to DB |
| `src/api/state.py` | **Delete/Keep** | Remove or keep as fallback |
| `tests/conftest.py` | **Modify** | Mock Supabase table calls |
| `tests/test_api_conversations.py` | **Modify** | User-scoped tests |
| `tests/test_api_chat.py` | **Modify** | DB-backed store tests |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **supabase-py sync blocking** | High — blocks event loop | Wrap ALL calls in `asyncio.to_thread()` |
| **RLS policy misconfiguration** | High — data leak between users | Test RLS thoroughly, use service role for admin ops |
| **DB latency on list operations** | Medium — slower UX | Index on `updated_at DESC`, paginate results |
| **Streaming endpoint partial save** | Medium — orphaned user messages | Save user message to DB immediately, assistant message at stream end |
| **UUID format change** | Low — frontend expects 8-char IDs | Use full UUID from DB, update frontend if needed |
| **supabase-py connection pool exhaustion** | Low — concurrent requests | Supabase client manages pool internally |
| **No conversation limit** | Low — unbounded growth | Add per-user limit check in `create()`, or use DB function |

---

## Key Design Decisions

1. **Full UUIDs instead of truncated** — DB generates proper UUIDs. The 8-char truncation in `state.py` was for readability but increases collision risk. Frontend needs update if it displays IDs.

2. **User scoping at DB level via RLS** — Even if application code has bugs, RLS prevents cross-user data access. Defense in depth.

3. **`asyncio.to_thread()` pattern** — Already used in the codebase (`orch.ask()` in chat.py). Consistent approach.

4. **Store per request** — `SupabaseConversationStore` is lightweight (just holds supabase client + user_id). Created per-request via dependency injection. No singleton needed.

5. **Auto-title from first message** — Keep the same behavior: first user message becomes title (truncated to 42 chars). Implemented in `add_message()`.

---

## Ready for Proposal

**Yes** — The exploration is complete. The orchestrator should:
1. Create a proposal for `supabase-persistence` change
2. Use Option A (Direct Replacement) as the approach
3. Reference this exploration for technical details
4. Note that this is a natural follow-up to the `supabase-auth` change (Phase 2 mentioned in the original proposal)
