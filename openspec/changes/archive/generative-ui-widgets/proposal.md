# Proposal: Generative UI Widgets

## Intent

Transform chat from 100% text to generative UI — visual data widgets (price cards, macro indicators, tables, calculation results, sparklines) render inline with prose analysis. Sub-orchestrators emit `[WIDGET:type]{json}[/WIDGET]` markers; frontend parses and renders custom React/Tailwind components. Zero new npm dependencies.

## Scope

### In Scope
- Widget marker format `[WIDGET:type]{json}[/WIDGET]`
- Frontend parser with flicker-free streaming buffer
- CryptoPriceCard, MacroIndicator, DataTable, CalcResult, SparklineChart components
- WidgetRenderer router component
- Sub-orchestrator prompt injection for marker emission
- Streaming buffer in chatStore for incomplete markers
- Skeleton placeholders during streaming

### Out of Scope
- Interactive/clickable widgets (charts with hover/click)
- 3D visualizations or real-time price tickers
- Separate REST endpoints for widget data (Approach B from exploration)
- Third-party chart libraries (recharts, tremor)

## Capabilities

### New Capabilities
- `widget-rendering`: Frontend parser, WidgetRenderer, and all widget components (Crypto, Macro, Table, Calc, Sparkline). Marker extraction, JSON parsing, fallback rendering, skeleton loading.
- `widget-markers`: Backend marker format specification. Sub-orchestrator prompt templates for emitting `[WIDGET:type]{json}[/WIDGET]` markers in responses.

### Modified Capabilities
- `chat-streaming-client`: Add requirement for widget marker buffering — tokens containing incomplete `[WIDGET:` markers MUST be accumulated until `[/WIDGET]` closes or stream ends.
- `nextjs-frontend`: ChatMessage MUST parse widget markers and render visual components inline (not just react-markdown). SSE streaming MUST handle widget skeleton states.

## Approach

**Phase 1 — Parser + Crypto Widget:**
- `widgetParser.ts` with marker extraction and streaming buffer
- `WidgetRenderer.tsx` routing widget types to components
- `chatStore.ts` streaming buffer for incomplete markers
- `CryptoPriceCard.tsx` with price, 24h change, market cap
- `crypto_sub.py` prompt updated to emit `[WIDGET:crypto]` markers

**Phase 2 — Macro + Data Widgets:**
- `MacroIndicator.tsx` and `DataTable.tsx` components
- `macro_sub.py` prompt updated to emit `[WIDGET:macro]` and `[WIDGET:table]`

**Phase 3 — Calculation Widgets:**
- `CalcResult.tsx` component
- `python_repl.py` updated to emit `[WIDGET:calc]` markers

**Phase 4 — Sparkline + Polish:**
- Pure SVG `SparklineChart.tsx` (no library)
- Skeleton loading animations (same dimensions as final widget)
- Mobile responsive tweaks (<768px stack vertically)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/lib/widgetParser.ts` | New | Marker extraction + streaming buffer |
| `frontend/src/components/widgets/` | New | All widget components + renderer |
| `frontend/src/components/ChatMessage.tsx` | Modified | Parse segments, render widgets inline |
| `frontend/src/stores/chatStore.ts` | Modified | Streaming buffer for incomplete markers |
| `src/market_orchestrator/crypto_sub.py` | Modified | LLM prompt emits crypto markers |
| `src/market_orchestrator/macro_sub.py` | Modified | LLM prompt emits macro/table markers |
| `src/market_orchestrator/python_repl.py` | Modified | Wrap calc results in markers |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LLM emits invalid JSON | Medium | try-catch parsing, render raw `<code>` fallback |
| Streaming splits markers across chunks | High | Buffer accumulator, scan for `[WIDGET:` until `[/WIDGET]` |
| LLM ignores marker instructions | Medium | Text-only fallback (current behavior), prompt refinement |
| Widget flicker during streaming | High | Skeleton placeholder with same dimensions as final widget |
| Mobile layout breaks | Low | Responsive Tailwind, vertical stacking at <768px |

## Rollback Plan

Remove widget parser from `ChatMessage.tsx` — revert to pure react-markdown rendering. Widget components are isolated in `widgets/` directory with zero side effects. Backend markers render as plain text (no crash). No database or API changes needed.

## Dependencies

- None. Pure React/Tailwind/SVG. All frontend dependencies already exist (shadcn Card, Badge).

## Success Criteria

- [ ] Crypto widget renders visual card with price, change %, market cap
- [ ] Macro widget renders indicator with value and date
- [ ] DataTable renders tabular data with headers and rows
- [ ] Streaming NEVER shows half-parsed `[WIDGET:` markers
- [ ] Invalid markers render as raw text (no crash, no blank space)
- [ ] Skeleton placeholder displayed during streaming, replaced by widget seamlessly
- [ ] Widgets responsive: stack vertically at <768px