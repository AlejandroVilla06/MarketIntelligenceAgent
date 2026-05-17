# user-settings Specification

## Purpose

Settings page with Account management (profile fields + future MCP API keys placeholder), Appearance controls (theme and language synced to Supabase profiles), and a Danger Zone with logout. Theme sync flow prevents FOUC (Flash of Unstyled Content) on login by loading user preferences from Supabase before rendering the UI.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **Settings Page Structure**: The system SHALL provide a `/settings` page accessible via a gear icon in the Header. The page SHALL render a Tab layout using shadcn `<Tabs>` with: **Account** and **Appearance** tabs. Each tab SHALL be wrapped in a `<Card>` with a header showing the tab name. Unauthenticated access SHALL redirect to `/login` via existing middleware. |
| R2 | **Account Tab**: The Account tab SHALL display the user's email as a read-only `<Input disabled>` field. SHALL allow editing `full_name` via a text input with a "Save" button. SHALL include a placeholder section titled "API Keys (MCP)" with disabled inputs and a muted description: "Connect external data sources — coming soon." Saving changes SHALL call `PUT /api/auth/me` with `full_name`. On success, SHALL show a toast confirmation. On failure, SHALL show an inline error message. |
| R3 | **Appearance Tab**: The Appearance tab SHALL have a dark/light theme toggle (shadcn `<Switch>` or segmented control). Changing theme SHALL call `api.profile.update({ preferred_theme })` via `PUT /api/auth/me` AND toggle `next-themes`. SHALL have a language selector (dropdown with ES/EN options). Changing language SHALL call `api.profile.update({ preferred_language })`. Current values SHALL be pre-selected from the loaded profile. |
| R4 | **Danger Zone**: The Danger Zone section SHALL appear at the bottom of the settings page, visually separated with a red-tinted border and heading. SHALL contain a "Cerrar sesión" button with `variant="destructive"`. Clicking logout SHALL call `supabase.auth.signOut()` and redirect to `/login`. SHALL show a confirmation dialog before proceeding ("¿Estás seguro de que querés cerrar sesión?"). |
| R5 | **Theme Sync Flow**: On app mount, `Providers.tsx` SHALL render a full-page skeleton (using shadcn `<Skeleton>`) while fetching the user profile from Supabase via `GET /api/auth/me`. After profile loads, the fetched `preferred_theme` SHALL be applied to `<ThemeProvider>`. If profile fetch fails (network error, 401), the system SHALL fall back to `"dark"` theme. After theme application, the skeleton SHALL be replaced by the full app UI. This flow SHALL prevent FOUC on login by blocking render until the correct theme is known. A 3-second timeout SHALL be enforced on the profile fetch to prevent infinite loading. |

## Scenarios

### R1: Settings Page Structure

- GIVEN an authenticated user at `/chat`
- WHEN user clicks the gear icon in the Header
- THEN the browser navigates to `/settings`
- AND the page shows Account and Appearance tabs in a Card layout
- AND the Account tab is selected by default

- GIVEN an unauthenticated browser session
- WHEN navigating to `/settings`
- THEN redirected to `/login` by existing middleware

- GIVEN viewport width is 375px
- WHEN `/settings` page renders
- THEN tabs are fully visible and horizontally scrollable
- AND all form controls are touch-friendly (min 44px tap target)

### R2: Account Tab

- GIVEN user `alice@example.com` with `full_name` "Alice"
- WHEN the Account tab renders
- THEN email field shows "alice@example.com" (disabled, read-only)
- AND full_name field shows "Alice" (editable)

- GIVEN user edits full_name to "Alice Johnson" and clicks Save
- WHEN `PUT /api/auth/me` returns 200
- THEN a toast reads "Perfil actualizado"
- AND the input reflects "Alice Johnson"

- GIVEN `PUT /api/auth/me` returns 500
- WHEN user clicks Save
- THEN an inline error "Error al guardar. Intenta de nuevo." appears below the form
- AND the previous full_name value is preserved in the input

- GIVEN the Account tab renders
- WHEN the "API Keys (MCP)" section is visible
- THEN it displays disabled input fields and muted text "Connect external data sources — coming soon"
- AND no interaction is possible with these controls

### R3: Appearance Tab

- GIVEN user profile has `preferred_theme: "dark"`
- WHEN Appearance tab renders
- THEN theme toggle shows "dark" as active

- GIVEN user toggles theme to "light"
- WHEN `PUT /api/auth/me` succeeds
- THEN the UI switches to light mode immediately
- AND the profile is persisted with `preferred_theme: "light"`
- AND on next login, the theme loads as light automatically

- GIVEN user selects "English" from the language dropdown
- WHEN `PUT /api/auth/me` succeeds
- THEN the UI language switches to English
- AND `preferred_language: "en"` is persisted

- GIVEN `PUT /api/auth/me` fails on theme toggle
- WHEN the request returns a network error
- THEN the toggle reverts to the previous theme state
- AND an error toast appears

### R4: Danger Zone

- GIVEN user scrolls to the Danger Zone section
- WHEN the "Cerrar sesión" button is visible
- THEN it has a red/destructive styling (variant="destructive")
- AND the section is visually separated with a red-tinted border

- GIVEN user clicks "Cerrar sesión"
- WHEN the confirmation dialog appears
- THEN it asks "¿Estás seguro de que querés cerrar sesión?" with "Cancelar" and "Cerrar sesión" buttons

- GIVEN user confirms logout
- WHEN `supabase.auth.signOut()` completes
- THEN browser redirects to `/login`
- AND the session is cleared (no auto-login on refresh)

### R5: Theme Sync Flow

- GIVEN user with `preferred_theme: "light"` logs in
- WHEN the app mounts in `Providers.tsx`
- THEN a full-page skeleton is displayed immediately
- AND `GET /api/auth/me` is called in the background
- AND on receiving `preferred_theme: "light"`, ThemeProvider applies "light"
- AND the skeleton is removed, revealing the app in light mode
- AND no flash of dark-mode styling occurs

- GIVEN profile fetch exceeds 3 seconds
- WHEN the timeout fires
- THEN theme defaults to "dark"
- AND the skeleton is removed
- AND the app renders in dark mode

- GIVEN profile fetch fails with a network error
- WHEN the fetch rejects
- THEN theme falls back to "dark"
- AND the skeleton is removed
- AND the app renders successfully in dark mode (no white screen, no crash)

- GIVEN user has no `preferred_theme` set (legacy profile)
- WHEN profile fetch returns `preferred_theme: null`
- THEN theme defaults to "dark"