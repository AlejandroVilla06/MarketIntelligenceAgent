# Design: Supabase Authentication

## Technical Approach

Integrate Supabase Auth into FastAPI: `supabase-py` handles auth operations (signup, login, OAuth), `PyJWT` validates tokens locally per request. Auth endpoints at `/api/auth/*` remain public; all business endpoints except `/api/health` require a valid JWT via `Depends(get_current_user)`. The in-memory `ConversationStore` stays for Phase 1 — database persistence is Phase 2. Follows existing FastAPI patterns: `asynccontextmanager` lifespan, `APIRouter` tags, `Depends` DI, `BaseSettings` config.

## Architecture Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| AD1 | Supabase client lifecycle | Singleton in lifespan, accessed via `Depends(get_supabase_client)` | Thread-safe client with connection pooling; follows existing `deps.py` lock-guarded singleton pattern |
| AD2 | Token validation strategy | Local `jwt.decode()` with HS256, `audience="authenticated"` | Zero network overhead per request; Supabase JWTs are standard HS256 |
| AD3 | Auth gating mechanism | `Depends(get_current_user)` per route | FastAPI-native; per-route control lets health remain public; explicit in function signatures |
| AD4 | Profile creation guarantee | PostgreSQL trigger on `auth.users` INSERT | Profile exists even if API code has bugs; well-documented Supabase pattern |
| AD5 | Session management | supabase-py `set_session()` / refresh | Client handles token refresh transparently; no custom refresh logic |
| AD6 | Migration strategy | Two phases: auth now, DB persistence later | Smaller blast radius; auth complexity warrants its own change |
| AD7 | Auth router isolation | `/api/auth/` on separate `APIRouter` with no JWT dependency | Clean separation from protected business routes; symmetrical with existing routers |

## Data Flow

```
Signup → POST /api/auth/signup → supabase.auth.sign_up()
           → DB trigger auto-creates profiles row → {user_id, access_token}

OAuth  → GET /api/auth/oauth/{provider} → supabase.auth.sign_in_with_oauth()
           → redirect → provider auth → callback → exchange_code_for_session()

Protected → Authorization: Bearer <jwt> → get_current_user()
              → jwt.decode(token, SUPABASE_JWT_SECRET, HS256, aud="authenticated")
              → Route receives user dict → orchestrator.ask(query, history)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/api/auth/__init__.py` | Create | Auth package init |
| `src/api/auth/supabase_client.py` | Create | Singleton: `init_supabase()`, `get_supabase_client()`, `close_supabase()` |
| `src/api/auth/jwt_validator.py` | Create | `get_current_user()` via `HTTPBearer` + `jwt.decode(HS256)` |
| `src/api/auth/user_service.py` | Create | `get_profile()`, `update_profile()` using supabase-py |
| `src/api/routes/auth.py` | Create | Auth router: signup, login, oauth, callback, logout, me, refresh |
| `src/api/schemas/auth.py` | Create | Pydantic models for all auth request/response types |
| `sql/init.sql` | Create | `profiles` table, `handle_new_user` trigger, RLS policies |
| `src/api/app.py` | Modify | Register auth router; add Supabase init/close to lifespan |
| `src/api/deps.py` | Modify | Add `get_supabase_client()`, re-export `get_current_user()` |
| `src/api/routes/chat.py` | Modify | Add `Depends(get_current_user)` to `/chat`, `/chat/stream`, `/reset` |
| `src/api/routes/conversations.py` | Modify | Add `Depends(get_current_user)` to all CRUD endpoints |
| `src/api/routes/status.py` | Modify | Add `Depends(get_current_user)` — orchestrator internals need protection |
| `src/api/routes/__init__.py` | Modify | Allow auth endpoints to bypass `get_current_user` if needed |
| `src/config/__init__.py` | Modify | Add `supabase_url`, `supabase_key`, `supabase_jwt_secret` fields |
| `.env` | Modify | Add `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` |
| `tests/conftest.py` | Modify | Override `get_current_user` with mock returning fake user dict |
| `tests/test_api_auth.py` | Create | Auth endpoint tests with mocked Supabase client |

**Unchanged:** `src/api/state.py` (Phase 2), `src/api/middleware.py`, `src/agents/*`, `src/ui/*` (Streamlit), `src/api/routes/health.py` (public).

## Key Interfaces

```python
# jwt_validator.py — new dependency
security = HTTPBearer()
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = jwt.decode(credentials.credentials, settings.supabase_jwt_secret,
                         algorithms=["HS256"], audience="authenticated")
    return {"id": payload["sub"], "email": payload.get("email"), "role": payload.get("role")}
    # Raises HTTPException(401) on expired/invalid tokens

# deps.py additions — follow existing lock-guarded singleton pattern
async def init_supabase() -> None: ...
async def get_supabase_client() -> Client: ...
async def close_supabase() -> None: ...
```

**Config fields** follow existing pattern: `Annotated[str, Field(description="...")]` with `SettingsConfigDict(env_file=".env", extra="ignore")`.

## Testing Strategy

| Layer | Target | Approach |
|-------|--------|----------|
| Unit | `/api/auth/signup`, `/login` | `TestClient` + patched `get_supabase_client` returning fake sessions |
| Unit | `/api/auth/me` GET/PUT | Mock `get_current_user` returns `{"id": "test-uuid", "email": "test@example.com"}` |
| Unit | JWT validator | Parametrize `get_current_user` with valid, expired, wrong-secret, missing tokens |
| Unit | Protected routes | Verify 401 without `Authorization` header; 200 with valid mocked user |
| Unit | `/api/health` | Verify 200 without auth (remains public) |
| Integration | OAuth callback | Mock `supabase.auth.exchange_code_for_session` |

Mock pattern mirrors `tests/conftest.py`: `unittest.mock.patch` applied at module level before test imports. This avoids the heavy `sentence_transformers` import problem that the existing conftest already solves.

## Migration / Rollout

1. Run `sql/init.sql` in Supabase SQL Editor (creates `profiles`, trigger, RLS)
2. Deploy code; auth module activates on next restart
3. **Rollback**: drop trigger + table in SQL; remove `src/api/auth/`, revert route signatures, strip config fields; zero data loss (conversations remain in-memory)
4. **Known limitation**: in-memory conversations lost on restart — documented, Phase 2 resolves

## Open Questions

None. All architecture decisions resolved in design.
