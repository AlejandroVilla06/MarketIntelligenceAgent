# Proposal: Sprint 7 — Agent & UI Overhaul

## Intent

El agente responde de forma robótica (temperature=0.0, regex stripping de "Answer:" / "Thought:"), solo habla ES/EN por detección keyword, el dashboard tiene sidebar oculto, CSS duplicado sin usar, y sin optimización de carga. Necesitamos un agente con respuestas naturales multi-idioma y una UI tipo ChatGPT con rendimiento optimizado.

## Scope

### In Scope
- Sistema de respuestas con variación y lenguaje natural (sin regex stripping)
- Detección de idioma robusta (cualquier idioma, no solo ES/EN)
- Sistema de prompts que NO genere formato ReAct en la respuesta final
- Dashboard tipo ChatGPT: sidebar real con historial, sugerencias, temas
- Optimización: lazy loading, caché de métricas, inicialización diferida
- Limpieza: unificar CSS, eliminar duplicación inline

### Out of Scope
- Migración a otro framework (Next.js, React)
- Nuevas capacidades de ML o data engine
- Autenticación de usuarios

## Capabilities

### New Capabilities
- `natural-language-agent`: Sistema de respuestas con variación, personalidad y tono adaptable
- `multi-language-support`: Detección y respuesta en cualquier idioma
- `chatgpt-dashboard`: Sidebar con historial, sugerencias, navegación tipo ChatGPT
- `ui-performance-optimization`: Lazy loading, caching, inicialización diferida

### Modified Capabilities
- None (refactor completo de UI y agente)

## Approach

**Agente**: Subir temperature a 0.3-0.5, usar system prompt que instruya NO usar formato ReAct en output, usar LangChain's `response_format` o post-procesamiento inteligente con LLM. Detección de idioma con `langdetect`/`fasttext` en vez de keywords.

**UI**: Streamlit con sidebar real (no oculta) usando componentes nativos + CSS custom tipo ChatGPT. Sugerencias de preguntas, historial de conversación en sidebar, tema oscuro profesional.

**Optimización**: `@st.cache_data` con TTL para métricas, `functools.lru_cache` para detección de idioma, inicialización lazy del orchestrator solo cuando el usuario escribe.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/agents/query_agent.py` | Modified | Nuevo sistema de respuestas, temperatura variable, multi-idioma |
| `src/agents/chains/prompts.py` | Modified | Prompts sin formato ReAct, con personalidad variable |
| `src/agents/orchestrator.py` | Modified | Inicialización lazy configurable |
| `src/ui/app.py` | Rewrite | Dashboard tipo ChatGPT con sidebar, sugerencias |
| `src/ui/styles/dashboard.css` | Modified | CSS unified y expandido |
| `.streamlit/config.toml` | Modified | Tema expandido |
| `requirements.txt` | Modified | +langdetect o py3langid |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| temperature > 0.0 da respuestas inconsistentes | Medium | Mantener range 0.2-0.5, testear |
| detección idioma con lib externa falla | Low | Fallback a keyword detection |
| sidebar en Streamlit se ve mal en mobile | Low | Testing responsive |

## Rollback Plan

Revert commits en `src/ui/app.py`, `src/agents/query_agent.py`, `src/agents/chains/prompts.py`. Las nuevas dependencias se pueden remover del requirements.

## Dependencies

- `langdetect` o `py3langid` para detección multi-idioma
- streamlit >= 1.30.0 (ya instalado)

## Success Criteria

- [ ] El agente responde con variación (misma pregunta → respuestas NO idénticas)
- [ ] Usuario escribe en francés/portugués/alemán → respuesta en ese idioma
- [ ] El output del agente NO contiene "Answer:" / "Thought:" / "Action:"
- [ ] Dashboard tiene sidebar con historial de conversación
- [ ] Dashboard carga < 2s vs ~5s actual
- [ ] Las sugerencias de preguntas aparecen en la pantalla de bienvenida
- [ ] CSS unificado (sin duplicación inline + archivo separado)
