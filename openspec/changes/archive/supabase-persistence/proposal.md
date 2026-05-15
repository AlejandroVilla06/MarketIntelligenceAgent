# Proposal: Supabase Persistence for Conversations

## Intent

Migrate chat history from volatile in-memory `ConversationStore` to persistent Supabase PostgreSQL. Eliminate data loss on restart, enforce user isolation via RLS, and enable cross-session data access for calculations.

## Scope

### In Scope
- Database schema (`conversations` + `messages` tables) with RLS policies and indexes
- `SupabaseConversationStore` replacing in-memory `ConversationStore`
- User scoping in all conversation/chat endpoints (realizes api-backend R4/R5/R6)
- Streaming endpoint persists messages to DB (user message immediately, assistant on completion)
- CalculationExecutor cross-session historical data access
- All tests updated for Supabase mocks, including user isolation verification

### Out of Scope
- Multi-instance caching (Redis)
- Real-time sync (Supabase Realtime)
- Conversation export/import
- Per-user storage quotas
- Frontend changes for full UUID format

## Capabilities

### New Capabilities
- `conversation-persistence`: Supabase-backed conversation/message storage, DB schema, RLS policies, `SupabaseConversationStore` with async interface

### Modified Capabilities
- `api-backend`: Conversation store backend changes from in-memory to Supabase; persistence guarantees across restarts; full UUIDs instead of 8-char truncated
- `python-repl`: CalculationExecutor gains method to query historical conversation data for cross-session calculations

## Approach

**Phase 1 — Schema + Migration**: Create `sql/002_conversations.sql` with tables, RLS, indexes, and auto-update trigger. Append to `sql/init.sql`.

**Phase 2 — SupabaseConversationStore**: New `src/api/persistence.py` — same interface as `ConversationStore` (create, get, delete, list, add_message) but backed by Supabase queries. All calls wrapped in `asyncio.to_thread()`. Per-request instantiation with `user_id` context.

**Phase 3 — Route Updates**: Route files get user-scoped store injection. Streaming endpoint saves user message immediately, assistant message at stream end.

**Phase 4 — CalculationExecutor History**: Add method to `python_repl.py` for querying past conversations by user_id, enabling "compare with last week's results" patterns.

**Phase 5 — Tests**: Update mocks, add RLS verification tests.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `sql/002_conversations.sql` | New | Schema, RLS, indexes, trigger |
| `sql/init.sql` | Modified | Include new migration |
| `src/api/persistence.py` | New | SupabaseConversationStore class |
| `src/api/state.py` | Removed | In-memory store replaced |
| `src/api/deps.py` | Modified | Per-request user-scoped store |
| `src/api/routes/conversations.py` | Modified | User scoping on all queries |
| `src/api/routes/chat.py` | Modified | DB persistence for messages |
| `src/market_orchestrator/python_repl.py` | Modified | Historical data access method |
| `tests/conftest.py` | Modified | Supabase table query mocks |
| `tests/test_api_conversations.py` | Modified | User isolation tests |
| `tests/test_api_chat.py` | Modified | Persistence tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| supabase-py blocks event loop | High | `asyncio.to_thread()` on ALL DB calls (same pattern as `orch.ask()`) |
| RLS blocks legitimate queries | Medium | Test with anon key (user) and service_role (admin) separately |
| UUID format change breaks frontend | Medium | Full UUIDs from DB — frontend must handle; coordinate update |
| Partial message loss on stream crash | Low | User message saved immediately; assistant only on completion |
| DB latency on conversation list | Low | Index on `updated_at DESC`; paginate results |

## Rollback Plan

1. Keep `src/api/state.py` as fallback (not deleted in Phase 2)
2. Feature flag `USE_SUPABASE_PERSISTENCE` toggles between stores
3. SQL migration can be reversed: `DROP TABLE messages; DROP TABLE conversations;`
4. Rollback = restore `deps.py` to return in-memory store singleton

## Dependencies

- `supabase-py` and `postgrest` — already installed
- Supabase project with `auth.users` table — already exists from `supabase-auth` change

## Success Criteria

- [ ] Conversations persist across server restart
- [ ] User A cannot see User B's conversations (RLS verified)
- [ ] Chat streaming works with DB persistence (no regression)
- [ ] CalculationExecutor can query historical conversation data
- [ ] All API tests pass with Supabase mocks
- [ ] No data loss on server restart