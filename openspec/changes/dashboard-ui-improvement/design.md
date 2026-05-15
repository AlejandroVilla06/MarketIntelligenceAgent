# Design: Dashboard UI Improvement

## Technical Approach

El cambio se implementa en tres frentes paralelos: (1) optimización de rendimiento con cacheo de métricas usando `@st.cache_data`, (2) rediseño de la sidebar con componentes custom usando `st.container()` y CSS avanzado, y (3) modificación de prompts del agente para detección de idioma y respuestas empáticas. Los tres frentes son independientes y pueden implementarse en paralelo.

## Architecture Decisions

### Decision: Cache Strategy for Metrics

**Choice**: Usar `@st.cache_data` con TTL de 30 segundos para métricas del sidebar
**Alternatives considered**: `st.fragment`, cache manual con session_state
**Rationale**: `@st.cache_data` es la API nativa de Streamlit para cacheo, funciona correctamente con funciones puras, y el TTL de 30 segundos balancea frescura de datos con reducción de llamadas API.

### Decision: Sidebar Implementation

**Choice**: Usar `st.container()` con CSS custom en lugar de `st.sidebar.*` nativo
**Alternatives considered**: Mantener `st.sidebar.*` con mejoras CSS solo
**Rationale**: Los componentes nativos de Streamlit tienen limitaciones de styling. `st.container()` ofrece control total sobre el layout y permite crear secciones colapsables, tarjetas, y jerarquía visual personalizada.

### Decision: Language Detection Implementation

**Choice**: Detectar idioma en `query_agent.py` antes de pasar al LLM, usar el idioma para seleccionar el prompt
**Alternatives considered**: Detectar en el frontend, detectar dentro del prompt del LLM
**Rationale**: Detectar en Python es más confiable y no depende de capacidades del LLM. Permite seleccionar el prompt correcto (español/inglés) antes de la llamada al modelo.

### Decision: Empathetic Prompts Structure

**Choice**: Crear múltiples variantes de prompt con diferentes tonos y usar rotación
**Alternatives considered**: Un solo prompt con instrucciones de empatía
**Rationale**: Múltiples variantes permiten rotación y evitan respuestas repetitivas. Las instrucciones de empatía dentro del prompt son más confiables que intentar modificar el comportamiento del LLM.

## Data Flow

```
User Input (español/inglés)
         ↓
query_agent.detect_language() → "es" o "en"
         ↓
Select prompt (MARKET_REACT_PROMPT_ES o MARKET_REACT_PROMPT_EN)
         ↓
Execute ReAct loop with selected prompt
         ↓
Response generated in user's language
         ↓
Display in chat with styling
```

```
Sidebar Metrics Request
         ↓
@st.cache_data(ttl=30) → check cache
         ↓
[Cache hit] → return cached metrics
         ↓
[Cache miss] → fetch from APIs → cache → return
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ui/app.py` | Modify | Agregar cacheo con `@st.cache_data`, nuevo CSS para sidebar custom, estructura de componentes |
| `src/agents/chains/prompts.py` | Modify | Agregar variantes de prompt en español e inglés con tono empático |
| `src/agents/query_agent.py` | Modify | Agregar función `detect_language()`, seleccionar prompt según idioma, agregar empatía |
| `.streamlit/config.toml` | Modify | Actualizar theme con más opciones de personalización |
| `src/ui/styles/custom_theme.css` | Create | CSS avanzado para sidebar, cards, y componentes visuales |

## Interfaces / Contracts

### New Function: detect_language(query: str) -> str
```python
def detect_language(query: str) -> str:
    """Detects language of user query.
    
    Returns: 'es' for Spanish, 'en' for English, 'other' for others.
    """
```

### New Functions in app.py
```python
@st.cache_data(ttl=30)
def get_cached_ollama_status() -> dict:
    """Cached version of get_ollama_status()."""

@st.cache_data(ttl=30)
def get_cached_document_counts(orchestrator) -> dict:
    """Cached version of document counts retrieval."""
```

### Prompt Structure
```python
EMPATHETIC_MARKET_REACT_PROMPT_ES = PromptTemplate.from_template(
    """Eres un asistente de análisis de mercado amigable y servicial...
    Instrucciones adicionales:
    - Saluda al usuario de manera cálida
    - Reconoce cuando el usuario expresa preocupación
    - Usa un tono cercano pero profesional
    ...
    """
)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `detect_language()` con diferentes inputs | pytest con casos: español, inglés, otros idiomas |
| Unit | Prompt templates se generan correctamente | Verificar rendering de templates |
| Integration | Cacheo funciona correctamente | Verificar TTL con timestamps |
| E2E | Dashboard carga rápido | Medir tiempo de carga |
| E2E | Respuestas en español/inglés | Manual testing con queries en ambos idiomas |

## Migration / Rollback

No migration required. Los cambios son backwards-compatible:
- El cacheo usa TTL corto, si falla se cae gracefully al comportamiento original
- Los nuevos prompts incluyen fallback al comportamiento original si el LLM falla
- El CSS nuevo complementa el existente, no lo reemplaza completamente

Rollback: git revert de los archivos modificados restaura el estado anterior.

## Open Questions

- [ ] ¿Qué pasa si el usuario mixtea idiomas en una misma query? (ej: "hola, how is NVDA?")
- [ ] ¿El tema de Streamlit en config.toml tiene límite de personalización?
- [ ] ¿Hay algún límite en el tamaño del CSS custom que podemos inyectar?

## Implementation Priority

1. **Inmediato**: Modificar prompts.py para agregar versiones en español (alto impacto, bajo riesgo)
2. **Corto plazo**: Agregar cacheo en app.py (mejora rendimiento inmediata)
3. **Medio plazo**: Diseñar e implementar sidebar custom (mayor esfuerzo, mayor impacto visual)