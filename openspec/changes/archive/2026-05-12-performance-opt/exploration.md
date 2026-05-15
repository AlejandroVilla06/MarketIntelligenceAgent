# Exploration: performance-opt

## Current State

### Backend (FastAPI + LangChain + ChromaDB)
- **Fake streaming**: `chat.py` lines 81-88 — runs full `orch.ask()` synchronously, then splits response into words with `asyncio.sleep(0.02)` to simulate streaming. User sees nothing until the ENTIRE response is ready.
- **No compression**: `app.py` has no GZip/deflate middleware. All responses sent uncompressed.
- **ChromaDB init**: `retriever.py` line 81-102 — `PersistentClient` created per `MarketRAGRetriever` instance. Embedding model (`~80MB SentenceTransformer`) is singleton via `lru_cache` in `embedding.py` (good), but loaded on first request, blocking startup.
- **Semantic cache**: Uses ChromaDB for similarity search — every cache HIT still requires embedding generation + vector search (~50-100ms). No in-memory LRU for exact-match hot queries.
- **LLM call**: `query_agent.py` line 604 — `self._llm.invoke(messages)` is synchronous, blocking. No streaming callback support.
- **Middleware**: `middleware.py` — just request logging, no compression, no caching headers.

### Frontend (Next.js 14 + React 18)
- **Bundle size**: 255 kB First Load JS on `/chat` page.
- **react-markdown**: ~50-60 kB alone (dynamic import candidate — only needed for assistant messages).
- **rehype-highlight**: ~30 kB (syntax highlighting for code blocks in markdown).
- **lucide-react**: Only 3 icons used (`Send`, `Trash2`, `Menu`, `Plus`) — but `lucide-react` is ~20 kB tree-shaken. Properly imported by name (good).
- **shadcn/ui components**: `Sheet`, `Dialog`, `DropdownMenu`, `Card`, `Input`, `Button` — ~15-20 kB total.
- **Supabase**: `@supabase/ssr` + `@supabase/supabase-js` — ~30 kB combined.
- **Middleware**: `supabase/middleware.ts` calls `supabase.auth.getUser()` on EVERY request (line 28) — this is a Supabase API call per navigation. Should check session validity locally with JWT expiry.
- **next.config.mjs**: Empty config — no bundle analyzer, no image optimization, no compression.
- **Font**: `Inter` loaded via `next/font/google` (good — self-hosted, no layout shift).
- **No React.memo**: `ChatMessage`, `MessageList`, `Sidebar` have no memoization. Every state change in `chatStore` triggers full re-render tree.
- **No useCallback**: `handleSelectConversation`, `handleDeleteConversation`, `handleNewChat` are recreated every render (not wrapped in `useCallback`).
- **`key={i}` antipattern**: `MessageList.tsx` line 37 — uses array index as key for messages, which causes incorrect reconciliation when messages change.

## Affected Areas

### Backend
- `src/api/routes/chat.py` — Fake streaming implementation, needs real LLM streaming
- `src/api/app.py` — No GZip middleware, no compression
- `src/agents/query_agent.py` — `invoke()` is sync, needs `stream()` with callback handler
- `src/agents/orchestrator.py` — `ask()` returns full string, needs streaming variant
- `src/api/middleware.py` — Only logging, needs compression headers
- `src/agents/cache/semantic_cache.py` — No in-memory hot cache layer

### Frontend
- `frontend/src/components/ChatMessage.tsx` — No React.memo, react-markdown loaded eagerly
- `frontend/src/components/MessageList.tsx` — No React.memo, index key antipattern
- `frontend/src/components/Sidebar.tsx` — No React.memo
- `frontend/src/app/chat/page.tsx` — No useCallback on handler functions
- `frontend/src/lib/supabase/middleware.ts` — getUser() called on every request
- `frontend/next.config.mjs` — Empty config, no optimizations
- `frontend/src/hooks/useChat.ts` — Exists but not used (chat logic is in page.tsx)

## Approaches

### 1. Real LLM Streaming (Backend — HIGH IMPACT)
Replace `invoke()` with `stream()` using LangChain's callback system.

- **How**: Add `StreamingCallbackHandler` to `MarketQueryAgent`, pass tokens through an `asyncio.Queue`, stream from `chat.py` via SSE as tokens arrive.
- **Pros**: Users see first token in ~1-2s instead of waiting 10-30s for full response. Perceived performance 10x improvement.
- **Cons**: Requires changes to `query_agent.py`, `orchestrator.py`, and `chat.py`. Need to handle partial responses (what if stream fails mid-way?).
- **Effort**: Medium (3-4 files, ~150 lines)

