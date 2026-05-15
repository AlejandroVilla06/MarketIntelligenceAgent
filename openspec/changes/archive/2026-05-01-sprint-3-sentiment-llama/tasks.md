# Tasks: Sprint 3 - Análisis de Sentimiento con Llama 3.1

## Phase 1: Configuration (Foundation)

- [x] 1.1 Agregar `ollama_host: Annotated[str]` en `src/config/__init__.py` con default "http://localhost:11434"
- [x] 1.2 Agregar `ollama_model: Annotated[str]` en `src/config/__init__.py` con default "llama3:8b"
- [x] 1.3 Agregar `sentiment_fallback: Annotated[str]` en `src/config/__init__.py` con default "textblob"
- [x] 1.4 Actualizar description de `sentiment_provider` para incluir "llama" como opción válida

## Phase 2: Core Implementation

- [x] 2.1 Crear clase `LlamaSentimentAnalyzer` en `src/data_engine/pipelines/news_pipeline.py`
- [x] 2.2 Implementar método `__init__` con ChatOllama y configuración de timeout
- [x] 2.3 Implementar método `analyze(text) -> float` con prompt especializado para finanzas
- [x] 2.4 Agregar parsing de respuesta JSON del LLM para obtener score entre -1 y 1
- [x] 2.5 Agregar manejo de errores: ConnectionError, Timeout, Response parsing errors
- [x] 2.6 Implementar fallback en `get_sentiment_analyzer()` cuando provider es "llama" y Ollama no está disponible

## Phase 3: Integration & Wiring

- [x] 3.1 Modificar `get_sentiment_analyzer()` en `news_pipeline.py` para soportar "llama" como provider
- [x] 3.2 Agregar lógica de fallback: si Ollama falla, usar `sentiment_fallback` (textblob/vader)
- [x] 3.3 Verificar que `NewsPipeline` use correctamente el nuevo analyzer
- [x] 3.4 Actualizar `analyze_sentiment()` para manejar scores de Llama (mismo rango -1 a 1)

## Phase 4: Testing

- [x] 4.1 Crear test unitario para `LlamaSentimentAnalyzer.analyze()` con mock de ChatOllama
- [x] 4.2 Test fallback automático cuando Ollama no está disponible
- [x] 4.3 Test integración: pipeline corre end-to-end (requiere Ollama instalado)
- [x] 4.4 Test verificación: sentiment scores comparables entre providers en mismos artículos

## Phase 5: Documentation & Cleanup

- [x] 5.1 Actualizar `.env.example` agregando sección OLLAMA con variables y descripciones
- [x] 5.2 Agregar docstrings a `LlamaSentimentAnalyzer` siguiendo estilo del proyecto
- [x] 5.3 Agregar logging en inicialización del analyzer (ollama_host, model usado)
- [x] 5.4 Verificar que pipeline funcione sin OLLAMA configurado (fallback a textblob)