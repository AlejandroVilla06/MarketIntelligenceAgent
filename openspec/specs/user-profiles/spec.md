# User Profiles Specification

## Purpose

User profile auto-creation via PostgreSQL trigger on Supabase `auth.users` INSERT, plus profile read/update through the `/api/auth/me` endpoint with Row-Level Security enforcing per-user access.

## Requirements

### Requirement: Profile Auto-Creation via Database Trigger (R1)

A user profile SHALL be automatically created when a new user signs up in Supabase Auth — handled by a PostgreSQL trigger (`on_auth_user_created`) that fires AFTER INSERT on `auth.users`. The profile row SHALL include: `id` (UUID PK, FK referencing `auth.users(id)` with ON DELETE CASCADE), `email`, `full_name` (nullable, populated from `raw_user_meta_data->>'full_name'`), `avatar_url` (nullable, populated from `raw_user_meta_data->>'avatar_url'`), `preferred_language` (default `'es'`), `preferred_theme` (default `'dark'`), `created_at`, and `updated_at`.

#### Scenario: Email/password signup creates profile

- GIVEN a new user signs up via email/password (no OAuth metadata)
- WHEN a row is inserted into `auth.users`
- THEN the `on_auth_user_created` trigger SHALL fire
- AND a new row SHALL appear in `public.profiles` with matching `id`, matching `email`, `full_name=NULL`, `avatar_url=NULL`
- AND `preferred_language` SHALL default to `'es'` and `preferred_theme` to `'dark'`

#### Scenario: OAuth signup populates full_name and avatar_url

- GIVEN a user signs up via Google OAuth with `raw_user_meta_data = {"full_name": "Alice Smith", "avatar_url": "https://lh3.googleusercontent.com/photo.jpg"}`
- WHEN a row is inserted into `auth.users`
- THEN the trigger SHALL create a profile with `full_name = "Alice Smith"` and `avatar_url = "https://lh3.googleusercontent.com/photo.jpg"`

#### Scenario: Profile deleted when user is deleted (CASCADE)

- GIVEN a user with an existing profile row
- WHEN the user is deleted from `auth.users`
- THEN the corresponding profile row SHALL be automatically deleted via ON DELETE CASCADE

#### Scenario: Trigger is SECURITY DEFINER — works regardless of caller

- GIVEN the `handle_new_user()` function is defined with `SECURITY DEFINER`
- WHEN any insert occurs on `auth.users` (regardless of the authenticated role)
- THEN the profile insertion SHALL succeed even if the calling role lacks INSERT permission on `public.profiles`

---

### Requirement: Profile CRUD via API (R2)

The `/api/auth/me` endpoint SHALL support reading (GET) and updating (PUT) the authenticated user's profile. PUT SHALL accept: `full_name` (string, nullable, max 100), `preferred_language` (`"es"` or `"en"`), `preferred_theme` (`"light"` or `"dark"`). Row-Level Security (RLS) policies SHALL enforce that users can only SELECT and UPDATE their own profile row (`auth.uid() = id`). Users SHALL NOT be able to read or modify other users' profiles, even via direct database access.

#### Scenario: GET /api/auth/me returns authenticated user's profile

- GIVEN user `abc-123` has a profile with `full_name = "Alice"` and `preferred_language = "es"`
- WHEN GET /api/auth/me is called with a valid Bearer token for user `abc-123`
- THEN HTTP 200 is returned with `id: "abc-123"`, `email`, `full_name: "Alice"`, `avatar_url`, `preferred_language: "es"`, `preferred_theme`

#### Scenario: PUT /api/auth/me updates profile fields

- GIVEN user `abc-123` has `full_name = "Alice"` and `preferred_theme = "dark"`
- WHEN PUT /api/auth/me is called with `{"full_name": "Alice Johnson", "preferred_theme": "light"}`
- THEN HTTP 200 is returned with the updated profile
- AND subsequent GET /api/auth/me SHALL reflect the changes

#### Scenario: RLS blocks cross-user profile access

- GIVEN user A's Bearer token
- WHEN user A attempts to query `public.profiles` where `id = <user_B_uuid>` via the Supabase client
- THEN the RLS SELECT policy (`auth.uid() = id`) SHALL return an empty result
- AND no profile data for user B is leaked

#### Scenario: update_at is refreshed on profile update

- GIVEN a profile row with an existing `updated_at` timestamp
- WHEN PUT /api/auth/me modifies any field
- THEN `updated_at` SHALL be set to the current timestamp (`NOW()`)

---

### Requirement: SQL Migration (R3)

The system SHALL provide a SQL migration file at `sql/init.sql` that creates the `profiles` table, the `handle_new_user` trigger function, the `on_auth_user_created` trigger, enables RLS on `public.profiles`, and creates SELECT and UPDATE policies scoped to `auth.uid() = id`. The migration SHALL be idempotent — safe to run multiple times — using `CREATE TABLE IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`, and `CREATE OR REPLACE TRIGGER`.

#### Scenario: Migration creates the expected schema

- GIVEN a Supabase project with no `public.profiles` table and no trigger
- WHEN `sql/init.sql` is executed in the Supabase SQL Editor
- THEN a `public.profiles` table SHALL exist with columns: `id`, `email`, `full_name`, `avatar_url`, `preferred_language`, `preferred_theme`, `created_at`, `updated_at`
- AND `id` SHALL be a UUID PRIMARY KEY with a FOREIGN KEY to `auth.users(id)` and ON DELETE CASCADE
- AND the `on_auth_user_created` trigger SHALL be bound to AFTER INSERT on `auth.users`
- AND RLS SHALL be enabled on `public.profiles`
- AND two policies SHALL exist: `"Users can view own profile"` (SELECT, `auth.uid() = id`) and `"Users can update own profile"` (UPDATE, `auth.uid() = id`)

#### Scenario: Migration is idempotent (safe to re-run)

- GIVEN the migration has already been applied to the database
- WHEN `sql/init.sql` is executed a second time
- THEN no errors SHALL occur
- AND the schema SHALL remain unchanged (no duplicate tables, triggers, or policies)

### SQL Reference

The following SQL SHALL be included in `sql/init.sql`:

```sql
-- Profiles table: extends auth.users with application-specific fields
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    preferred_language TEXT DEFAULT 'es',
    preferred_theme TEXT DEFAULT 'dark',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger function: auto-creates a profile row when a user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Bind trigger to auth.users INSERT
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Enable Row-Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: users can read only their own profile
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

-- RLS Policy: users can update only their own profile
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);
```