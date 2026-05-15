# Design: Generative UI Charts + User Settings

## Technical Approach

Add `recharts` (tree-shaken via `dynamic(() => import(...), { ssr: false })`) for interactive `TimeSeriesChart` widgets consumed through `[WIDGET:chart]` markers — extending the existing `WidgetRenderer` switch with a `chart` case following the same `data?`/`isLoading?` contract as `CryptoPriceCard` and `CalcResult`. Enhance `DataTable` with client-side column sort + pagination (10 rows/page).

Build `/settings` page using shadcn `Tabs` (requires `npx shadcn@latest add tabs switch select label separator`). Theme sync flow: `Providers.tsx` shows full-page skeleton while fetching profile from `/api/auth/me` (already implemented in `api.ts`) → applies `preferred_theme` → removes skeleton. `ThemeToggle` calls `api.profile.update({ preferred_theme })` on every toggle. Extend `authStore` with `profile` fields + `syncProfile()` action.

## Architecture Decisions

| Decision | Choice | Rejected | Why |
|----------|--------|----------|-----|
| **Chart library** | Recharts v2 (`ResponsiveContainer` + `LineChart`) | D3.js (too heavy, ~500KB), Chart.js (limited React integration), Nivo (unnecessary for line/area) | Tree-shakes to ~150KB gzipped; shadcn/ui charts use it; `dynamic()` import eliminates SSR issues |
| **Chart SSR strategy** | `dynamic(() => import("./TimeSeriesChart"), { ssr: false })` in `WidgetRenderer` | `typeof window` check, manual `useEffect` mount | Next.js idiomatic pattern; avoids hydration mismatch; already in codebase conventions |
| **Theme restore flow** | Skeleton overlay in `Providers` during fetch, then render with resolved theme | CSS `visibility: hidden` on `<html>` until JS runs | Skeleton gives explicit visual feedback; covers FOUC entirely; aligns with existing skeleton patterns |
| **Settings tabs** | shadcn `Tabs` (`@radix-ui/react-tabs`) | Custom `useState` with conditional rendering, Next.js parallel routes | Already in shadcn ecosystem; accessible (keyboard nav, ARIA); consistent with existing `DropdownMenu`, `Sheet`, `Card` usage |
| **Language selector** | shadcn `Select` with `es`/`en` options | Custom dropdown, radio group | Consistent UI with remaining shadcn components; `Select` uses Radix accessible primitives |
| **API keys UX** | Disabled `Input` placeholders + `Badge variant="secondary"` with "Proximamente" | Full form with fake submit, hidden section | Honest about readiness; zero backend overhead; trivial to activate later |
| **Column sort** | Client-side `useState` + `Array.sort()` on column click | Server-side sorting via API query params | DataTable renders ≤100 rows (backed by LLM responses); client-side sorting is instant and adequate |
| **Pagination** | Client-side `useState` slice with prev/next buttons (10 rows/page) | Infinite scroll, `react-window` virtualization | Simple, accessible; no new dependency; 10 rows/page matches mobile-friendly design |

## Data Flow: Theme Sync

