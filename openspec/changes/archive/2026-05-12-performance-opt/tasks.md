# Tasks: performance-opt

## Phase 1: Quick Wins
- [ ] 1.1 Dynamic import react-markdown en ChatMessage.tsx
- [ ] 1.2 Add GZip middleware a app.py
- [ ] 1.3 React.memo en ChatMessage, MessageList, Sidebar
- [ ] 1.4 useCallback en chat/page.tsx
- [ ] 1.5 Fix key={i} antipattern en MessageList
- [ ] 1.6 Optimize next.config.mjs

## Phase 2: Real LLM Streaming
- [ ] 2.1 Add StreamingCallbackHandler to query_agent.py
- [ ] 2.2 Add ask_stream() to orchestrator.py
- [ ] 2.3 Modify SSE endpoint for real streaming
- [ ] 2.4 Add fallback for providers without streaming

## Phase 3: Polish
- [ ] 3.1 LRU hot cache in semantic_cache.py
- [ ] 3.2 Optimize Supabase middleware
- [ ] 3.3 Run all tests, verify no regressions