### 2. Dynamic Import react-markdown (Frontend — HIGH IMPACT, LOW EFFORT)
`react-markdown` + `rehype-highlight` is ~80 kB. Only assistant messages need it.

- **How**: `const ReactMarkdown = dynamic(() => import('react-markdown'), { loading: () => <p className="animate-pulse">...</p> })`
- **Pros**: Immediate 80 kB reduction in initial chat page bundle. User sees UI faster.
- **Cons**: Slight flash when markdown renders (mitigated by loading skeleton).
- **Effort**: Low (1 file, ~5 lines)

### 3. GZip Compression Middleware (Backend — MEDIUM IMPORT, LOW EFFORT)
All API responses sent uncompressed.

- **How**: `from fastapi.middleware.gzip import GZipMiddleware; app.add_middleware(GZipMiddleware, minimum_size=500)`
- **Pros**: 60-80% reduction in response size for text-heavy market data responses. Simple one-liner.
- **Cons**: Negligible CPU overhead per request.
- **Effort**: Low (1 file, 2 lines)

### 4. React.memo + useCallback (Frontend — MEDIUM IMPACT, LOW EFFORT)
Every zustand state change re-renders entire component tree.

- **How**: Wrap `ChatMessage`, `MessageList`, `Sidebar` in `React.memo`. Wrap handlers in `chat/page.tsx` with `useCallback`.
- **Pros**: Eliminates unnecessary re-renders during streaming (every token update). Smoother UX.
- **Cons**: Slightly more complex code. Must ensure dependency arrays are correct.
- **Effort**: Low (4-5 files, ~20 lines)

### 5. In-Memory LRU Cache for Hot Queries (Backend — MEDIUM IMPACT)
Current semantic cache hits still require embedding + ChromaDB search.

- **How**: Add `@functools.lru_cache(maxsize=256)` on query hash before semantic cache lookup. TTL via periodic invalidation.
- **Pros**: Cache HIT goes from ~50-100ms to <1ms for repeated queries. Perfect for "¿cómo está AAPL?" asked 100 times.
- **Cons**: Memory usage increases (~2-5 MB for 256 entries). Need TTL management.
- **Effort**: Low-Medium (1-2 files, ~30 lines)

### 6. Supabase Middleware Optimization (Frontend — MEDIUM IMPACT)
`getUser()` is called on EVERY request including static assets.

- **How**: Check JWT expiry locally before calling Supabase API. Only call `getUser()` when token is near expiry.
- **Pros**: Eliminates unnecessary Supabase API calls. Faster navigation.
- **Cons**: Need to handle JWT decoding (but `jose` is already available).
- **Effort**: Medium (1 file, ~30 lines)

### 7. next.config.mjs Optimization (Frontend — LOW-MEDIUM IMPACT)
Empty config means no output optimization.

- **How**: Add `output: 'standalone'`, enable `swcMinify`, configure `images` domain, enable `compress: true`.
- **Pros**: Smaller bundles, faster builds, better production performance.
- **Cons**: Need to test that nothing breaks.
- **Effort**: Low (1 file, ~15 lines)

### 8. Fix key={i} Antipattern (Frontend — LOW IMPACT, ZERO EFFORT)
`MessageList.tsx` uses array index as key.

- **How**: Use `msg.timestamp` or generate a unique ID per message in the store.
- **Pros**: Correct React reconciliation. Prevents stale UI bugs.
- **Cons**: Need to add `id` field to `Message` type.
- **Effort**: Low (2-3 files, ~10 lines)

### 9. CORS Preflight Optimization (Backend — LOW IMPACT)
`allow_methods=["*"]` and `allow_headers=["*"]` force preflight on complex requests.

- **How**: Restrict to actual methods/headers used. Add `max_age=3600` to cache preflight.
- **Pros**: Fewer preflight round-trips.
- **Cons**: Need to enumerate actual methods/headers.
- **Effort**: Low (1 file, 3 lines)

### 10. Font Loading Optimization (Frontend — LOW IMPACT)
Already using `next/font/google` (good). Could add `font-display: swap` explicitly.

- **How**: Already handled by `next/font`. No action needed.
- **Pros**: Already optimal.
- **Cons**: None.
- **Effort**: None (already done)

## Recommendation

**Ranked by Impact/Effort Ratio (best first):**

