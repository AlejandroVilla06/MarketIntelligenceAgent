# Exploration: Dashboard UI Improvement

## Current State

El proyecto MarketIntelligenceAgent tiene un dashboard Streamlit básico en `src/ui/app.py` que fue creado en el Sprint 6. El dashboard actualmente:

1. **Lentitud**: Llama a 3 APIs en cada render de sidebar (Ollama, ChromaDB, Latency Tracker) sin cacheo. El orchestrator se reinicializa frecuentemente.

2. **UI Anti-estética**: Usa `st.sidebar.*` nativo de Streamlit con CSS mínimo que solo cambia colores de botones a steel blue. No hay diseño profesional, jerarquía visual, o componentes custom.

3. **Respuestas Robóticas**: Los prompts en `src/agents/chains/prompts.py` son muy técnicos (formato ReAct con "Thought:", "Action:", "Answer:"). No hay empatía, variabilidad, ni soporte multilingüe.

## Affected Areas

- `src/ui/app.py` — Rendering de sidebar y chat sin optimización
- `src/agents/chains/prompts.py` — Prompts secos y técnicos
- `src/agents/query_agent.py` — Lógica de respuesta sin adaptación de idioma
- `.streamlit/config.toml` — Tema limitado

## Approaches

1. **Optimización de Rendimiento con Cache** — Usar `@st.cache_data` para métricas del sidebar, lazy loading del orchestrator
   - Pros: Rápido de implementar, sin cambios arquitectónicos
   - Cons: TTL puede causar datos stale
   - Effort: Medium

2. **Rediseño UI con Componentes Custom** — Crear sidebar con `st.container` + CSS avanzado
   - Pros: Diseño profesional, control total
   - Cons: Más código CSS, requiere testing
   - Effort: High

3. **Prompts con Empatía y Multilingüismo** — Modificar prompts para incluir guidelines de comunicación
   - Pros: Respuestas naturales, mejor UX
   - Cons: Puede afectar calidad de respuestas técnicas
   - Effort: Medium

## Recommendation

Implementar los tres enfoques en paralelo. La optimización de cache es rápida y de alto impacto. El rediseño de UI puede hacerse de forma incremental. Los prompts mejorados son el cambio de mayor valor para la experiencia del usuario.

## Risks

- Cacheo sin TTL puede mostrar datos desactualizados
- Nuevos prompts pueden reducir la precisión técnica de respuestas financieras
- CSS custom puede romperse con actualizaciones de Streamlit

## Ready for Proposal

Yes. La propuesta "dashboard-ui-improvement" ha sido creada en `openspec/changes/dashboard-ui-improvement/proposal.md`.