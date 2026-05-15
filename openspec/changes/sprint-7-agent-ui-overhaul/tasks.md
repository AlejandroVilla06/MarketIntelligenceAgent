# Tasks: Sprint 7 — Agent & UI Overhaul

## Phase 1: Agent — Multi-Language Detection

- [x] 1.1 Add `langdetect` to `requirements.txt`
- [x] 1.2 Rewrite `detect_language()` in `query_agent.py` to use `langdetect` with fallback to keyword detection (6 languages: EN, ES, FR, DE, PT, IT)
- [x] 1.3 Add tests for `detect_language()` with ES, EN, FR, DE, PT, IT, mixed/ambiguous queries
- [x] 1.4 Update `prompts.py` — create single dynamic prompt with `{language}` parameter via `build_agent_prompt()`, keep backward compat aliases
- [x] 1.5 Update `MarketQueryAgent.run()` to build dynamic prompt per query language using `_build_agent_for_language()`

## Phase 2: Agent — Natural Responses

- [x] 2.1 Change default `rag_llm_temperature` from 0.0 to 0.3 in config with ge/le validation
- [x] 2.2 Update system prompt to instruct LLM: NO "Thought:/Action:/Observation:/Answer:" format (in `IMPORTANT FORMATTING RULES` section)
- [x] 2.3 Remove `_clean_response()` regex stripping — no longer needed (prompt handles it)
- [x] 2.4 Verify prompts instruct natural tone with complete sentences ("conversational, professional tone", "explain numbers in context")

## Phase 3: Dashboard — ChatGPT Layout

- [x] 3.1 Rewrite `src/ui/app.py` — new layout with `st.sidebar` for chat history, external CSS
- [x] 3.2 Implement welcome screen with 6 suggested question buttons in a 2-column grid
- [x] 3.3 Implement message bubbles (user right, assistant left) with labels
- [x] 3.4 Implement sidebar: "New Chat" button, history list with delete, click to resume
- [x] 3.5 Implement multi-conversation support via `st.session_state` with auto-titling
- [x] 3.6 Import and use external `dashboard.css` exclusively — ZERO inline CSS in app.py

## Phase 4: Dashboard — Performance

- [x] 4.1 Implement lazy orchestrator initialization (init on first query only, not on page load)
- [x] 4.2 CSS loading cached in session state (read once, reuse on rerender)
- [ ] 4.3 Add metrics caching for sidebar stats (deferred — sidebar is lightweight now)
- [ ] 4.4 Add `st.fragment` decorator to isolate chat area from sidebar rerenders

## Phase 5: Configuration & Dependencies

- [x] 5.1 Update `.streamlit/config.toml` with simpler theme
- [x] 5.2 Add `langdetect` to `requirements.txt`
- [x] 5.3 Update `src/config/__init__.py` — temperature = 0.3 with ge=0.0, le=1.0 validation

## Phase 6: Testing & Verification

- [ ] 6.1 Run `pytest tests/` — all existing tests must pass
- [ ] 6.2 Run new language detection tests
- [ ] 6.3 Manual: dashboard loads in < 1s
- [ ] 6.4 Manual: Spanish query → Spanish response
- [ ] 6.5 Manual: French query → French response
- [ ] 6.6 Manual: sidebar shows history, new chat works
- [ ] 6.7 Manual: suggested questions are clickable
- [ ] 6.8 Manual: responses vary (same question twice → different wording)
- [ ] 6.9 Manual: no "Thought:/Action:/Answer:" in output

## Phase 7: Cleanup

- [ ] 7.1 Remove old inline CSS from `app.py` (verify all styles are in `dashboard.css`)
- [ ] 7.2 Remove `MARKET_REACT_PROMPT_ES` and `MARKET_REACT_PROMPT_EN` duplicates
- [ ] 7.3 Remove `SUMMARIZE_RESULTS_PROMPT_ES` and `SUMMARIZE_RESULTS_PROMPT_EN` duplicates
- [ ] 7.4 Verify old SDD changes (chat-redesign-localized-responses, dashboard-ui-improvement) are superseded
