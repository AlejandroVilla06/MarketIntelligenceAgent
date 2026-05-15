# conversation-persistence Specification

## Purpose
Supabase PostgreSQL persistence for conversations and messages with Row-Level Security user isolation. Replaces volatile in-memory `ConversationStore`.

## Requirements

### Requirement: Database Schema (R1)
The system SHALL create `conversations` and `messages` tables with UUID PKs, FK relationships, and performance indexes.

| Table | Key Columns | Constraints |
|-------|------------|-------------|
| conversations | id UUID PK DEFAULT gen_random_uuid(), user_id UUID NOT NULL, title TEXT DEFAULT 'Nueva conversación', created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW() | FK user_id→auth.users(id) |
| messages | id UUID PK DEFAULT gen_random_uuid(), conversation_id UUID NOT NULL, role TEXT CHECK(IN 'user','assistant'), content TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW() | FK conversation_id→conversations(id) ON DELETE CASCADE |
| indexes | conversations(user_id), messages(conversation_id), conversations(updated_at DESC) | — |

#### Scenario: Schema created via migration
- GIVEN migration `sql/002_conversations.sql` applied to Supabase
- WHEN `information_schema.tables` is queried
- THEN `conversations` and `messages` SHALL exist with all columns per spec

#### Scenario: Cascade delete removes messages
- GIVEN conversation with 5 messages
- WHEN `DELETE FROM conversations WHERE id = $1`
- THEN all 5 messages SHALL be removed automatically

### Requirement: updated_at Trigger (R2)
The system SHALL auto-update `updated_at` on conversation modification via a trigger function `update_updated_at_column()` and trigger `set_conversations_updated_at` BEFORE UPDATE ON conversations FOR EACH ROW.

#### Scenario: Trigger fires on update
- GIVEN a conversation with `title = 'Old'`
- WHEN `UPDATE conversations SET title = 'New' WHERE id = $1`
- THEN `updated_at` SHALL be later than before the update

### Requirement: RLS Policies (R3)
RLS SHALL be enabled on both tables. Users SHALL only access their own data.

| Table | Operation | Policy Expression |
|-------|-----------|-------------------|
| conversations | SELECT | `auth.uid() = user_id` |
| conversations | INSERT | `WITH CHECK (auth.uid() = user_id)` |
| conversations | DELETE | `auth.uid() = user_id` |
| messages | ALL | `conversation_id IN (SELECT id FROM conversations WHERE user_id = auth.uid())` |

#### Scenario: User isolation
- GIVEN user A with conversation CA, user B with conversation CB
- WHEN user A queries conversations
- THEN only CA SHALL be returned; CB SHALL NOT appear

#### Scenario: Cross-user message access blocked
- GIVEN user A's authenticated session
- WHEN querying messages from conversation CB (owned by user B)
- THEN zero rows SHALL be returned

### Requirement: SupabaseBackedStore (R4)
`SupabaseConversationStore` SHALL implement the current `ConversationStore` interface (`create`, `get`, `list`, `delete`, `add_message`). All methods SHALL accept `user_id` and wrap DB calls in `asyncio.to_thread()`. The store SHALL use `get_supabase_client()` singleton.

#### Scenario: Create persists to Supabase
- GIVEN valid Supabase client and user_id `u1`
- WHEN `store.create(user_id="u1", title="My chat")`
- THEN a row SHALL exist in `conversations` with `user_id = 'u1'`

#### Scenario: List returns user-scoped results
- GIVEN user A has 3 conversations, user B has 2
- WHEN `store.list(user_id="A")`
- THEN exactly 3 conversations SHALL be returned, ordered by `updated_at DESC`

#### Scenario: Delete with ownership check
- GIVEN user A attempting to delete user B's conversation
- WHEN `store.delete(conversation_id="cb-1", user_id="A")`
- THEN no row SHALL be deleted; the method SHALL raise or return a not-found indicator

#### Scenario: Add message updates conversation timestamp
- GIVEN an existing conversation
- WHEN `store.add_message(conv_id="c1", user_id="u1", role="user", content="hello")`
- THEN a message row SHALL be inserted AND `conversations.updated_at` SHALL be refreshed

### Requirement: API Route Integration (R5)
Routes SHALL use `SupabaseConversationStore` with the authenticated user's ID. POST /api/conversations SHALL create a user-linked conversation. GET /api/conversations SHALL filter by authenticated user. DELETE /api/conversations/{id} SHALL verify ownership before deleting. POST /api/chat SHALL save user message immediately and assistant message after LLM responds.

#### Scenario: POST creates user-scoped conversation
- GIVEN authenticated user `abc-123`
- WHEN `POST /api/conversations`
- THEN a conversation with `user_id = abc-123` SHALL be persisted in Supabase

#### Scenario: GET filters by authenticated user
- GIVEN authenticated user A with 2 conversations
- WHEN `GET /api/conversations`
- THEN only user A's 2 conversations SHALL appear in the response

#### Scenario: DELETE rejects non-owner
- GIVEN user A attempting to delete conversation owned by user B
- WHEN `DELETE /api/conversations/{b-id}`
- THEN the operation SHALL fail with an access-denied response

#### Scenario: Chat persists messages to Supabase
- GIVEN authenticated user sends query "What is AAPL?"
- WHEN POST /api/chat processes the request
- THEN user message SHALL be persisted before orchestrator call AND assistant message SHALL be persisted after LLM responds
