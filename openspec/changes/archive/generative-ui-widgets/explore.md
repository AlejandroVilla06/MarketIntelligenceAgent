# Exploration: Generative UI Widgets

## Current State

### Data Flow (Today)
```
User Query → RouterAgent → SubOrchestrator → MCP Server (raw data)
                                      ↓
                              LLM formats as prose
                                      ↓
                              SSE stream (word-by-word)
                                      ↓
                              ChatMessage.tsx → react-markdown (plain text)
```

### What Sub-Orchestrators Return

**CryptoSubOrchestrator** (`src/agents/mcp/crypto_server.py`):
- `get_crypto_price("BTC")` → formatted text:
  ```
  CRYPTO DATA — Bitcoin (BTC)
  Precio: $81,372.18 USD
  Capitalización: $1,612,345,678,901
  Volumen 24h: $28,456,789,012
  Cambio 24h: +2.34%
  Cambio 7d: -1.23%
  Supply circulante: 19,800,000
  Market cap rank: #1
  Fuente: CoinMarketCap (tiempo real)
  ```
- `get_top_cryptos(10)` → table-like text with aligned columns
- `get_crypto_global_metrics()` → global market metrics text

**MacroSubOrchestrator** (`src/agents/mcp/macro_server.py`):
- `get_gdp()`, `get_cpi()`, etc. → FRED observations:
  ```
  US Gross Domestic Product:
    2025-01-01: 28271.844
    2024-10-01: 27957.448
  ```
- `get_macro_summary()` → combined multi-indicator text

**CalculationExecutor** (`src/market_orchestrator/python_repl.py`):
- `calculate_python(code)` → stdout capture (print statements)
- Returns structured results like:
  ```
  Present value of cash flows: $379.08
  Initial investment: $400.00
  NPV: $-20.92
  => Negative NPV: Project destroys value ❌
  ```

### Current Frontend Components

| Component | File | Role |
|-----------|------|------|
| `ChatMessage.tsx` | `frontend/src/components/ChatMessage.tsx` | Renders markdown via react-markdown |
| `MessageList.tsx` | `frontend/src/components/MessageList.tsx` | List of messages with auto-scroll |
| `chatStore.ts` | `frontend/src/stores/chatStore.ts` | Zustand store for messages/streaming |
| `api.ts` | `frontend/src/lib/api.ts` | SSE streaming client |

### Available shadcn/ui Components
- `Card`, `CardHeader`, `CardContent`, `CardTitle`, `CardDescription`, `CardFooter`
- `Button` (with variants: default, outline, secondary, ghost, destructive, link)
- `Badge` (not yet installed but shadcn available)
- `Dialog`, `DropdownMenu`, `Input`, `Sheet`

### Streaming Behavior
- Backend: `ask_stream()` splits response by spaces → word-by-word SSE
- Frontend: `appendStreamToken()` concatenates tokens in Zustand store
- Final: `addMessage()` stores complete content, `resetStreaming()` clears buffer

---

## Affected Areas

- `src/agents/mcp/crypto_server.py` — must return structured data + text
- `src/agents/mcp/macro_server.py` — must return structured data + text
- `src/market_orchestrator/crypto_sub.py` — must pass structured markers to LLM prompt
- `src/market_orchestrator/macro_sub.py` — must pass structured markers to LLM prompt
- `src/market_orchestrator/python_repl.py` — must structure calculation results
- `src/market_orchestrator/orchestrator.py` — may need `ask_stream()` changes
- `frontend/src/components/ChatMessage.tsx` — must parse markers and render widgets
- `frontend/src/components/widgets/` — NEW: widget components directory
- `frontend/src/lib/widgetParser.ts` — NEW: marker extraction utility
- `frontend/src/lib/types.ts` — add widget type definitions

---

## Approaches

### Approach A: Widget Markers in LLM Response (Recommended)

The LLM is instructed to emit structured markers in its response. The frontend parses them and renders custom React components.

**Marker Format:**
```
[WIDGET:crypto]{"symbol":"BTC","price":81372.18,"change24h":2.34,"marketCap":1.612e12}[/WIDGET]
[WIDGET:macro]{"indicator":"GDP","value":28271.844,"date":"2025-01-01","previous":27957.448}[/WIDGET]
[WIDGET:calc]{"formula":"NPV","inputs":{"rate":"10%","cashFlows":"$100 x 5"},"result":"-$20.92","verdict":"negative"}[/WIDGET]
[WIDGET:table]{"headers":["Rank","Name","Price","24h"],"rows":[["1","Bitcoin","$81,372","+2.3%"],...]}[/WIDGET]
```

**How it works:**
1. MCP servers return raw JSON + formatted text (dual output)
2. Sub-orchestrator LLM prompt includes instructions to emit widget markers
3. Frontend parser extracts markers from streamed content
4. `ChatMessage.tsx` splits content into text segments and widget segments
5. Text segments → react-markdown, Widget segments → custom components

