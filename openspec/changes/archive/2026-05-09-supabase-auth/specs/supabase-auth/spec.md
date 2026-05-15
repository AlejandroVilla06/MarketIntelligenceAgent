# Supabase Authentication Specification

## Purpose

Supabase-backed user authentication for the FastAPI backend: signup, login, OAuth (Google/GitHub), JWT validation, and token management. Establishes user identity for all protected endpoints.

## Requirements

### Requirement: Supabase Client Configuration (R1)

The system SHALL create a Supabase client singleton at startup via the FastAPI lifespan, initialized with `SUPABASE_URL` and `SUPABASE_KEY` from settings. The client SHALL be accessible through dependency injection as `get_supabase_client()`.

#### Scenario: Client initialized at startup

- GIVEN the FastAPI application starts
- WHEN the lifespan startup handler executes
- THEN a Supabase client singleton SHALL be instantiated with `settings.SUPABASE_URL` and `settings.SUPABASE_KEY`
- AND the instance SHALL be stored for reuse across the application lifetime

#### Scenario: Client accessible via dependency injection

- GIVEN the application is running with an initialized Supabase client
- WHEN a route handler calls `get_supabase_client()`
- THEN the same singleton client instance SHALL be returned

---

### Requirement: Email/Password Signup (R2)

POST /api/auth/signup SHALL accept `email` (valid email string) and `password` (min 6 chars). On success, SHALL return HTTP 201 with `user_id` (UUID string) and `access_token` (JWT string). Duplicate email SHALL return HTTP 400. Missing or invalid fields SHALL return HTTP 422.

#### Scenario: Successful signup with valid credentials

- GIVEN email `newuser@example.com` is not registered
- WHEN POST /api/auth/signup is called with `{"email": "newuser@example.com", "password": "Str0ng!Pass"}`
- THEN HTTP 201 is returned
- AND the body contains `user_id` (UUID) and `access_token` (JWT string)

#### Scenario: Signup with already registered email

- GIVEN email `existing@example.com` is already registered in Supabase
- WHEN POST /api/auth/signup is called with `{"email": "existing@example.com", "password": "Str0ng!Pass"}`
- THEN HTTP 400 is returned
- AND the body contains `{"detail": "Email already registered"}`

#### Scenario: Signup with missing fields

- GIVEN the API is running
- WHEN POST /api/auth/signup is called with `{}` (no email, no password)
- THEN HTTP 422 is returned
- AND the body describes the missing required fields

#### Scenario: Signup with invalid email format

- GIVEN the API is running
- WHEN POST /api/auth/signup is called with `{"email": "not-an-email", "password": "Str0ng!Pass"}`
- THEN HTTP 422 is returned with a validation error for `email`

---

### Requirement: Email/Password Login (R3)

POST /api/auth/login SHALL accept `email` and `password`. On success, SHALL return HTTP 200 with `access_token` and `refresh_token` (both JWT strings). Invalid credentials SHALL return HTTP 401.

#### Scenario: Successful login with correct credentials

- GIVEN a registered user with email `user@example.com` and password `Str0ng!Pass`
- WHEN POST /api/auth/login is called with those credentials
- THEN HTTP 200 is returned
- AND the body contains `access_token` and `refresh_token`

#### Scenario: Login with incorrect password

- GIVEN a registered user with email `user@example.com`
- WHEN POST /api/auth/login is called with `{"email": "user@example.com", "password": "WrongPass1"}`
- THEN HTTP 401 is returned
- AND the body contains `{"detail": "Invalid credentials"}`

#### Scenario: Login with nonexistent email

- GIVEN email `ghost@example.com` is not registered
- WHEN POST /api/auth/login is called with `{"email": "ghost@example.com", "password": "Anything1"}`
- THEN HTTP 401 is returned

---

### Requirement: OAuth Authentication (R4)

GET /api/auth/oauth/{provider} SHALL accept `google` or `github` as the provider path parameter. SHALL return HTTP 200 with the Supabase OAuth authorization URL. Unsupported providers SHALL return HTTP 400.

