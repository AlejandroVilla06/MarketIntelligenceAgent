# Delta for nextjs-frontend

## ADDED Requirements

### Requirement: Header Settings Navigation

The Header component SHALL include a settings gear icon (cog/link) navigating to `/settings`. The icon SHALL use `lucide-react` `Settings` icon. The icon SHALL be visible on all screen sizes (mobile through desktop). On mobile (<1024px), the settings icon SHALL remain visible alongside the existing hamburger and clock triggers.

#### Scenario: Settings icon visible on desktop

- GIVEN viewport ≥ 1280px and user at `/chat`
- WHEN the Header renders
- THEN a gear/cog icon is visible
- AND clicking it navigates to `/settings`

#### Scenario: Settings icon visible on mobile

- GIVEN viewport < 768px and user at `/chat`
- WHEN the Header renders
- THEN the gear icon is visible alongside hamburger and clock icons
- AND it is touch-friendly (min 44px tap target)

#### Scenario: Settings icon is hidden when already on settings page

- GIVEN user is on `/settings`
- WHEN the Header renders
- THEN the settings icon MAY be hidden or replaced with a back arrow

### Requirement: Providers Theme Initialization

`Providers.tsx` SHALL fetch the user profile from Supabase (via `GET /api/auth/me`) on mount before rendering children. While fetching, a full-page skeleton using shadcn `<Skeleton>` SHALL occupy the viewport. After profile resolves, the `preferred_theme` field SHALL be passed to `<ThemeProvider>` as `defaultTheme` (overriding the static `"dark"` default). If the fetch fails or times out after 3 seconds, the skeleton SHALL be dismissed and theme SHALL fall back to `"dark"`. This prevents FOUC (Flash of Unstyled Content) on login.

#### Scenario: Profile available, theme applied before render

- GIVEN authenticated user with `preferred_theme: "light"`
- WHEN the app mounts
- THEN a full-page skeleton is visible (viewport height/width)
- AND profile fetch completes with `preferred_theme: "light"`
- THEN `<ThemeProvider>` receives `defaultTheme="light"`
- AND the skeleton is replaced by the rendered app in light mode
- AND no dark-mode flash occurs during the transition

#### Scenario: Profile fetch fails, fallback to dark

- GIVEN the profile fetch throws a network error
- WHEN the app mounts
- THEN the skeleton renders for up to 3 seconds
- THEN `<ThemeProvider>` receives `defaultTheme="dark"`
- AND the skeleton is dismissed
- AND the app renders in dark mode successfully (no crash, no white screen)

#### Scenario: Profile fetch times out

- GIVEN the profile fetch does not resolve
- WHEN 3 seconds elapse since mount
- THEN the fetch is aborted (AbortController)
- AND `<ThemeProvider>` receives `defaultTheme="dark"`
- AND the skeleton is dismissed

#### Scenario: Unauthenticated user (no session)

- GIVEN no Supabase session exists
- WHEN the app mounts
- THEN no profile fetch is attempted
- AND `<ThemeProvider>` receives `defaultTheme="dark"`
- AND the app renders immediately with no skeleton

## MODIFIED Requirements

### Requirement: Theme Toggle (R8)

The system SHALL provide a dark/light theme toggle via `next-themes`. On toggle, the system SHALL persist the new theme BOTH to `next-themes` (for immediate UI update) AND to the Supabase profile via `PUT /api/auth/me` with `preferred_theme`. On next app mount, the theme SHALL be loaded from the Supabase profile (not localStorage), following the Providers Theme Initialization flow. The default theme SHALL be `"dark"`.

(Previously: Theme persisted in localStorage only. No Supabase sync. No skeleton loading guard.)

#### Scenario: Theme toggle persists to Supabase

- GIVEN dark mode is active
- WHEN user clicks the theme toggle
- THEN UI switches to light mode via `next-themes`
- AND `PUT /api/auth/me` is called with `{ preferred_theme: "light" }`

#### Scenario: Theme survives logout and re-login

- GIVEN user set `preferred_theme: "light"` and logged out
- WHEN user logs in again
- THEN the Providers skeleton shows while profile loads
- AND after profile resolves, the app renders in light mode
- AND no dark-mode flash occurs

#### Scenario: Theme toggle fallback on API failure

- GIVEN `PUT /api/auth/me` fails during theme toggle
- WHEN the user toggles the theme
- THEN the UI still switches visually via `next-themes` (optimistic update)
- AND an error toast notifies the user that persistence failed
- AND on next app mount, the previous profile theme is loaded (not the failed toggle)
