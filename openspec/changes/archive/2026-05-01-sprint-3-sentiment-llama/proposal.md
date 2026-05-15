# Proposal: Sprint 3 - Análisis de Sentimiento con Llama 3.1

## Intent

Integrar Llama 3.1 como provider de análisis de sentimiento para mejorar la calidad del análisis vs TextBlob/VADER. El objetivo es usar un LLM local via Ollama para obtener sentiment más contextual y preciso en noticias financieras.

## Scope

### In Scope
- Integración de Ollama con LangChain para sentiment analysis
- Crear `LlamaSentimentAnalyzer` en `news_pipeline.py`
- Configuración de modelo en `.env` (OLLAMA_HOST, OLLAMA_MODEL)
- Fallback automático a TextBlob/VADER si Ollama no está disponible
- Soporte para sentimiento financiero especializado (no solo general)

### Out of Scope
- UI para sentiment analysis (fuera del Sprint 5)
- Fine-tuning de modelo Llama
- Integración con otros LLMs (Claude, GPT) como alternatives

## Capabilities

### New Capabilities
- `llama-sentiment-analyzer`: Agregar análisis de sentimiento con Llama 3.1 via Ollama + LangChain

### Modified Capabilities
- `news-sentiment-ingestion`: Extender para incluir Llama como provider adicional de sentiment

## Approach

Usar Ollama corriendo localmente con modelo Llama 3.1 (o quantized como llama3:8b). Crear un nuevo analyzer que:
1. LangChain Ollama integration para inference
2. Prompt especializado para análisis de sentimiento financiero
3. Fallback a TextBlob/VADER si Ollama no está disponible o falla

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/data_engine/pipelines/news_pipeline.py` | Modified | Agregar `LlamaSentimentAnalyzer` class |
| `src/config/__init__.py` | Modified | Agregar config para Ollama (OLLAMA_HOST, OLLAMA_MODEL) |
| `.env` | Modified | Agregar variables de entorno para Ollama |
| `openspec/specs/news-sentiment-ingestion/spec.md` | Modified | Delta spec agregando Llama como provider |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Ollama no instalado | Medium | Fallback automático a TextBlob/VADER |
| Memoria insuficiente | Low | Usar modelo quantizado (llama3:8b-q4) |
| Rate limiting local | Medium | Cache de resultados, batch processing |

## Rollback Plan

1. Cambiar `SENTIMENT_PROVIDER` en `.env` a "textblob" o "vader"
2. Eliminar variables OLLAMA del `.env`
3. El código ya tiene fallback automático

## Dependencies

- Ollama instalado localmente (https://ollama.com)
- LangChain integrado (ya en requirements.txt)

## Success Criteria

- [ ] `LlamaSentimentAnalyzer` implemented y funcional
- [ ] Fallback automático funciona cuando Ollama no está disponible
- [ ] Sentiment score comparable o mejor que TextBlob/VADER en mismos artículos
- [ ] Pipeline corre end-to-end sin errores