#### Scenario: Google OAuth redirect URL

- GIVEN provider path parameter is `google`
- WHEN GET /api/auth/oauth/google is called
- THEN HTTP 200 is returned
- AND the body contains `{"url": "https://kytdgetgeoykzkyrtzpi.supabase.co/auth/v1/authorize?provider=google&..."}`

#### Scenario: GitHub OAuth redirect URL

- GIVEN provider path parameter is `github`
- WHEN GET /api/auth/oauth/github is called
- THEN HTTP 200 is returned
- AND the body contains a Supabase OAuth URL with `provider=github`

#### Scenario: Unsupported OAuth provider

- GIVEN provider path parameter is `facebook`
- WHEN GET /api/auth/oauth/facebook is called
- THEN HTTP 400 is returned
- AND the body contains `{"detail": "Unsupported provider. Available: google, github"}`

---

### Requirement: OAuth Callback (R5)

GET /api/auth/callback SHALL accept a `code` query parameter from the OAuth provider redirect. SHALL exchange the code for a Supabase session. On success, SHALL return HTTP 200 with `user_id` and `access_token`. Invalid or expired code SHALL return HTTP 401.

#### Scenario: Successful OAuth callback exchange

- GIVEN a valid authorization `code` from Google/GitHub OAuth redirect
- WHEN GET /api/auth/callback?code=<valid_code> is called
- THEN HTTP 200 is returned
- AND the body contains `user_id` (UUID) and `access_token` (JWT)

#### Scenario: Callback with invalid code

- GIVEN an expired or invalid authorization `code`
- WHEN GET /api/auth/callback?code=invalid_code is called
- THEN HTTP 401 is returned
- AND the body contains `{"detail": "Invalid or expired authorization code"}`

#### Scenario: Callback with missing code parameter

- GIVEN the API is running
- WHEN GET /api/auth/callback is called (no `code` query param)
- THEN HTTP 422 is returned (FastAPI query validation)

---

### Requirement: Logout (R6)

POST /api/auth/logout SHALL require a valid Bearer token in the Authorization header. SHALL invalidate the current Supabase session. SHALL return HTTP 200 on success and HTTP 401 if the token is missing or invalid.

#### Scenario: Successful logout with valid token

- GIVEN a valid Bearer token in the Authorization header
- WHEN POST /api/auth/logout is called
- THEN HTTP 200 is returned
- AND the body contains `{"message": "Logged out successfully"}`
- AND the session is invalidated in Supabase

#### Scenario: Logout without token

- GIVEN no Authorization header is present
- WHEN POST /api/auth/logout is called
- THEN HTTP 401 is returned
- AND the body contains `{"detail": "Not authenticated"}`

#### Scenario: Logout with expired token

- GIVEN an expired Bearer token
- WHEN POST /api/auth/logout is called
- THEN HTTP 401 is returned

---

### Requirement: Get Current User Profile (R7)

GET /api/auth/me SHALL require a valid Bearer token. SHALL return the authenticated user's profile: `id` (UUID), `email`, `full_name`, `avatar_url`, `preferred_language`, `preferred_theme`. Invalid or expired token SHALL return HTTP 401.

#### Scenario: Retrieve own profile with valid token

- GIVEN a valid Bearer token for user `abc-123` with email `alice@example.com`
- WHEN GET /api/auth/me is called
- THEN HTTP 200 is returned
- AND the body contains `id: "abc-123"`, `email: "alice@example.com"`, `full_name`, `avatar_url`, `preferred_language`, `preferred_theme`

#### Scenario: Retrieve profile with expired token

- GIVEN an expired Bearer token
- WHEN GET /api/auth/me is called
- THEN HTTP 401 is returned
- AND the body contains `{"detail": "Token expired"}`

#### Scenario: Retrieve profile without token

- GIVEN no Authorization header
- WHEN GET /api/auth/me is called
- THEN HTTP 401 is returned

---

### Requirement: Update User Profile (R8)

