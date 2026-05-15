# Tasks: Dashboard UI Improvement

## Phase 1: Foundation - Empathetic Prompts

- [x] 1.1 Modificar `src/agents/chains/prompts.py` - crear `MARKET_REACT_PROMPT_ES` con instrucciones de empatía en español
- [x] 1.2 Modificar `src/agents/chains/prompts.py` - crear variante `MARKET_REACT_PROMPT_EN` con empatía en inglés
- [x] 1.3 Modificar `src/agents/chains/prompts.py` - crear `SUMMARIZE_RESULTS_PROMPT_ES` y `SUMMARIZE_RESULTS_PROMPT_EN`

## Phase 2: Core - Language Detection

- [x] 2.1 Modificar `src/agents/query_agent.py` - agregar función `detect_language(query: str) -> str`
- [x] 2.2 Modificar `src/agents/query_agent.py` - agregar lógica para seleccionar prompt según idioma detectado
- [x] 2.3 Modificar `src/agents/query_agent.py` - integrar detección en método `run()` antes de ejecutar el agente
- [x] 2.4 Modificar `src/agents/query_agent.py` - agregar respuesta de fallback multilingüe para saludos

## Phase 3: UI Performance - Caching

- [ ] 3.1 Modificar `src/ui/app.py` - envolver `get_ollama_status()` con `@st.cache_data(ttl=30)`
- [ ] 3.2 Modificar `src/ui/app.py` - envolver `get_latency_metrics()` con `@st.cache_data(ttl=30)`
- [ ] 3.3 Modificar `src/ui/app.py` - crear función `get_cached_document_counts(orchestrator)` con cacheo
- [ ] 3.4 Modificar `src/ui/app.py` - actualizar `render_sidebar()` para usar funciones cacheadas

## Phase 4: UI - Custom Sidebar & Styling

- [x] 4.1 Crear `src/ui/styles/dashboard.css` - agregar CSS avanzado para sidebar con tarjetas y secciones colapsables
- [x] 4.2 Modificar `src/ui/app.py` - importar y usar el nuevo CSS en lugar del CSS inline actual
- [ ] 4.3 Modificar `src/ui/app.py` - refactorizar `render_sidebar()` para usar componentes custom con `st.container()`
- [ ] 4.4 Modificar `.streamlit/config.toml` - expandir configuración de tema con más opciones visuales

## Phase 5: Testing & Verification

- [x] 5.1 Crear `tests/test_language_detection.py` - tests unitarios para `detect_language()` con casos en español, inglés y otros
- [x] 5.2 Crear `tests/test_prompts.py` - verificar que los nuevos prompts se renderizan correctamente
- [ ] 5.3 Manual test - ejecutar `streamlit run src/ui/app.py` y verificar carga rápida del dashboard
- [ ] 5.4 Manual test - enviar queries en español y verificar respuesta en español
- [ ] 5.5 Manual test - enviar queries en inglés y verificar respuesta en inglés
- [ ] 5.6 Manual test - verificar diseño visual de la sidebar con tarjetas y jerarquía

## Phase 6: Cleanup

- [ ] 6.1 Eliminar código CSS inline antiguo de `src/ui/app.py` ahora que está en archivo separado
- [ ] 6.2 Agregar comentarios de documentación a las nuevas funciones
- [ ] 6.3 Actualizar `README.md` si es necesario con nuevas instrucciones de uso