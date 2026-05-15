# Proposal: Overhaul Fixes

## Intent

The app is completely broken: blank page, invisible sidebar, runtime crashes on metadata filters, and NameError on MACD. Four critical bugs and two warnings prevent ANY functionality from working. This is not an enhancement — it's emergency triage to make the app functional again.

## Scope

### In Scope
- Fix CSS `padding: 0 !important` that hides all content in Streamlit 1.57
- Fix typo `query_query_embeddings` → `query_embeddings` in retriever.py (crashes all metadata filters)
- Fix import order: move `setup_user_context()` execution AFTER `st.set_page_config()`
- Fix `macd_line` → `macd_series` NameError in indicators.py
- Remove duplicate logger in transformer.py
- Verify `.env` completeness

### Out of Scope
- UI/UX enhancements (covered by `dashboard-ui-improvement` change)
- New features, ML model changes, or architecture refactoring
- Prompt changes or agent behavior improvements

## Capabilities

### New Capabilities
None — pure bugfix, no new capabilities introduced.

### Modified Capabilities
- `market-rag-retriever`: Typo in query method causes crashes on metadata-filtered queries; requirement behavior unchanged but implementation must work
- `feature-engineering`: MACD calculation has NameError; spec behavior unchanged but implementation must work

## Approach

Surgical fixes, one per bug, no refactoring:
1. **CSS**: Replace destructive `.block-container { padding: 0 !important }` with Streamlit 1.57-safe selectors. Keep dark theme but use proper padding values.
2. **Retriever**: Simple typo fix — `query_query_embeddings` → `query_embeddings` on line 472.
3. **App.py**: Move the `from src.agents.user_context import setup_user_context` import and `setup_user_context()` call from lines 35-44 to after `st.set_page_config()` (after line 56). Streamlit requires `set_page_config()` as the FIRST command.
4. **Indicators**: Change `macd_line` → `macd_series` on line 338 (variable already defined as `macd_series`).
5. **Transformer**: Delete duplicate `logger = get_logger(__name__)` on line 38.
6. **.env**: Verify key configs present (OpenRouter keys, provider settings).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ui/styles/dashboard.css` | Modified | Fix padding rule, update selectors for Streamlit 1.57 |
| `src/agents/retriever.py` | Modified | Fix typo on line 472 |
| `src/ui/app.py` | Modified | Reorder imports: move user_context after set_page_config |
| `src/ml_models/features/indicators.py` | Modified | Fix variable name on line 338 |
| `src/ml_models/features/transformer.py` | Modified | Delete duplicate logger line 38 |
| `.env` | Verified | Confirm all required keys present |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| CSS fix breaks other Streamlit versions | Low | Test on 1.57 specifically; use responsive padding values |
| Moving import changes module load order | Low | Import is still top-of-file for its block; only call moves after config |
| .env missing keys block startup | Medium | Verify and document required keys |

## Rollback Plan

Each fix is a single-line change. Git revert on individual files is trivial. For CSS, keep the old file committed so `git checkout HEAD -- dashboard.css` restores original. No database or schema changes involved.

## Dependencies

- None beyond existing stack (Streamlit 1.57, ChromaDB, LangChain)

## Success Criteria

- [ ] App loads without blank page — content renders immediately
- [ ] Sidebar is visible with dark theme and conversation history
- [ ] Metadata filter queries return results without crashing
- [ ] MACD calculation runs without NameError
- [ ] No duplicate logger warnings on import
- [ ] `.env` has all required configuration keys