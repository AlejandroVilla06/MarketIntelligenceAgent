# Proposal: Dashboard UI Improvement

## Intent

El dashboard actual del Market Intelligence Agent tiene tres problemas críticos que impactan la experiencia del usuario: (1) lentitud en la carga porque cada render ejecuta llamadas a APIs sin cacheo, (2) diseño antiestético con barra lateral nativa de Streamlit y CSS mínimo, y (3) respuestas del agente robóticas, técnicas y sin empatía ni soporte multilingüe. El usuario necesita un dashboard rápido, atractivo visualmente, y con un agente que responda de forma natural y en cualquier idioma.

## Scope

### In Scope
- Optimización de rendimiento del dashboard (lazy loading, cacheo de componentes)
- Rediseño de la barra lateral con componentes personalizados y jerarquía visual
- Mejora de prompts del agente para respuestas empáticas y multilingües
- Nuevo diseño de chat con mejor UX (sugerencias, contexto)

### Out of Scope
- Cambios en la arquitectura del orchestrator o retriever
- Nuevas funcionalidades de ML o analytics
- Migración a otro framework de UI (React, Vue, etc.)

## Capabilities

### New Capabilities
- `ui-perf-optimization`: Optimizaciones de rendimiento en frontend (lazy loading, memoización, cacheo)
- `custom-sidebar`: Barra lateral con componentes custom y diseño profesional
- `empathetic-agent`: Prompts mejorados para respuestas con empatía y soporte multilingüe

### Modified Capabilities
- `streamlit-app`: El spec existente de streamlit-app necesita actualizarse para incluir los nuevos requirements de UI

## Approach

**Rendimiento:** Implementar `st.fragment` o `@st.cache_data` para cachear métricas del sidebar. Usar `st.empty()` para actualizaciones parciales en lugar de reruns completos. Inicializar el orchestrator de forma lazy solo cuando el usuario interactúa.

**UI:** Crear componentes custom usando `st.container` con CSS personalizado. Implementar una estructura de sidebar más limpia con secciones colapsables. Usar un diseño más moderno con tarjetas, gradientes sutiles, y mejor tipografía.

**Agente:** Modificar `MARKET_REACT_PROMPT` y `SUMMARIZE_RESULTS_PROMPT` para incluir guidelines de empatía, detección de idioma del usuario, y respuestas más naturales. Agregar un sistema de variaciones de respuesta.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ui/app.py` | Modified | Optimización de rendimiento y nuevo CSS |
| `src/agents/chains/prompts.py` | Modified | Prompts con empatía y multilingüismo |
| `src/agents/query_agent.py` | Modified | Detección de idioma y respuesta adaptable |
| `.streamlit/config.toml` | Modified | Theme configuration mejorada |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cacheo causa datos stale | Medium | TTL corto en cache, invalidez manual |
| Prompts modificados degradan calidad | Medium | A/B testing, mantener fallback al prompt original |
| CSS breaking en actualizaciones de Streamlit | Low | Usar selectores específicos, testing en múltiples versiones |

## Rollback Plan

Revertir cambios en `src/ui/app.py` y `src/agents/chains/prompts.py` a los archivos originales del último commit. El `.streamlit/config.toml` puede revertirse directamente ya que es idempotente.

## Dependencies

- streamlit >= 1.30.0 (para usar @st.cache_data y fragmentos)
- No hay dependencias externas nuevas

## Success Criteria

- [ ] Dashboard carga en menos de 2 segundos (vs ~5s actual)
- [ ] Sidebar renderiza sin llamadas redundantes a APIs
- [ ] Las respuestas del agente detectan el idioma del usuario y responden en ese idioma
- [ ] Las respuestas incluyen saludos amigables y variación en el tono
- [ ] UI pasar checklist de diseño visual (jerarquía, spacing, colors)