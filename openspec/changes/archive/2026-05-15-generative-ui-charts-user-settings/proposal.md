# Proposal: Generative UI Charts + User Settings

## Intent

Transform static widget visualizations (plain SVG sparklines, plain tables) into interactive TimeSeriesChart widgets powered by Recharts, and implement a user settings panel with account management, appearance controls (theme/language synced to Supabase), and a danger zone — eliminating the current theme flash on login by loading preferences from profile before rendering.

## Scope

### In Scope
- `recharts` integration via `frontend/package.json`
- `TimeSeriesChart.tsx` widget (Recharts `ResponsiveContainer` + `LineChart` + Tailwind theme colors)
- `[WIDGET:chart]` marker parsing in `WidgetRenderer.tsx`
- Enhanced `DataTable.tsx` with column sorting and pagination
- `/settings` page with Account, Appearance, and Danger Zone tabs
- `ThemeToggle.tsx` Supabase sync (PUT `/api/auth/me` on toggle)
- `authStore.ts` profile state extension (preferred_theme, preferred_language)
- `Providers.tsx` theme-from-profile flow with skeleton loading (no flash)
- `Header.tsx` settings gear icon linking to `/settings`
- Chart data types in `types.ts` (ChartData, TimeSeriesPoint, etc.)

### Out of Scope
- Per-user MCP API keys backend (UI placeholder only, endpoint deferred)
- Avatar upload (no file storage)
- Privacy/export section
- Real-time price tickers or 3D visualizations

## Capabilities

### New Capabilities
- `interactive-charts`: Recharts-based TimeSeriesChart widget with `[WIDGET:chart]` marker format, theme-aware colors, responsive container, tooltip, and legend. Includes ChartData types.
- `user-settings`: Settings page (Account tab: full name + email readonly + API Keys placeholder; Appearance tab: theme + language synced to Supabase; Danger Zone: logout destructive button). ThemeSyncFlow with skeleton loading during app mount.

### Modified Capabilities
- `widget-rendering`: WidgetRouter MUST route `chart` type to `TimeSeriesChart`. DataTable MUST support sorting and pagination. `widgetParser.ts` types MUST include ChartData shape.
- `nextjs-frontend`: Providers MUST fetch profile from Supabase before rendering (no flash). ThemeToggle MUST sync to Supabase profile. Header MUST link to `/settings`. R8 (Theme Toggle) changes from localStorage-only to Supabase-persisted with skeleton load guard.

## Approach

**Charts**: Add `recharts` dependency. Create `TimeSeriesChart.tsx` consuming `[WIDGET:chart]{type, data, xKey, yKey, title}[/WIDGET]` markers. Use `ResponsiveContainer` + Recharts primitives with Tailwind CSS variable colors (`hsl(var(--chart-1))` etc.) via pattern from shadcn/ui chart theming. Enhance `DataTable` with client-side column sort + pagination (10 rows/page). Update `WidgetRenderer` switch to include `chart` case. Add types to `widgetParser.ts`.

**Settings**: Create `/settings` route with tab layout (Account | Appearance | Danger Zone). Extending `authStore` with profile fields (`preferred_theme`, `preferred_language`, `full_name`) and `syncProfile()` action. `Providers.tsx` wraps children with a full-page skeleton until profile fetch resolves, then applies theme from profile data. `ThemeToggle` writes to both next-themes AND Supabase profile on change. `Header.tsx` adds `Settings` icon linking to `/settings`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/package.json` | Modified | Add `recharts` dependency |
| `frontend/src/components/widgets/TimeSeriesChart.tsx` | New | Recharts-based interactive chart widget |
| `frontend/src/components/widgets/WidgetRenderer.tsx` | Modified | Add `chart` case routing to TimeSeriesChart |
| `frontend/src/components/widgets/DataTable.tsx` | Modified | Column sorting + pagination controls |
| `frontend/src/lib/widgetParser.ts` | Modified | Add ChartData types to WidgetData |
| `frontend/src/app/settings/page.tsx` | New | Settings page with Account/Appearance/Danger Zone tabs |
| `frontend/src/components/ThemeToggle.tsx` | Modified | Sync theme to Supabase profile |
| `frontend/src/stores/authStore.ts` | Modified | Add profile fields + sync actions |
| `frontend/src/components/Providers.tsx` | Modified | Theme-from-profile + skeleton loading guard |
| `frontend/src/components/Header.tsx` | Modified | Add settings gear icon/link |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Theme flash on login (FOUC) | High | Skeleton overlay in Providers until profile resolves; `defaultTheme="dark"` fallback |
| Recharts bundle size (~200KB) | Medium | Tree-shake only used components (LineChart, Tooltip, ResponsiveContainer); Next.js dynamic import |
| Widget marker JSON schema mismatch (chart data) | Medium | Schema validation in `parseMessage()`; fallback to raw text on invalid JSON |
| Supabase profile fetch slow/blocking | Low | 3-second timeout → default to dark theme; non-blocking render flow |
| Settings page accessible when logged out | Low | Next.js middleware already redirects unauthenticated users |

## Rollback Plan

- Remove `recharts` from `package.json` and delete `TimeSeriesChart.tsx`
- Revert `WidgetRenderer.tsx` switch to remove `chart` case (raw text fallback already handles unknown types gracefully)
- Remove `/settings` route — no backend changes needed (profiles endpoint already exists)
- Revert `Providers.tsx` to original ThemeProvider — `defaultTheme="dark"` works without Supabase sync
- `WidgetRenderer` already renders `Unknown widget: chart` for unregistered types, so no crash on rollback

## Dependencies

- `recharts` npm package (MIT license, ~200KB gzipped)
- Existing `GET/PUT /api/auth/me` endpoint (already functional per `user-profiles` spec)
- `next-themes` (already installed)

## Success Criteria

- [ ] TimeSeriesChart renders line charts with Tailwind theme colors (dark/light)
- [ ] TimeSeriesChart is responsive (mobile <640px to desktop ≥1280px)
- [ ] `[WIDGET:chart]` markers parsed correctly during streaming (no half-rendered markers)
- [ ] DataTable supports column sorting and pagination (10 rows/page)
- [ ] Settings page renders Account, Appearance, and Danger Zone tabs
- [ ] Theme change persists across login sessions (Supabase profile)
- [ ] Login shows full-page skeleton until theme loads (no flash)
- [ ] Language change persists to Supabase profile
- [ ] Account section has placeholder for future API Keys (disabled UI)
- [ ] Build passes (`npm run build` exits 0)