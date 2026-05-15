# Exploration: Supabase Authentication Integration

**Date**: 2026-05-09
**Status**: Complete
**Change**: supabase-auth

---

## Current State

The project has a working FastAPI backend (`src/api/`) created in the `infra-api` change:

- **App factory**: `src/api/app.py` with `create_app()`, CORS middleware, lifespan-managed orchestrator singleton
- **Routes**: health, status, chat (sync + SSE streaming), conversations CRUD, reset
- **State**: In-memory `ConversationStore` (`src/api/state.py`) with LRU eviction (max 1000)
- **Dependencies**: `src/api/deps.py` with `get_orchestrator()` and `get_conversations()` singletons
- **Auth**: **NONE** — all endpoints are open, no user identity
- **Config**: `src/config/__init__.py` has `Settings(BaseSettings)` with API keys, CORS origins, etc.
- **Tests**: 9/9 pass with mocked orchestrator (`tests/conftest.py` patches `get_orchestrator`)

Key files:
- `src/api/app.py` — FastAPI factory, CORS, router includes
- `src/api/deps.py` — Dependency injection (orchestrator, conversation store)
- `src/api/state.py` — In-memory conversation store (will be replaced)
- `src/api/middleware.py` — Request logging
- `src/api/routes/chat.py` — Chat endpoints (uses `get_conversations`)
- `src/api/routes/conversations.py` — Conversation CRUD (uses `get_conversations`)
- `src/api/schemas/chat.py` — Pydantic models
- `src/config/__init__.py` — Settings with all env vars

The `state.py` file already has a comment: *"Temporary — will be replaced by Supabase in a later change."*

---

## Affected Areas

| File | Impact | Why |
|------|--------|-----|
| `src/api/deps.py` | **Modified** | Add `get_current_user()` dependency, Supabase client singleton |
| `src/api/state.py` | **Replaced** | In-memory store → Supabase PostgreSQL conversations table |
| `src/api/middleware.py` | **Modified** | Add JWT validation middleware (optional, can use Depends instead) |
| `src/api/app.py` | **Modified** | Register auth router, add Supabase client init to lifespan |
| `src/api/routes/chat.py` | **Modified** | Add `Depends(get_current_user)`, pass user_id to store |
| `src/api/routes/conversations.py` | **Modified** | Add `Depends(get_current_user)`, scope queries to user_id |
| `src/config/__init__.py` | **Modified** | Add `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` |
| `.env` | **Modified** | Add Supabase credentials |
| **NEW**: `src/api/routes/auth.py` | **Created** | Auth endpoints (signup, login, OAuth, me) |
| **NEW**: `src/api/schemas/auth.py` | **Created** | Auth request/response Pydantic models |
| **NEW**: `src/api/auth/` | **Created** | Auth module (supabase client, JWT validation, user management) |
| **NEW**: `tests/test_api_auth.py` | **Created** | Auth endpoint tests |

---

## Approaches

### Approach 1: Supabase Python Client + JWT Validation (RECOMMENDED)

Use `supabase-py` for auth operations (signup, login, OAuth) and validate JWTs in FastAPI using `python-jose` or `PyJWT`.

**How it works**:
1. Supabase handles all auth (email/password, OAuth, magic links)
2. Supabase issues JWTs (access_token + refresh_token)
3. Frontend sends `Authorization: Bearer <access_token>` header
4. FastAPI validates JWT signature using Supabase's JWT secret
5. FastAPI extracts `user_id` (sub claim) and attaches to request

**Pros**:
- Supabase manages password hashing, OAuth flows, token refresh
- Built-in RLS support (JWT claims match `auth.uid()`)
- No need to implement OAuth flows manually
- Supabase free tier is generous (50k monthly active users)
- Battle-tested security (GoTrue auth server)

**Cons**:
- External dependency on Supabase service
- Need to handle JWT validation correctly (signature, expiry, issuer)
- OAuth callback URLs need Supabase project configuration

**Effort**: Medium

### Approach 2: FastAPI Users + PostgreSQL

Use `fastapi-users` library with direct PostgreSQL connection.

**How it works**:
1. `fastapi-users` handles registration, login, OAuth
2. Direct PostgreSQL connection (no Supabase)
3. JWT or cookie-based sessions

**Pros**:
- Full control over auth logic
- No external service dependency
- Built-in OAuth support

**Cons**:
- Need to manage PostgreSQL hosting separately
- More code to write and maintain
- No built-in RLS (need to implement in application layer)
- No built-in Supabase integration for future features (storage, realtime)