```
User logs in
  → layout.tsx renders <Providers>
  → Providers.tsx: useState("theme", null)
  → Skeleton full-page shown (3 skeletons: heading, text, block)
  → useEffect fires:
      createClient() → supabase.auth.getSession()
      → if session: fetch(`${API_URL}/api/auth/me`, Bearer token)
      → if ok: setTheme(profile.preferred_theme || "dark")
      → if fail/3s timeout: setTheme("dark")
  → theme !== null → <ThemeProvider attribute="class" defaultTheme={theme} enableSystem={false}>
  → Children render with resolved theme (no FOUC)

User toggles theme
  → ThemeToggle.tsx: setTheme(newTheme)
  → next-themes updates <html class="dark|light">
  → ThemeToggle.tsx: api.profile.update({ preferred_theme: newTheme })
  → PUT /api/auth/me → Supabase profiles table updated
  → On failure: silent (user already sees correct theme)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Modify | Add `recharts: "^2.x"` |
| `frontend/src/components/widgets/TimeSeriesChart.tsx` | Create | Recharts `LineChart`/`AreaChart` with `ResponsiveContainer`, Tooltip, Legend; `useThemeColors()` hook for CSS variable colors |
| `frontend/src/components/widgets/WidgetRenderer.tsx` | Modify | Add `case "chart":` → dynamic import of `TimeSeriesChart` |
| `frontend/src/components/widgets/DataTable.tsx` | Modify | Add `sortColumn`/`sortDir` state, `handleSort(col)`, `page` state, prev/next buttons, `slice()` rows |
| `frontend/src/lib/widgetParser.ts` | Modify | Add `ChartDataPoint` type to `WidgetData.data` union (no parser changes — JSON.parse already handles arbitrary shapes) |
| `frontend/src/app/settings/page.tsx` | Create | Client component with `Tabs` (Account | Appearance | Danger Zone); `Card` wrappers per tab |
| `frontend/src/hooks/useThemeColors.ts` | Create | `getComputedStyle(document.documentElement)` → `{ primary, muted, background }` |
| `frontend/src/components/ThemeToggle.tsx` | Modify | Add `api.profile.update({ preferred_theme })` after `setTheme()` |
| `frontend/src/stores/authStore.ts` | Modify | Add `profile: { full_name, preferred_theme, preferred_language }`, `setProfile()`, `syncProfile()` |
| `frontend/src/components/Providers.tsx` | Modify | Add `useState(theme)`, `useEffect` fetch profile, skeleton render while `theme === null` |
| `frontend/src/components/Header.tsx` | Modify | Add `<Link href="/settings">` + `Settings` icon from lucide-react (gear) |

## Interfaces

```typescript
// TimeSeriesChart props (follows existing widget contract)
interface ChartDataPoint { [key: string]: string | number }
interface TimeSeriesChartProps {
  data: ChartDataPoint[];   // required (no null render)
  xKey: string;
  yKey: string;
  title?: string;
  type?: "line" | "area";
  color?: string;
  isLoading?: boolean;       // skeleton pattern consistent with other widgets
}

// Settings forms
interface AccountForm { full_name: string; email: string }
interface AppearanceForm { preferred_theme: "dark" | "light"; preferred_language: "es" | "en" }

// authStore extension
interface AuthState {
  user: User | null;
  loading: boolean;
  profile: { full_name?: string; preferred_theme?: string; preferred_language?: string } | null;
  setUser: (user: User | null) => void;
  setProfile: (profile: AuthState["profile"]) => void;
  syncProfile: () => Promise<void>;  // calls api.profile.get() → setProfile()
}
```

## New shadcn Components Required

Run: `npx shadcn@latest add tabs switch select label separator`

| Component | Where Used |
|-----------|------------|
| `tabs` | Settings page tab navigation |
| `switch` | Appearance → Theme toggle (dark/light) |
| `select` | Appearance → Language dropdown (ES/EN) |
| `label` | Settings form fields (`full_name`, `email`) |
| `separator` | Danger Zone section divider |

## Testing Strategy

| Layer | Test | Approach |
|-------|------|----------|
| Unit | `parseMessage()` handles `[WIDGET:chart]` | Jest + existing parser test pattern — add chart JSON case |
| Unit | `TimeSeriesChart` empty data renders fallback | React Testing Library — render with `data=[]`, assert "No data" |
| Unit | `DataTable` column sort toggles direction | RTL — click column header, assert row order changes |
| Integration | Theme toggle persists to Supabase | Mock `api.profile.update()`, assert called with `{ preferred_theme: "light" }` |
| Integration | Settings page saves `full_name` | Mock `api.profile.update()`, type in field, click Save, assert API call |
| Integration | Danger Zone logout redirects to `/login` | Mock `supabase.auth.signOut()`, click logout, assert `router.push("/login")` |
| Visual | Skeleton shown during theme load | Mock fetch with 500ms delay, assert `Skeleton` components rendered |

## Open Questions

- [ ] Should chart colors use shadcn chart CSS variables (`--chart-1` through `--chart-5`) or the widget's `color` field from the marker? **Decision needed**: widget `color` field for LLM control, CSS variables as fallback.
- [ ] Language sync to backend: does the backend currently use `preferred_language` for response language? Or is it purely UI chrome? (Currently the agent detects language from query text — `preferred_language` could select UI language only.)
