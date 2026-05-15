# Proposal: Sprint 4 — RAG Cross-Correlation: Sentiment + Financial Data

## Intent

Habilitar que el agente de mercado correlacione el sentimiento de Llama 3.1 con datos financieros (precios, volumen). Actualmente el RAG retorna datos de múltiples colecciones pero no puede responder "¿cuando el sentimiento fue positivo, el precio subió?". Este Sprint cierra ese gap.

## Scope

### In Scope
- Nuevas herramientas de correlación sentiment ↔ price en `market_tools.py`
- Query de datos alineados temporalmentepor símbolo y ventana de tiempo
- Prompts actualizados para usar contexto combinado de múltiples colecciones
- Integración con el ReAct loop del `MarketQueryAgent`

### Out of Scope
- Modificaciones al modelo de Llama o fine-tuning
- Nuevos fuentes de datos (Yahoo Finance, Polygon ya existentes)
- UI/visualización de correlaciones
- Backtesting de estrategias

## Capabilities

### New Capabilities
- `sentiment-price-correlation`: Correlacionar scores de sentimiento con cambios de precio por símbolo y ventana temporal
- `temporal-alignment`: Alinear datos de frecuencia diferente (sentiment diario, prices intraday) por símbolo + rango de fechas
- `cross-collection-context`: Enriquecer prompts con contexto estructurado de múltiples colecciones para queries complejas

### Modified Capabilities
- `market-query-agent`: Extender herramientas del ReAct agent para incluir correlation y temporal analysis
- `market-rag-retriever`: Agregar método `query_by_metadata()` para filtrar por símbolo/fecha sin búsqueda semántica

## Approach

Tool-Based RAG Agent — agregar herramientas especializadas en `market_tools.py`:

1. **`sentiment_price_correlation_tool`** — recibe símbolo + ventana temporal, retorna: lista de días con sentiment score, price change %, correlación (Pearson/Spearman)
2. **`temporal_alignment_tool`** — recibe símbolo + start/end, retorna: DataFrame alineado sentiment vs. price
3. **`aggregate_context_tool`** — recibe símbolo, retorna: resumen estructurado con sentiment agregado, price stats, volumen

Luegointegrar estas herramientas en `MarketQueryAgent` como herramientas adicionales del ReAct loop.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/agents/chains/market_tools.py` | New | 3 nuevas herramientas de correlación |
| `src/agents/query_agent.py` | Modified | Registrar nuevas herramientas en el agent |
| `src/agents/retriever.py` | Modified | Agregar `query_by_metadata()` |
| `src/agents/chains/prompts.py` | Modified | Prompts para contexto cross-collection |
| `openspec/specs/market-query-agent/spec.md` | Modified | Delta spec para nuevas herramientas |
| `openspec/specs/market-rag-retriever/spec.md` | Modified | Delta spec para `query_by_metadata()` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Latencia de inferencia Llama afecta queries real-time | Medium | Cachear resultados de correlación, async fallback |
| No overlap temporal entre sentiment y stock data | Medium | Validar rango de datos antes de correlacionar, log warning |
| Complejidad de prompts para contexto cruzado | Low | Empezar con templates simples, iterar basado en resultados |

## Rollback Plan

1. Revertir `src/agents/chains/market_tools.py` — remover las 3 nuevas funciones, mantener backup en git
2. Revertir `src/agents/query_agent.py` — desregistrar las nuevas herramientas del agent
3. Si `openspec/specs/` fue modificado, copiar desde `changes/sprint-4-*/specs/` como delta specs
4. Test: ejecutar queries existentes que no dependan de correlación

## Dependencies

- `market-rag-retriever`: existente (Sprint 2)
- `llama-sentiment-analyzer`: existente (Sprint 3)
- `market-query-agent`: existente (Sprint 3)
- ChromaDB + Polars: instalados

## Success Criteria

- [ ] El agente responde "¿Cómo correlacionó el sentimiento con el precio de AAPL esta semana?" retornando scores de correlación
- [ ] `temporal_alignment_tool` retorna DataFrame con sentiment y price alineados por fecha
- [ ] Prompts enriquecidos usan contexto de múltiples colecciones
- [ ] Tests unitarios para las 3 nuevas herramientas pasan
- [ ] Queries existentes del agent siguen funcionando sin regresión