**Effort**: High

### Approach 3: Auth0 / Clerk / Other SaaS

Use a dedicated auth SaaS provider.

**Pros**:
- Most mature auth solutions
- Excellent developer experience
- Built-in MFA, passwordless, social logins

**Cons**:
- Additional cost
- Vendor lock-in
- Overkill for this project's needs
- No RLS integration with Supabase

**Effort**: Low-Medium

---

## Recommendation

**Approach 1: Supabase Python Client + JWT Validation**

Rationale:
1. The project already plans to use Supabase for database (conversations persistence)
2. Supabase auth is free for the expected user scale
3. RLS integration means database security is automatic
4. The `supabase-py` client handles all auth operations
5. JWT validation is straightforward with `PyJWT`
6. Future Next.js frontend has excellent Supabase auth support (`@supabase/ssr`)

---

## Detailed Design

### 1. Supabase Project Setup (User Steps)

The user needs to:
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Get the project URL and anon key from Settings → API
3. Get the JWT secret from Settings → API → JWT Secret
4. Enable Google OAuth: Authentication → Providers → Google (requires Google Cloud Console OAuth credentials)
5. Enable GitHub OAuth: Authentication → Providers → GitHub (requires GitHub OAuth App)
6. Set redirect URLs in Supabase dashboard: `http://localhost:3000/auth/callback` (Next.js) and `http://localhost:8000/api/auth/callback` (FastAPI)

### 2. Environment Variables

```env
# Supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_JWT_SECRET=<jwt-secret-from-settings>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>  # For admin operations
```

### 3. Database Schema

```sql
-- User profiles (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    preferred_language TEXT DEFAULT 'es' CHECK (preferred_language IN ('es', 'en')),
    preferred_theme TEXT DEFAULT 'dark' CHECK (preferred_theme IN ('light', 'dark')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations (linked to users)
CREATE TABLE public.conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT DEFAULT 'Nueva conversación',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages (linked to conversations)
CREATE TABLE public.messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX idx_conversations_updated_at ON public.conversations(updated_at DESC);

-- RLS Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Profiles: users can only read/update their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Conversations: users can only access their own conversations
CREATE POLICY "Users can view own conversations"
    ON public.conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own conversations"
    ON public.conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
    ON public.conversations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
    ON public.conversations FOR DELETE
    USING (auth.uid() = user_id);

-- Messages: users can only access messages in their conversations
CREATE POLICY "Users can view messages in own conversations"
    ON public.messages FOR SELECT
    USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own conversations"
    ON public.messages FOR INSERT
    WITH CHECK (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

-- Trigger: auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
```

