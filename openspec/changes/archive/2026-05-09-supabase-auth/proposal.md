# Proposal: Supabase Authentication

## Intent

Secure the FastAPI backend with user authentication via Supabase, establishing identity for all protected endpoints. This is Phase 1 of the auth+persistence migration: auth now, conversation persistence later.

## Scope

### In Scope
- Supabase auth integration (signup, login, OAuth with Google/GitHub, token refresh)
- JWT validation in FastAPI via `Depends(get_current_user)`
- User profile auto-creation via DB trigger on `auth.users` INSERT
- Auth endpoints: signup, login, OAuth redirect/callback, logout, me (GET/PUT), refresh
- Protect all existing endpoints except `/api/health` and `/api/auth/*`
- Supabase SQL migration: `profiles` table, RLS policies, `handle_new_user` trigger
- Auth request/response Pydantic schemas
- Tests with mocked Supabase client and fake JWTs

### Out of Scope
- Conversation/message persistence in Supabase (Phase 2)
- Streamlit UI auth (Streamlit remains open)
- Next.js frontend implementation
- Rate limiting (separate change)
- Admin endpoints for user management
- Email verification enforcement

## Capabilities

### New Capabilities
- `supabase-auth`: Supabase-backed authentication — signup, login, OAuth, JWT validation, token refresh
- `user-profiles`: User profile CRUD — auto-created via DB trigger, editable via `/api/auth/me`

### Modified Capabilities
- `api-backend`: All endpoints except `/api/health` require authentication; new auth router registered

## Approach

**Supabase Python Client + PyJWT validation**, two-phase migration:

1. **Supabase handles auth operations** (signup, login, OAuth flows, token refresh) — the Python client wraps GoTrue
2. **FastAPI validates JWTs locally** using `PyJWT` with the Supabase JWT secret (no network call per request)
3. **`Depends(get_current_user)`** on protected routes — per-route control, FastAPI-native
4. **Database trigger** auto-creates `profiles` row on `auth.users` INSERT — guarantees profile exists
5. **In-memory store stays** for Phase 1 — `ConversationStore` gains `user_id` awareness but no DB migration yet

OAuth flow: Frontend gets redirect URL from `/api/auth/oauth/{provider}`, user authenticates, Supabase redirects to callback URL, backend exchanges code for session.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/api/auth/__init__.py` | New | Auth package |
| `src/api/auth/supabase_client.py` | New | Supabase client singleton + lifespan init |
| `src/api/auth/jwt_validator.py` | New | JWT decode/validate + `get_current_user` dependency |
| `src/api/auth/user_service.py` | New | Profile CRUD via Supabase client |
| `src/api/routes/auth.py` | New | Auth endpoints router |
| `src/api/schemas/auth.py` | New | Auth request/response Pydantic models |
| `src/api/app.py` | Modified | Register auth router, add Supabase init to lifespan |
| `src/api/deps.py` | Modified | Add `get_supabase_client()`, `get_current_user()` |
| `src/api/routes/chat.py` | Modified | Add `Depends(get_current_user)` |
| `src/api/routes/conversations.py` | Modified | Add `Depends(get_current_user)`, scope to user_id |
| `src/config/__init__.py` | Modified | Add `supabase_url`, `supabase_key`, `supabase_jwt_secret` |
| `.env` | Modified | Add `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` |
| `sql/init.sql` | New | Profiles table, trigger, RLS policies |
| `tests/test_api_auth.py` | New | Auth endpoint tests with mocked Supabase |
| `src/agents/*` | Unchanged | Agent layer untouched |
| `src/ui/app.py` | Unchanged | Streamlit unaffected |
| `src/api/state.py` | Unchanged | In-memory store remains (Phase 2 replaces) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| JWT validation fails with Supabase tokens | Medium | Use HS256 (Supabase default); test with real tokens before merge |
| OAuth callback URL misconfiguration | Medium | Document exact redirect URLs per provider; test each in dev |
| Supabase service downtime blocks auth | Low | Graceful 503 response; JWTs are self-contained (no call per request) |
| Breaking existing API tests | Medium | Mock `get_current_user` in test fixtures; skip auth for health endpoint |
| In-memory conversations lost on server restart | High | Known limitation; documented; Phase 2 solves it |
| `supabase-py` API changes | Low | Pin version `>=2.0.0`; follow migration guides |

## Rollback Plan

1. Remove `src/api/auth/` package and `src/api/routes/auth.py`
2. Revert `deps.py`, `app.py`, `chat.py`, `conversations.py` to remove `get_current_user` dependency
3. Remove `supabase_url`, `supabase_key`, `supabase_jwt_secret` from config
4. Remove `supabase` and `pyjwt` from dependencies
5. All endpoints return to open access; no data loss (in-memory store unchanged)

Rollback is safe because Phase 1 does NOT modify the conversation store — only adds auth gating.

## Dependencies

- **Supabase project**: Must be created and configured (URL, anon key, JWT secret, OAuth providers)
- **Python packages**: `supabase>=2.0.0`, `pyjwt>=2.8.0`, `cryptography>=41.0.0`
- **Supabase dashboard**: OAuth redirect URLs, email confirmation settings
- **Database migrations**: Run `sql/init.sql` in Supabase SQL editor

## Success Criteria

- [ ] All auth endpoints return correct status codes (201 signup, 200 login, 200 me, 401 unauthorized)
- [ ] Protected endpoints return 403/401 without valid Bearer token
- [ ] `/api/health` remains accessible without auth
- [ ] JWT tokens from Supabase are validated correctly (signature, expiry, audience)
- [ ] OAuth redirect URLs work for Google and GitHub
- [ ] User profile auto-created on signup via DB trigger
- [ ] Existing tests pass with mocked auth dependency
- [ ] New auth tests pass with ≥90% coverage on auth module