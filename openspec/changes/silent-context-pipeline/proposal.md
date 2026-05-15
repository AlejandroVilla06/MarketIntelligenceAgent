# Proposal: Silent Context Pipeline

## Intent

El sistema muestra datos crudos (Price Data, News, Sentiment) al usuario en lugar de solo análisis ejecutivo. La causa raíz es triple: (1) el prompt de sistema contiene artefactos ReAct que se filtran al LLM, (2) el stripping regex es insuficiente para capturar las fugas, y (3) el fallback `_format_output()` expone símbolos cuando el LLM no está disponible. Queremos un pipeline donde TODA la recuperación de datos es invisible — el usuario recibe EXCLUSIVAMENTE análisis ejecutivo del LLM.

## Scope

### In Scope
- Nuevo prompt limpio `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` sin artefactos ReAct
- Refactor de `_generate_analysis()` para usar prompt limpio en vez de regex-stripping
- Robustecer `_strip_data_sections()` con patrones localizados + Markdown + delimitadores
- Robustecer `_strip_react_artifacts()` con patterns adicionales
- Validación de cache: sanitizar respuestas cacheadas antes de retornar
- Reescribir `_format_output()` para NO exponer símbolos ni datos
- Configurar DeepSeek como proveedor LLM por defecto en `.env`

### Out of Scope
- Cambios al retriever (`retriever.py`) — funciona correctamente
- Cambios a la UI de Streamlit (`app.py`)
- Cambios al sistema de detección de idioma
- Cambios a la memoria de conversación
- Modificar `orchestrator.py` (no necesita cambios)
- Refactor del cache semántico (solo validación antes de retorno)

## Capabilities

### New Capabilities
- `silent-context-prompt`: Prompt exclusivo para pipeline de dos etapas (retrieve → analyze), sin artefactos ReAct, con instrucciones explícitas de contexto silencioso

### Modified Capabilities
- `market-query-agent`: El agente ahora usa prompt limpio, valida cache, y el fallback no expone datos crudos

## Approach

**Estrategia principal**: Eliminar la generación de artefactos en vez de intentar limpiarlos después.

1. **Prompt limpio** — Crear `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` sin `{input}`, `{agent_scratchpad}`, ni sección `# 🛠 AVAILABLE TOOLS`. Este prompt declara explícitamente que los datos de ChromaDB son "contexto silencioso" que NUNCA debe reproducirse.

2. **Reemplazar regex-stripping por prompt limpio** — En `_generate_analysis()`, construir `messages` usando el prompt limpio en vez de tomar `AGENT_SYSTEM_PROMPT_TEMPLATE` y regex-stripping `Begin!` y tools. El regex quedaría solo como safety net.

3. **Safety net robusto** — Ampliar `_strip_data_sections()` y `_strip_react_artifacts()` con patrones para Español, Francés, Alemán, Portugués, Italiano, Markdown headers, y delimitadores comunes de fugas.

4. **Cache validation** — En `_check_cache()`, aplicar la pipeline de sanitización completa antes de retornar.

5. **Fallback seguro** — `_format_output()` devuelve un mensaje genérico sin símbolos ni datos.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/agents/chains/prompts.py` | Modified | Nuevo template `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` + `build_analysis_prompt()` |
| `src/agents/query_agent.py` L550-636 | Modified | `_generate_analysis()` usa prompt limpio, elimina regex-stripping de system prompt |
| `src/agents/query_agent.py` L700-739 | Modified | `_strip_react_artifacts()` y `_strip_data_sections()` con patrones ampliados |
| `src/agents/query_agent.py` L464-479 | Modified | `_check_cache()` agrega validación antes de retorno |
| `src/agents/query_agent.py` L741-774 | Modified | `_format_output()` reescrito sin exponer símbolos |
| `.env` | Modified | `LLM_PROVIDER=deepseek` + `DEEPSEEK_API_KEY` configurado |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LLM aún filtra secciones de datos a pesar del prompt limpio | Low | Safety net regex ampliado sigue aplicándose como post-procesamiento |
| DeepSeek API key no configurada → vuelve a fallback | Med | `_format_output()` reescrito NO expone datos; instruimos en `.env` |
| Over-stripping: regex remueve contenido legítimo del análisis | Low | Patrones regex targetean SOLO headers de sección y delimitadores, no contenido narrativo |
| Cache existente con respuestas "sucias" | Med | Validación en `_check_cache()` sanitiza antes de retornar |

## Rollback Plan

1. Revertir `src/agents/chains/prompts.py` — el `AGENT_SYSTEM_PROMPT_TEMPLATE` original permanece intacto (no se eliminó)
2. Revertir `src/agents/query_agent.py` — git checkout del archivo
3. Revertir `.env` — restaurar valores originales
4. El código existente del ReAct prompt queda como fallback si se necesita el agente ReAct en el futuro

## Dependencies

- Credenciales DeepSeek válidas (API key configurada en `.env`)
- No hay dependencias de packages nuevas — usa `re` y `langchain` existentes

## Success Criteria

- [ ] El prompt enviado al LLM NO contiene `{input}`, `{agent_scratchpad}`, `Begin!`, ni sección `# 🛠 AVAILABLE TOOLS`
- [ ] Respuestas del LLM NO contienen secciones tipo "Price Data:", "News:", "Sentiment:" en ningún idioma
- [ ] Cuando el LLM no está disponible, el mensaje NO muestra símbolos ni datos crudos
- [ ] Cache retorna respuestas sanitizadas (sin secciones de datos crudos)
- [ ] La pipeline de dos etapas (retrieve → analyze) funciona end-to-end con DeepSeek
- [ ] Tests existentes pasan sin modificación