### 4. Auth Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  src/api/app.py (factory)                                   │
│  ├── Lifespan: init_supabase_client()                       │
│  ├── CORS middleware                                        │
│  ├── Request logging middleware                             │
│  └── Routers:                                               │
│      ├── /api/auth/*    (auth.py - NEW)                     │
│      ├── /api/chat      (chat.py - MODIFIED)                │
│      ├── /api/conversations (conversations.py - MODIFIED)   │
│      ├── /api/health    (health.py)                         │
│      └── /api/status    (status.py)                         │
├─────────────────────────────────────────────────────────────┤
│  src/api/deps.py (dependencies)                             │
│  ├── get_supabase_client() → Client                         │
│  ├── get_current_user(token) → User                         │
│  ├── get_orchestrator() → MarketOrchestrator                │
│  └── get_conversation_store(user_id) → ConversationStore    │
├─────────────────────────────────────────────────────────────┤
│  src/api/auth/ (NEW module)                                 │
│  ├── supabase_client.py  — Client initialization            │
│  ├── jwt_validator.py    — JWT validation with PyJWT        │
│  └── user_service.py     — Profile CRUD operations          │
└─────────────────────────────────────────────────────────────┘
```

### 5. Auth Endpoints

```python
# src/api/routes/auth.py

# POST /api/auth/signup
# Body: { "email": "...", "password": "..." }
# Creates user in Supabase, auto-creates profile via trigger
# Returns: { "user": {...}, "session": { "access_token": "...", "refresh_token": "..." } }

# POST /api/auth/login
# Body: { "email": "...", "password": "..." }
# Returns: { "user": {...}, "session": { "access_token": "...", "refresh_token": "..." } }

# GET /api/auth/oauth/{provider}
# provider: "google" | "github"
# Returns: { "url": "https://supabase.co/auth/v1/authorize?..." }
# Frontend redirects user to this URL

# GET /api/auth/callback
# Query: code=<authorization_code>
# Exchanges code for session
# Returns: { "user": {...}, "session": {...} }

# POST /api/auth/logout
# Headers: Authorization: Bearer <access_token>
# Returns: { "message": "Logged out" }

# GET /api/auth/me
# Headers: Authorization: Bearer <access_token>
# Returns: { "id": "...", "email": "...", "full_name": "...", "avatar_url": "...", ... }

# PUT /api/auth/me
# Headers: Authorization: Bearer <access_token>
# Body: { "full_name": "...", "preferred_language": "en", "preferred_theme": "light" }
# Returns: updated profile

# POST /api/auth/refresh
# Body: { "refresh_token": "..." }
# Returns: new session with fresh access_token
```

### 6. JWT Validation Middleware

```python
# src/api/auth/jwt_validator.py

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate Supabase JWT and return user claims."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
        )
        return {
            "id": payload["sub"],  # user UUID
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 7. Conversation Store Migration

Replace in-memory `ConversationStore` with Supabase-backed store:

```python
# src/api/state.py (replaced)

class SupabaseConversationStore:
    def __init__(self, client: Client, user_id: str):
        self.client = client
        self.user_id = user_id

    async def create(self, title: str = "Nueva conversación") -> dict:
        response = self.client.table("conversations").insert({
            "user_id": self.user_id,
            "title": title,
        }).execute()
        return response.data[0]

    async def get(self, cid: str) -> dict | None:
        response = self.client.table("conversations").select(
            "*, messages(*)"
        ).eq("id", cid).eq("user_id", self.user_id).maybe_single().execute()
        return response.data

    async def list(self) -> list[dict]:
        response = self.client.table("conversations").select(
            "id, title, created_at, updated_at, messages(count)"
        ).eq("user_id", self.user_id).order("updated_at", desc=True).execute()
        return response.data

    async def add_message(self, cid: str, role: str, content: str) -> dict:
        self.client.table("messages").insert({
            "conversation_id": cid,
            "role": role,
            "content": content,
        }).execute()
        # Update conversation title if first user message
        if role == "user":
            conv = await self.get(cid)
            if conv and conv["title"] == "Nueva conversación":
                title = (content[:42] + "…") if len(content) > 42 else content
                self.client.table("conversations").update(
                    {"title": title}
                ).eq("id", cid).execute()
        return await self.get(cid)

    async def delete(self, cid: str) -> bool:
        response = self.client.table("conversations").delete().eq(
            "id", cid
        ).eq("user_id", self.user_id).execute()
        return len(response.data) > 0
```

### 8. Dependencies

```toml
# Add to requirements or pyproject.toml
supabase>=2.0.0       # Supabase Python client
PyJWT>=2.8.0          # JWT validation (or python-jose)
cryptography>=41.0.0  # Required by PyJWT for HS256
```

Note: `httpx` is already installed (used by `supabase-py` internally).

### 9. CORS Configuration

The existing CORS setup needs to support:
- Credentials (cookies/tokens) — already has `allow_credentials=True`
- Specific origins (not `*` when credentials=True) — already configured from settings
- Auth headers — already has `allow_headers=["*"]`

No changes needed to CORS config. The frontend just needs to include the `Authorization` header.

### 10. Security Considerations

1. **JWT Secret**: Never expose in client-side code. Only used server-side.
2. **RLS**: Enabled on all tables — even if API has a bug, database enforces access control.
3. **Rate Limiting**: Add `slowapi` or similar for auth endpoints (signup, login):
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   @router.post("/auth/login")
   @limiter.limit("5/minute")
   async def login(...): ...
   ```
4. **Token Refresh**: Frontend should handle token refresh before expiry. Supabase JS client does this automatically.
5. **Service Role Key**: Only used for admin operations (user management), never sent to client.
6. **Password Requirements**: Supabase enforces minimum 6 characters by default.
7. **Email Verification**: Supabase sends verification emails by default. Can be disabled in dashboard for development.

---

## Migration Path: In-Memory → Supabase

### Phase 1: Auth Only (this change)
1. Add Supabase auth (signup, login, OAuth, JWT validation)
2. Add `get_current_user()` dependency
3. Keep in-memory conversation store but add user_id awareness
4. Protected endpoints require auth but conversations still in-memory

### Phase 2: Database Persistence (next change)
1. Create Supabase tables (profiles, conversations, messages)
2. Replace `ConversationStore` with `SupabaseConversationStore`
3. Migrate existing in-memory data (if any) via admin endpoint
4. Remove `src/api/state.py` in-memory implementation

### Why Two Phases?
- Auth is complex enough to warrant its own change
- Separation of concerns (auth vs data persistence)
- Can test auth independently
- Reduces risk (smaller blast radius)

---

## Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `src/api/auth/__init__.py` | Auth module init |
| `src/api/auth/supabase_client.py` | Supabase client singleton |
| `src/api/auth/jwt_validator.py` | JWT validation + `get_current_user()` |
| `src/api/auth/user_service.py` | Profile CRUD operations |
| `src/api/routes/auth.py` | Auth endpoints (signup, login, OAuth, me) |
| `src/api/schemas/auth.py` | Auth request/response Pydantic models |
| `tests/test_api_auth.py` | Auth endpoint tests |
| `tests/conftest_auth.py` | Auth test fixtures (mock Supabase, fake JWT) |

### Modified Files
| File | Changes |
|------|---------|
| `src/api/app.py` | Register auth router, add Supabase client init to lifespan |
| `src/api/deps.py` | Add `get_supabase_client()`, `get_current_user()` |
| `src/api/routes/chat.py` | Add `Depends(get_current_user)`, pass user_id |
| `src/api/routes/conversations.py` | Add `Depends(get_current_user)`, scope to user_id |
| `src/config/__init__.py` | Add `supabase_url`, `supabase_key`, `supabase_jwt_secret` |
| `.env` | Add Supabase credentials |

### Unchanged Files
| File | Reason |
|------|--------|
| `src/api/state.py` | Replaced in Phase 2, not this change |
| `src/api/middleware.py` | Auth handled via Depends, not middleware |
| `src/ui/app.py` | Streamlit unaffected |
| `src/agents/*` | Agent layer unchanged |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JWT validation fails with Supabase tokens | Medium | High | Test with real Supabase tokens; use HS256 (not RS256) |
| OAuth callback URL misconfiguration | Medium | Medium | Document exact URLs; test each provider |
| Supabase service downtime | Low | High | Implement graceful degradation; cache JWT validation |
| Breaking existing tests | Medium | Medium | Mock Supabase client in tests (same pattern as orchestrator) |
| In-memory store loses data during migration | High | Low | Documented as known limitation; Phase 2 solves it |
| Rate limiting blocks legitimate users | Low | Medium | Use generous limits; add IP whitelist for development |
| Supabase free tier limits hit | Low | Low | Monitor usage; upgrade if needed |

---

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| AD1 | Use `supabase-py` client (not raw HTTP) | Official client handles token refresh, retries, type safety |
| AD2 | JWT validation in FastAPI (not Supabase client verification) | Faster (no network call); Supabase JWTs are self-contained |
| AD3 | HS256 algorithm (not RS256) | Supabase uses HS256 by default; simpler key management |
| AD4 | `Depends(get_current_user)` (not middleware) | More Pythonic; per-route control; FastAPI-native pattern |
| AD5 | Auto-create profile via database trigger (not API code) | Guarantees profile exists even if API code has bugs |
| AD6 | Two-phase migration (auth then persistence) | Smaller changes, lower risk, easier to test |
| AD7 | Keep `src/api/state.py` in Phase 1 | Avoid breaking existing endpoints; migrate in Phase 2 |
| AD8 | `http` security scheme (not cookie) | Stateless; works with Next.js SSR; simpler for API-first design |

---

## Open Questions

1. **Email verification**: Should we require email verification before allowing API access? (Supabase sends verification emails by default)
2. **Anonymous access**: Should some endpoints (health, status) remain public?
3. **Session duration**: What token expiry time? (Supabase default: 1 hour access, 7 days refresh)
4. **Profile fields**: Are `preferred_language` and `preferred_theme` needed now or later?

---

## Ready for Proposal

**Yes** — the exploration is complete. The orchestrator should proceed to `sdd-propose` with:

- **Change name**: `supabase-auth`
- **Intent**: Add Supabase authentication to the FastAPI API, protecting all endpoints with JWT validation
- **Scope**: Auth module, auth endpoints, JWT validation, protected routes, Supabase project setup
- **Approach**: Supabase Python client + PyJWT validation + database trigger for profile creation
- **Out of scope**: Database persistence for conversations (Phase 2), Next.js frontend