| # | Optimization | Impact | Effort | Ratio | Time |
|---|---|---|---|---|---|
| 1 | Dynamic import react-markdown | HIGH | LOW | ⭐⭐⭐⭐⭐ | 15 min |
| 2 | GZip compression middleware | MEDIUM | LOW | ⭐⭐⭐⭐⭐ | 5 min |
| 3 | React.memo + useCallback | MEDIUM | LOW | ⭐⭐⭐⭐ | 30 min |
| 4 | Real LLM streaming | HIGH | MEDIUM | ⭐⭐⭐⭐ | 2-3 hrs |
| 5 | In-memory LRU cache | MEDIUM | LOW | ⭐⭐⭐⭐ | 30 min |
| 6 | Supabase middleware optimization | MEDIUM | MEDIUM | ⭐⭐⭐ | 1 hr |
| 7 | next.config.mjs optimization | LOW-MED | LOW | ⭐⭐⭐ | 15 min |
| 8 | Fix key={i} antipattern | LOW | LOW | ⭐⭐⭐ | 10 min |
| 9 | CORS preflight optimization | LOW | LOW | ⭐⭐ | 10 min |
| 10 | Font optimization | NONE | NONE | — | Done |

### Top 5 Detailed Plan

#### 1. Dynamic Import react-markdown (15 min)
**File**: `frontend/src/components/ChatMessage.tsx`

```tsx
// Before
import ReactMarkdown from "react-markdown"

// After
import dynamic from "next/dynamic"
const ReactMarkdown = dynamic(() => import("react-markdown"), {
  loading: () => <div className="animate-pulse h-4 bg-muted rounded w-3/4" />,
  ssr: false, // Markdown only renders client-side anyway
})
```

**Expected result**: Chat page drops from ~255 kB to ~175 kB First Load JS.

#### 2. GZip Compression (5 min)
**File**: `src/api/app.py`

```python
from fastapi.middleware.gzip import GZipMiddleware

# After CORS middleware
app.add_middleware(GZipMiddleware, minimum_size=500)
```

**Expected result**: 60-80% smaller API responses. Chat responses (typically 1-5 KB text) compress to 200-800 bytes.

#### 3. React.memo + useCallback (30 min)
**Files**: `ChatMessage.tsx`, `MessageList.tsx`, `Sidebar.tsx`, `chat/page.tsx`

- Wrap all 3 components in `React.memo`
- Wrap `handleSelectConversation`, `handleDeleteConversation`, `handleNewChat` in `useCallback`
- Fix `key={i}` to use unique message ID

**Expected result**: During streaming, only the new message bubble re-renders (not entire list).

#### 4. Real LLM Streaming (2-3 hrs)
**Files**: `query_agent.py`, `orchestrator.py`, `chat.py`

Approach:
1. Create `StreamingCallbackHandler(BaseCallbackHandler)` in `query_agent.py`
2. Add `stream()` method to `MarketQueryAgent` that uses `self._llm.stream(messages)` instead of `invoke()`
3. Add `ask_stream()` to `MarketOrchestrator` that yields tokens
4. Modify `chat_stream` endpoint to consume the async generator

```python
# query_agent.py — new stream method
async def stream(self, query: str) -> AsyncGenerator[str, None]:
    """Stream analysis token by token."""
    # ... same setup as run() ...
    async for chunk in self._llm.astream(messages):
        if chunk.content:
            yield chunk.content
```

**Expected result**: First token visible in ~1-2s. Full perceived response time drops from 15-30s to progressive.

#### 5. In-Memory LRU Cache (30 min)
**File**: `src/agents/query_agent.py` (in `_check_cache`)

```python
import hashlib
from functools import lru_cache

# In-memory exact-match cache (fast path before semantic cache)
_exact_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 300  # 5 minutes

def _check_exact_cache(self, query: str) -> str | None:
    key = hashlib.md5(query.lower().strip().encode()).hexdigest()
    if key in _exact_cache:
        result, ts = _exact_cache[key]
        if time.time() - ts < self._CACHE_TTL:
            return result
        del _exact_cache[key]
    return None
```

**Expected result**: Repeated queries (common in market apps — "¿cómo está AAPL?") return in <1ms.

## Risks

- **Real streaming**: If the LLM provider doesn't support streaming (some OpenAI-compatible APIs), need graceful fallback to current behavior.
- **Dynamic import react-markdown**: SSR disabled means no server-rendered markdown (acceptable for chat — it's always client-side).
- **In-memory cache**: Memory grows unbounded if TTL eviction isn't implemented. Need periodic cleanup.
- **React.memo**: Incorrect dependency arrays can cause stale renders. Must test thoroughly.

## Ready for Proposal

**Yes** — all 10 optimizations are well-understood, low-risk individually, and can be implemented incrementally. The recommended order is: (1) quick wins first (GZip, dynamic import, memo), (2) then the high-impact streaming change, (3) then cache and middleware polish.

**Biggest bang for buck**: Dynamic import react-markdown + GZip = 20 minutes of work for ~40% bundle reduction + ~70% API response compression.
