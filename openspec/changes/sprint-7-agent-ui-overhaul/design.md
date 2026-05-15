# Design: Sprint 7 — Agent & UI Overhaul

## Technical Approach

El cambio tiene 4 frentes independientes que se implementan en paralelo:

1. **Agente multi-idioma**: Reemplazar keyword detection por `langdetect`, construir prompts dinámicos por idioma
2. **Respuestas naturales**: Subir temperature, instruir al LLM que no use formato ReAct, eliminar `_clean_response()` regex
3. **Dashboard ChatGPT**: Sidebar con historial, sugerencias en welcome, bubbles con markdown
4. **Optimización**: Lazy orchestrator, `@st.cache_data`, CSS externalizado

## Architecture Decisions

### Decision: Language Detection Library

**Choice**: `langdetect` (port of Google's language-detection)
**Alternatives**: `fasttext` (more accurate but 500MB+ model), `py3langid` (lighter but less accurate), keyword-based (current, only ES/EN)
**Rationale**: `langdetect` is < 10MB, works offline, supports 55 languages, detects in < 50ms. Good enough for a chat agent. FastText is overkill.

### Decision: Temperature Strategy

**Choice**: `rag_llm_temperature = 0.3` default (was 0.0). Configurable via `.env`.
**Alternatives**: Keep 0.0 (robotic), use 0.7+ (creative but risks hallucination)
**Rationale**: 0.3 balances variation with factual consistency. User can override for their use case.

### Decision: Prompt Structure for Multi-Language

**Choice**: Single prompt template with `{language}` parameter + dynamic instruction to respond in that language. Tool descriptions stay in English.
**Alternatives**: Full prompt per language (current approach, doesn't scale beyond ES/EN)
**Rationale**: LLMs understand "respond in X language" perfectly. No need for full prompt translation. Scales to any language.

### Decision: Sidebar Implementation

**Choice**: Use native `st.sidebar` with custom CSS styling (not hidden, not `st.container` hacks)
**Alternatives**: `st.container` with absolute positioning (fragile), keep sidebar hidden (current)
**Rationale**: `st.sidebar` is stable, accessible, and responsive. Custom CSS can style it to look like ChatGPT.

### Decision: Orchestrator Lazy Loading

**Choice**: Initialize orchestrator on first user query, show welcome screen immediately on load
**Alternatives**: Initialize eagerly (current ~5s load), initialize on button click
**Rationale**: Users see UI immediately. The ~2-3s init delay happens after they type, disguised by the typing indicator.

### Decision: CSS Strategy

**Choice**: Single `dashboard.css` file loaded via `st.markdown`, remove ALL inline CSS from `app.py`
**Alternatives**: Keep inline CSS (current duplication), CSS-in-JS via Python
**Rationale**: Single CSS file is maintainable, cacheable by browser, and separates concerns

## Data Flow

### Agent Flow (New)
```
User Query (any language)
    ↓
detect_language(query) → "fr", "de", "pt", "es", "en", etc.
    ↓
Build system prompt: base prompt + "Respond in {language}"
    ↓
LLM (temperature=0.3) → generates response without ReAct format
    ↓
Cache result (if enabled)
    ↓
Return clean natural response
```

### Dashboard Flow (New)
```
Page Load
    ↓
Show Welcome Screen (instant, < 1s)
    ↓
[User types query]
    ↓
Initialize Orchestrator (if first query) ← Lazy init
    ↓
Send to Agent → stream response
    ↓
Display in chat bubbles
    ↓
Save to sidebar history
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/agents/query_agent.py` | Modify | Language detection, dynamic prompts, no regex cleanup, temperature change |
| `src/agents/chains/prompts.py` | Modify | Single dynamic prompt template, remove ES/EN duplicates |
| `src/agents/orchestrator.py` | Modify | Optional lazy init mode |
| `src/ui/app.py` | Rewrite | ChatGPT layout, sidebar, suggestions, lazy init, caching |
| `src/config/__init__.py` | Modify | Add `detect_language` setting, temperature validation |
| `requirements.txt` | Modify | Add `langdetect` |
| `.streamlit/config.toml` | Modify | Expanded theme config |

## Interfaces

### `detect_language(query: str) -> str`
```python
def detect_language(query: str) -> str:
    """Detect language using langdetect.
    
    Returns:
        ISO 639-1 code (e.g., 'en', 'es', 'fr', 'de', 'pt').
        Falls back to 'en' on detection failure or short queries.
    """
```

### Dynamic Prompt Template
```python
SYSTEM_PROMPT = """You are a market intelligence assistant...
Respond in {language} language.
IMPORTANT: Do NOT use "Thought:", "Action:", "Observation:", or "Answer:" prefixes.
Just respond naturally."""
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `detect_language()` with ES, EN, FR, DE, PT, mixed | pytest |
| Unit | Prompt template renders correctly with different languages | pytest |
| Unit | Temperature is read from settings correctly | pytest |
| Integration | Orchestrator lazy init works (init only on first query) | Integration test |
| E2E | Agent response in French contains French text | Manual |
| E2E | Dashboard loads in < 1s | Manual timing |
| E2E | Sidebar shows history correctly | Manual |

## Migration / Rollback

**No data migration needed.** All changes are in application code.

**Rollback**: `git revert` of changed files. The old CSS inline code is preserved in git history.

## Implementation Priority

1. **Inmediato**: `detect_language()` con langdetect + prompts dinámicos
2. **Inmediato**: Temperature 0.3 + eliminar regex cleaning
3. **Corto**: Dashboard ChatGPT layout + sidebar
4. **Corto**: Lazy orchestrator init
5. **Medio**: Caching y optimizaciones
6. **Medio**: External CSS cleanup