**Pros:**
- Minimal backend changes (only prompt modification)
- Works with existing streaming infrastructure
- Widgets are part of the message content (persistent, scrollable)
- Can coexist with prose analysis

**Cons:**
- LLM must be reliable at emitting valid JSON (needs error handling)
- Streaming: must buffer until marker is complete before rendering widget
- Marker format must be escaped in code blocks

**Effort: Medium**

### Approach B: Structured API Endpoints (Not Recommended)

Separate endpoints return JSON data. Frontend fetches independently and renders widgets outside the chat.

**Pros:**
- Clean separation of concerns
- No LLM reliability concerns

**Cons:**
- Breaks the chat-first UX (widgets feel disconnected)
- Requires new API endpoints for each data type
- Doubles the API calls (chat + data fetch)
- Conversation context lost for widget data
- Significant backend + frontend changes

**Effort: High**

### Approach C: Hybrid — Markers + Fallback (Future Enhancement)

Combine Approach A with a fallback: if the LLM fails to emit markers, the backend sends a separate structured payload alongside the text.

**Pros:**
- Best of both worlds
- Graceful degradation

**Cons:**
- More complex implementation
- Can be added later as an enhancement

**Effort: High (defer to Phase 2)**

---

## Recommendation

**Approach A: Widget Markers in LLM Response**

This is the right approach because:
1. **Minimal disruption** — only prompt changes on backend, parser + components on frontend
2. **Works with streaming** — buffer tokens until `[/WIDGET]` is detected, then render
3. **Natural UX** — widgets appear inline with the analysis text
4. **Incremental** — can implement one widget type at a time (crypto first, then macro, then calc)

### Widget Marker Specification

**Format:** `[WIDGET:type]{json}[/WIDGET]`

**Supported types:**
| Type | JSON Schema | Component |
|------|-------------|-----------|
| `crypto` | `{symbol, name, price, change24h, change7d, marketCap, volume24h, rank}` | `CryptoWidget` |
| `macro` | `{indicator, value, date, previous, unit, source}` | `MacroWidget` |
| `table` | `{headers: string[], rows: string[][]}` | `DataTableWidget` |
| `calc` | `{formula, inputs: Record<string,string>, result, verdict, interpretation}` | `CalcWidget` |
| `sparkline` | `{symbol, prices: number[], label}` | `SparklineWidget` |

**Error handling:** If JSON parsing fails, render the raw marker as `<code>` with a warning badge.

### Streaming Strategy

```
Token stream: "Bitcoin ... [WIDGET:crypto]{...}[/WIDGET] ... analysis continues"
                    ↓                                    ↓
              Buffer tokens                    Widget detected!
              (no widget yet)                  Parse JSON → render component
                                               Continue with remaining text
```

Implementation:
1. `widgetParser.ts` extracts all `[WIDGET:type]{json}[/WIDGET]` from content
2. Returns array of `{type: 'text' | 'widget', content: string | WidgetData}`
3. `ChatMessage.tsx` maps segments: text → `<ReactMarkdown>`, widget → `<WidgetRenderer>`
4. During streaming: buffer incomplete markers (no closing `[/WIDGET]` yet)

---

## Component Tree

```
ChatMessage
├── ReactMarkdown (for text segments)
└── WidgetRenderer (for widget segments)
    ├── CryptoWidget
    │   ├── Price display (large, bold)
    │   ├── 24h change badge (green/red)
    │   ├── Market cap + volume
    │   └── Rank badge
    ├── MacroWidget
    │   ├── Indicator name + value
    │   ├── Change arrow (↑/↓)
    │   └── Date + source
    ├── DataTableWidget
    │   ├── Header row
    │   └── Body rows (scrollable)
    ├── CalcWidget
    │   ├── Formula name
    │   ├── Inputs display
    │   ├── Result (highlighted)
    │   └── Verdict badge
    └── SparklineWidget
        └── SVG mini-chart (pure CSS/SVG, no lib)
```

### Props Interfaces

```typescript
// frontend/src/lib/types/widgets.ts

interface CryptoWidgetData {
  type: 'crypto'
  symbol: string          // "BTC"
  name?: string           // "Bitcoin"
  price: number           // 81372.18
  change24h: number       // 2.34 (percent)
  change7d?: number       // -1.23
  marketCap?: number      // 1612345678901
  volume24h?: number      // 28456789012
  rank?: number           // 1
}

interface MacroWidgetData {
  type: 'macro'
  indicator: string       // "GDP"
  value: number           // 28271.844
  date: string            // "2025-01-01"
  previous?: number       // 27957.448
  unit?: string           // "Billions USD"
  source?: string         // "FRED"
}

interface TableWidgetData {
  type: 'table'
  headers: string[]       // ["Rank", "Name", "Price"]
  rows: string[][]        // [["1", "Bitcoin", "$81,372"]]
}

interface CalcWidgetData {
  type: 'calc'
  formula: string         // "NPV"
  inputs: Record<string, string>  // {"rate": "10%", "cashFlows": "$100 x 5"}
  result: string          // "-$20.92"
  verdict?: string        // "negative"
  interpretation?: string // "Project destroys value"
}

interface SparklineWidgetData {
  type: 'sparkline'
  symbol: string          // "BTC"
  prices: number[]        // [81000, 81200, 81372, ...]
  label?: string          // "7-day price"
}

type WidgetData = CryptoWidgetData | MacroWidgetData | TableWidgetData 
                | CalcWidgetData | SparklineWidgetData

interface ParsedSegment {
  type: 'text' | 'widget'
  content: string | WidgetData
}
```

