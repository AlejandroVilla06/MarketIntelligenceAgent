# Design: Sprint 3 - Análisis de Sentimiento con Llama 3.1

## Technical Approach

Agregar Llama 3.1 como tercer provider de sentiment analysis via Ollama + LangChain. El diseño mantiene la arquitectura existente de analyzers y agrega fallback automático cuando Ollama no está disponible.

## Architecture Decisions

### Decision: Sentiment Analyzer Pattern

**Choice**: Mantener el patrón de clase base con interfaz común (`analyze(text) -> float`)
**Alternatives considered**: Function-based, dependency injection con protocolos
**Rationale**: El código existente ya tiene este patrón con TextBlob y VADER. Mantener consistencia reduce refactoring y facilita testing.

### Decision: Fallback Strategy

**Choice**: Fallback automático dentro de `get_sentiment_analyzer()`
**Alternatives considered**: Fallback en tiempo de ejecución del análisis, feature flag
**Rationale**: Fallback en initialization es más limpio. Si Ollama no está, usamos TextBlob por defecto. El usuario cambia `SENTIMENT_PROVIDER` en config para elegir.

### Decision: Ollama Connection Method

**Choice**: LangChain Ollama integration (`ChatOllama` de `langchain_ollama`)
**Alternatives considered**: Direct REST API calls, llama.cpp Python binding
**Rationale**: LangChain ya está en el proyecto. ChatOllama ofrece abstracción superior, manejo de errores, y streaming ready.

### Decision: Prompt Engineering

**Choice**: System prompt especializado para finanzas + output parsing de JSON
**Alternatives considered**: Few-shot examples, chain-of-thought
**Rationale**: Prompts simples son más confiables para sentiment scoring. Usar JSON output para parsing estable.

## Data Flow

```
NewsPipeline.analyze_sentiment(df)
    │
    ├──→ LlamaSentimentAnalyzer.analyze(title)
    │         │
    │         ├──→ ChatOllama.invoke(prompt + title)
    │         │
    │         └──→ parse_response(score)
    │
    └──→ (si falla) → TextBlobSentimentAnalyzer.analyze(title)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/config/__init__.py` | Modify | Agregar `ollama_host`, `ollama_model`, `sentiment_fallback` settings |
| `src/data_engine/pipelines/news_pipeline.py` | Modify | Agregar `LlamaSentimentAnalyzer` class, modificar `get_sentiment_analyzer()` |
| `.env.example` | Modify | Agregar variables OLLAMA_* |
| `.env` | Modify | Agregar valores de configuración Ollama |

## Interfaces / Contracts

```python
# Nueva clase en news_pipeline.py
class LlamaSentimentAnalyzer:
    """Sentiment analyzer using Llama 3.1 via Ollama + LangChain."""

    def __init__(self, model: str = "llama3:8b"):
        self._model = model
        self._llm = ChatOllama(model=model)

    def analyze(self, text: str) -> float:
        """Analyze sentiment, return score -1 to 1."""
        # Prompt + LLM call + parse response
```

```python
# Nueva configuración en config/__init__.py
class Settings(BaseSettings):
    # ... existing ...

    # Sentiment Analysis - NEW
    ollama_host: Annotated[str, Field(
        description="Ollama host URL"
    )] = "http://localhost:11434"

    ollama_model: Annotated[str, Field(
        description="Ollama model for sentiment (llama3:8b, llama3:8b-q4)"
    )] = "llama3:8b"

    sentiment_fallback: Annotated[str, Field(
        description="Fallback provider when primary fails (textblob, vader)"
    )] = "textblob"
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `LlamaSentimentAnalyzer.analyze()` | Mock ChatOllama, verificar parsing de score |
| Unit | `get_sentiment_analyzer()` fallback logic | Test con/sin OLLAMA_HOST |
| Integration | Full pipeline con Ollama | Test end-to-end si Ollama disponible |
| Integration | Fallback automático | Mock unavailable Ollama, verificar fallback |

## Migration / Rollout

No migration required. Los cambios son additive:
- Nuevas variables en `.env` son opcionales
- Si `ollama_host` no está configurado, se usa fallback
- Pipeline existente sigue funcionando con TextBlob/VADER

## Open Questions

- [ ] ¿Qué modelo específico usar? ¿llama3:8b, llama3:8b-q4, o otro quantizado?
- [ ] ¿Timeout para Ollama? ¿Retry policy?
- [ ] ¿Cache de resultados de sentiment para evitar re-análisis?

### Next Step

Ready for tasks (sdd-tasks) para implementar los cambios.