PUT /api/auth/me SHALL require a valid Bearer token. SHALL accept an optional subset of: `full_name` (string, max 100 chars), `preferred_language` (`"es"` or `"en"`), `preferred_theme` (`"light"` or `"dark"`). SHALL return HTTP 200 with the updated full profile. Invalid field values SHALL return HTTP 422.

#### Scenario: Update profile fields successfully

- GIVEN a valid Bearer token for user `abc-123`
- WHEN PUT /api/auth/me is called with `{"full_name": "Alice Johnson", "preferred_theme": "light"}`
- THEN HTTP 200 is returned
- AND the body contains `full_name: "Alice Johnson"` and `preferred_theme: "light"`
- AND unchanged fields (email, preferred_language) retain their existing values

#### Scenario: Update with invalid theme value

- GIVEN a valid Bearer token
- WHEN PUT /api/auth/me is called with `{"preferred_theme": "blue"}`
- THEN HTTP 422 is returned
- AND the body describes that `preferred_theme` must be `"light"` or `"dark"`

#### Scenario: Update without token

- GIVEN no Authorization header
- WHEN PUT /api/auth/me is called
- THEN HTTP 401 is returned

---

### Requirement: Token Refresh (R9)

POST /api/auth/refresh SHALL accept a `refresh_token` in the request body. SHALL return a new `access_token` and `refresh_token` (JWT strings) on success. Invalid or expired refresh token SHALL return HTTP 401.

#### Scenario: Successful token refresh

- GIVEN a valid `refresh_token` from a previous login or refresh
- WHEN POST /api/auth/refresh is called with `{"refresh_token": "<valid_refresh>"}`
- THEN HTTP 200 is returned
- AND the body contains a new `access_token` and `refresh_token`

#### Scenario: Refresh with invalid token

- GIVEN an expired or malformed `refresh_token`
- WHEN POST /api/auth/refresh is called with `{"refresh_token": "invalid"}`
- THEN HTTP 401 is returned
- AND the body contains `{"detail": "Invalid refresh token"}`

#### Scenario: Refresh with missing token

- GIVEN the API is running
- WHEN POST /api/auth/refresh is called with `{}` (no refresh_token)
- THEN HTTP 422 is returned

---

### Requirement: JWT Validation (R10)

The system SHALL validate Supabase-issued JWTs locally (no network call to Supabase per request) using the HS256 algorithm with `SUPABASE_JWT_SECRET`. SHALL extract `sub` (user UUID) and `email` from token claims. SHALL reject tokens with invalid signatures, expired tokens (`exp` in the past), and tokens with incorrect audience. SHALL enforce audience `"authenticated"`.

#### Scenario: Valid token is decoded and user claims extracted

- GIVEN a valid Supabase JWT with claims `{"sub": "abc-123", "email": "user@example.com", "aud": "authenticated", "exp": <future>}`
- WHEN `get_current_user()` validates and decodes the token
- THEN `user["id"]` SHALL be `"abc-123"`
- AND `user["email"]` SHALL be `"user@example.com"`

#### Scenario: Token with invalid signature is rejected

- GIVEN a JWT signed with a different secret (not `SUPABASE_JWT_SECRET`)
- WHEN `get_current_user()` validates the token
- THEN an `InvalidTokenError` SHALL be raised
- AND the HTTP response SHALL be 401 with `{"detail": "Invalid token"}`

#### Scenario: Expired token is rejected

- GIVEN a JWT with `exp` claim timestamp already in the past
- WHEN `get_current_user()` validates the token
- THEN an `ExpiredSignatureError` SHALL be raised
- AND the HTTP response SHALL be 401 with `{"detail": "Token expired"}`

#### Scenario: Token with wrong audience is rejected

- GIVEN a JWT with `aud` claim not equal to `"authenticated"`
- WHEN `get_current_user()` validates the token
- THEN an `InvalidTokenError` SHALL be raised
- AND the HTTP response SHALL be 401

#### Scenario: Validation is local (no network call)

- GIVEN the Supabase service is unreachable (network down)
- WHEN a request with a valid JWT is received
- THEN `get_current_user()` SHALL still successfully validate the token locally
- AND the request SHALL proceed normally
