# Tasks: Supabase Authentication

## Phase 1: Dependencies & Config

- [x] 1.1 Install `supabase>=2.0.0` and `pyjwt>=2.8.0` (pip install, no requirements.txt)
- [x] 1.2 Add `supabase_url`, `supabase_key`, `supabase_jwt_secret` to `src/config/__init__.py`
- [x] 1.3 Add `supabase_url`, `supabase_key`, `supabase_jwt_secret` to `.env`
- [x] 1.4 Verify imports (`python -c "import supabase; import jwt; print('OK')"`)

## Phase 2: Auth Core Module

- [x] 2.1 Create `src/api/auth/__init__.py` — package init, export `get_current_user`, `get_supabase_client`
- [x] 2.2 Create `src/api/auth/supabase_client.py` — `init_supabase()`, `get_supabase_client()`, `close_supabase()` with lock-guarded singleton
- [x] 2.3 Create `src/api/auth/jwt_validator.py` — `HTTPBearer` + `jwt.decode(HS256, audience="authenticated")` → `HTTPException(401)` on failure
- [x] 2.4 Create `src/api/schemas/auth.py` — `SignupRequest`, `LoginRequest`, `TokenResponse`, `RefreshRequest`, `UserProfile`, `ProfileUpdateRequest`
- [x] 2.5 Create `src/api/auth/user_service.py` — `get_profile(user_id)`, `update_profile(user_id, **fields)` using Supabase client

## Phase 3: Auth Routes & Wiring

- [x] 3.1 Create `src/api/routes/auth.py` — signup, login, oauth, callback, logout, me, refresh endpoints
- [x] 3.2 Modify `src/api/app.py` — register auth router at `/api/auth`, add `init_supabase()` and `close_supabase()` to lifespan
- [x] 3.3 Modify `src/api/deps.py` — re-export `get_current_user()` and `get_supabase_client()` for route consumption

## Phase 4: Protect Existing Endpoints

- [x] 4.1 Modify `src/api/routes/chat.py` — add `user: dict = Depends(get_current_user)` to POST /chat and GET /chat/stream; pass user_id to conversation store
- [x] 4.2 Modify `src/api/routes/conversations.py` — add `Depends(get_current_user)` to all endpoints; filter by user_id
- [x] 4.3 Modify `src/api/routes/status.py` — add `Depends(get_current_user)` to GET /status
- [x] 4.4 Verify `GET /api/health` in `src/api/routes/health.py` remains public (no auth dependency)

## Phase 5: Database Migration

- [x] 5.1 Create `sql/init.sql` — profiles table, `handle_new_user()` trigger, RLS policies (idempotent)
- [ ] 5.2 Run migration in Supabase SQL Editor and confirm trigger fires on signup

## Phase 6: Testing

- [x] 6.1 Update `tests/conftest.py` — mock `get_supabase_client`, create valid JWT test token
- [x] 6.2 Create `tests/test_api_auth.py` — 15 tests covering signup, login, oauth, callback, me, chat auth, health, refresh, logout
- [ ] 6.3 Add auth tests to `tests/test_api_chat.py` — verify 401 without token, 200 with mocked user, user-scoped conversation creation
- [ ] 6.4 Add auth tests to `tests/test_api_conversations.py` — verify 401 without token, list only own conversations, 404 on cross-user access
- [ ] 6.5 Create `tests/test_jwt_validator.py` — parametrize: valid token, expired token, wrong secret, wrong audience, missing token → all 401

## Phase 7: Smoke Test

- [ ] 7.1 Start server and hit `POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/auth/me` manually
- [ ] 7.2 Verify protected endpoints return 401 without `Authorization` header
- [ ] 7.3 Verify protected endpoints return 200 with valid Bearer token
- [x] 7.4 Run `pytest` — all 24 API tests pass (15 auth + 9 existing), no regressions in API layer