---

## Files to Create/Modify

### Backend (Python)

| File | Change | Description |
|------|--------|-------------|
| `src/agents/mcp/crypto_server.py` | MODIFY | Add `get_crypto_price_json()` returning `dict` alongside text |
| `src/agents/mcp/macro_server.py` | MODIFY | Add `_fetch_series_json()` returning structured data |
| `src/market_orchestrator/crypto_sub.py` | MODIFY | Update LLM prompt to emit `[WIDGET:crypto]` markers |
| `src/market_orchestrator/macro_sub.py` | MODIFY | Update LLM prompt to emit `[WIDGET:macro]` markers |
| `src/market_orchestrator/python_repl.py` | MODIFY | Wrap results in `[WIDGET:calc]` markers |

### Frontend (TypeScript/React)

| File | Change | Description |
|------|--------|-------------|
| `frontend/src/lib/types/widgets.ts` | CREATE | Widget data type definitions |
| `frontend/src/lib/widgetParser.ts` | CREATE | Extract widgets from message content |
| `frontend/src/components/widgets/CryptoWidget.tsx` | CREATE | Crypto price card |
| `frontend/src/components/widgets/MacroWidget.tsx` | CREATE | Macro indicator card |
| `frontend/src/components/widgets/DataTableWidget.tsx` | CREATE | Generic table |
| `frontend/src/components/widgets/CalcWidget.tsx` | CREATE | Calculation result |
| `frontend/src/components/widgets/SparklineWidget.tsx` | CREATE | SVG mini-chart |
| `frontend/src/components/widgets/WidgetRenderer.tsx` | CREATE | Routes widget type to component |
| `frontend/src/components/widgets/index.ts` | CREATE | Barrel export |
| `frontend/src/components/ChatMessage.tsx` | MODIFY | Parse markers, render widgets inline |
| `frontend/src/components/MessageList.tsx` | MODIFY | Handle streaming widget buffer |
| `frontend/src/stores/chatStore.ts` | MODIFY | Add widget buffer state for streaming |

### New Dependencies (Frontend)

**None required.** Sparklines can be done with pure SVG. All other widgets use existing Tailwind + shadcn Card components.

Optional future additions:
- `recharts` or `@tremor/react` for richer charts (defer)
- `@tanstack-table` for sortable tables (defer)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM emits invalid JSON in markers | Widget fails to render | Try-catch parsing, render raw text with error badge, log for debugging |
| Streaming splits marker across tokens | Widget not detected until complete | Buffer tokens containing `[WIDGET` until `[/WIDGET]` is found |
| LLM ignores marker instructions | No widgets rendered | Fallback: text-only rendering (current behavior), refine prompt iteratively |
| Marker conflicts with markdown code blocks | False positives | Use unique delimiters `[WIDGET:type]` that won't appear in prose |
| Mobile layout breaks with wide widgets | Bad UX on small screens | Use responsive Tailwind classes, max-width constraints, horizontal scroll for tables |
| Performance with many widgets in long chat | Slow re-renders | Memoize widget components, virtualize message list if needed |

---

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)
1. Create `widgetParser.ts` with marker extraction
2. Create `WidgetRenderer.tsx` as routing component
3. Modify `ChatMessage.tsx` to use parser + renderer
4. Add widget type definitions

### Phase 2: First Widget (Crypto)
1. Create `CryptoWidget.tsx` with price card design
2. Update `crypto_server.py` to include structured data in output
3. Update `crypto_sub.py` LLM prompt to emit markers
4. Test end-to-end with BTC price query

### Phase 3: Additional Widgets
1. `MacroWidget.tsx` — FRED indicator display
2. `DataTableWidget.tsx` — for top cryptos, indicator lists
3. `CalcWidget.tsx` — NPV/Sharpe results
4. `SparklineWidget.tsx` — SVG mini-chart

### Phase 4: Streaming Polish
1. Handle incomplete markers during streaming
2. Widget skeleton loading states
3. Smooth transition from skeleton → rendered widget

---

## Key Questions for User

1. **Widget style preference**: Minimal/compact cards or rich/expanded with more detail?
2. **Color scheme**: Use existing shadcn theme tokens or custom crypto green/red?
3. **Sparkline**: Is a simple SVG polyline acceptable, or do you want a proper chart library?
4. **Priority**: Start with crypto widgets (most visual impact) or macro first?
5. **Mobile**: Should widgets be collapsible on mobile to save space?
