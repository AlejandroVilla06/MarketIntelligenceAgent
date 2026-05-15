# Design: Silent Context Pipeline

## Technical Approach

El problema raíz es que el pipeline actual reusa `AGENT_SYSTEM_PROMPT_TEMPLATE` (ReAct), strippea artefactos con regex frágiles, y expone símbolos en el fallback. La solución: **prompt limpio como primera línea de defensa**, con regex solo como safety net. Se crea `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` — sin `{input}`, `{agent_scratchpad}`, ni tools — y una función dedicada `build_analysis_prompt()`. El pipeline de dos etapas (retrieve → analyze) se mantiene intacto; solo cambia qué prompt usa Stage 2.

### Sequence Diagram: Pipeline Antes vs Después

```
ANTES (ReAct prompt + stripping):
  run() → _retrieve_raw_data() → _generate_analysis()
    ├─ build_agent_prompt()     ← ReAct template con tools, {input}, {agent_scratchpad}
    ├─ regex-strip Begin!, tools  ← frágil, incompleto
    ├─ _format_data_for_prompt()
    ├─ construye user_message (SILENT CONTEXT)
    └─ LLM.invoke(messages)
  → _strip_react_artifacts()   ← safety net
  → _strip_data_sections()     ← solo EN, patterns limitados

DESPUÉS (prompt limpio, safety net robusto):
  run() → _retrieve_raw_data() → _generate_analysis()
    ├─ build_analysis_prompt()   ← PROMT LIMPIO sin ReAct ni tools
    ├─ _format_data_for_prompt()
    ├─ construye user_message (SILENT CONTEXT)
    └─ LLM.invoke(messages)
  → _strip_react_artifacts()   ← ampliado a 6 idiomas
  → _strip_data_sections()     ← 6 idiomas + Markdown + bullets
  → _check_cache() sanitiza     ← NUEVO: validación en lectura
  → _format_output() seguro     ← NUEVO: sin símbolos ni datos
```

## Architecture Decisions

### A. Prompt Template: ¿Nuevo archivo o mismo archivo?

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **A: Mismo archivo (`prompts.py`)** | Cohesión por dominio; ambos templates son prompts del agente | ✅ **Elegida** |
| B: Archivo separado (`analysis_prompt.py`) | Aislamiento, pero fragmenta el módulo de prompts sin beneficio real | ❌ Descarte: over-engineering |

**Rationale**: Ambos templates coexisten en `prompts.py` con responsabilidades claramente distintas: `AGENT_SYSTEM_PROMPT_TEMPLATE` para ReAct (legacy/backward compat), `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` para el pipeline silencioso. Separarlos crea un módulo de 50 líneas sin cohesión con nada más.

### B. `build_analysis_prompt`: ¿Función separada o modificar `build_agent_prompt`?

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **A: Nueva función `build_analysis_prompt()`** | Código nuevo, sin riesgo de romper ReAct; firma diferente | ✅ **Elegida** |
| B: Modificar `build_agent_prompt()` con flag `silent=True` | Menos código, pero acopla dos responsabilidades en una función | ❌ Descarte: viola Single Responsibility |

**Rationale**: Firma diferente — `build_analysis_prompt(language, chat_history, user_profile, data_context)` recibe `data_context` que `build_agent_prompt()` no necesita. Meter un flag `silent=True` es un code smell de control flow acoplado.

### C. Silent Context: ¿System prompt o user message?

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| A: System prompt incluye los datos | Un solo mensaje, pero mezcla rol (system=reglas) con datos | ❌ Descarte |
| **B: User message con `---BEGIN DATA---`** | Separación clara: system=instrucciones, user=datos | ✅ **Elegida** |

**Rationale**: Mantener la separación semántica del chat format. El system prompt establece el contrato ("no reproduzcas datos"), el user message entrega el contenido. Es el patrón estándar de OpenAI/DeepSeek y el más testeado contra alucinaciones.

### D. ¿Cómo evitar duplicación con el prompt existente?

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| A: Template completamente nuevo, zero-copy del viejo | Sin duplicación, pero se pierden instrucciones útiles (persona, sectores) | ❌ Descarte |
| **B: Template nuevo que REUTILIZA secciones no-ReAct (persona, sectores, prohibiciones)** | Mejor prompt (hereda lo bueno), sin arrastrar ReAct | ✅ **Elegida** |
| C: Herencia de templates con `str.replace()` masivo | Frágil, acoplado al formato del template viejo | ❌ Descarte |

**Rationale**: El template viejo tiene instrucciones excelentes sobre persona, estructura de respuesta y frameworks sectoriales. El nuevo template las hereda SELECTIVAMENTE, eliminando solo `{input}`, `{agent_scratchpad}`, `Begin!`, y la sección `# 🛠 AVAILABLE TOOLS`. Es composición, no duplicación.

### E. Post-procesamiento: ¿Regex expansion o parser?

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **A: Expandir regex con 6 idiomas + Markdown** | Simple, mantenible, cubre 90% de fugas | ✅ **Elegida** |
| B: Parser estructurado (state machine, AST) | Overkill para texto libre de LLM; no puede parsear intención | ❌ Descarte |

**Rationale**: El output del LLM es texto narrativo no estructurado. Un parser formal no puede distinguir "Precio objetivo: $200" (análisis válido) de "Price Data: AAPL 170" (fuga). La primera línea de defensa es el prompt limpio; el regex es safety net para headers obvios.

### F. Cache validation: ¿Dónde se sanitiza?

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| A: Invalidar todo el cache | Limpio pero pierde análisis ejecutivos válidos cacheados | ❌ Descarte |
| **B: Sanitizar en `_check_cache()` antes de retornar** | Recupera entradas "sucias" del cache viejo sin perder las limpias | ✅ **Elegida** |
| C: Sanitizar al escribir (`_store_cache`) | Solo limpia entradas nuevas; el cache viejo sigue sucio | ❌ Descarte |

**Rationale**: Sanitizar en lectura (`_check_cache`) protege tanto contra entradas viejas sucias como contra regresiones futuras. Si el cache tiene entradas del pipeline viejo con "Price Data:", el stripping las limpia transparentemente.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/agents/chains/prompts.py` | Modify | Agregar `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` (~80 líneas) + `build_analysis_prompt()`. El template existente (`AGENT_SYSTEM_PROMPT_TEMPLATE`) y `build_agent_prompt()` no se tocan. |
| `src/agents/query_agent.py` L550-636 | Modify | `_generate_analysis()`: reemplazar `build_agent_prompt()` + regex-stripping por `build_analysis_prompt()`. Eliminar líneas 580-591. |
| `src/agents/query_agent.py` L718-739 | Modify | `_strip_data_sections()`: agregar patrones para 6 idiomas (es,en,fr,de,pt,it), Markdown tables, bullets, líneas numéricas. |
| `src/agents/query_agent.py` L464-479 | Modify | `_check_cache()`: aplicar `_strip_data_sections()` + `_strip_react_artifacts()` antes de retornar; invalidar si resultado queda vacío. |
| `src/agents/query_agent.py` L741-774 | Modify | `_format_output()`: eliminar símbolos y datos; mensaje genérico instruyendo configuración de LLM. |
| `.env` | Modify | Descomentar y configurar `LLM_PROVIDER`, `DEEPSEEK_API_KEY`, `DEEPSEEK_API_BASE`. |
| `tests/test_query_agent.py` | Modify | Actualizar `test_format_output_list` y `test_format_output_dict`: ya no deben esperar símbolos en fallback. |
| `tests/test_prompts.py` | Modify | Agregar tests para `build_analysis_prompt()`; test existente `test_prompt_has_tool_instructions` se mantiene (testea ReAct prompt). |

## Interfaces / Contracts

### `build_analysis_prompt()` — Nueva firma

```python
def build_analysis_prompt(
    language: str = "en",
    chat_history: str = "",
    user_context: str = "",
    data_context: str = "",        # NUEVO: lugar para formatted_data
) -> str:                          # Retorna str, NO PromptTemplate
```

**Por qué `str` en vez de `PromptTemplate`**: Este prompt NO usa `{input}` ni `{agent_scratchpad}` — no necesita `PromptTemplate.format()`. Se construye con `str.replace()` como hace `build_agent_prompt()` internamente, pero el resultado se usa directamente como `system` message.

### `_check_cache()` — Contrato modificado

```python
def _check_cache(self, query: str, language: str) -> str | None:
    # Antes: return result  (puede tener datos crudos)
    # Ahora: return sanitized or None (si queda vacío post-stripping)
```

### `_format_output()` — Contrato modificado

```python
def _format_output(self, data: Any) -> str:
    # Antes: "📊 Data retrieved for AAPL, NVDA" + instrucciones
    # Ahora: mensaje genérico sin símbolos: "No fue posible generar el análisis..."
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit — `prompts.py` | `build_analysis_prompt()` para 6 idiomas, sin ReAct artifacts, con silent context | Nuevos tests en `test_prompts.py` |
| Unit — `query_agent.py` | `_strip_data_sections()` con headers multi-idioma; `_format_output()` sin símbolos; `_check_cache()` sanitiza | Modificar tests existentes |
| Integration | Pipeline end-to-end: query → retrieve → analyze → output sin datos crudos | pytest con mock de LLM |
| Regression | Tests existentes de `build_agent_prompt()` y `MARKET_REACT_PROMPT` siguen pasando | pytest existente sin cambios |

## Migration / Rollout

No migration required. El cambio es backward-compatible:
- `AGENT_SYSTEM_PROMPT_TEMPLATE` y `build_agent_prompt()` se preservan intactos (ReAct prompt sigue disponible)
- Los aliases (`MARKET_REACT_PROMPT`, etc.) no se tocan
- El cache semántico se limpia en lectura (sanitización en `_check_cache`)
- Rollback: revertir `prompts.py` y `query_agent.py` con `git checkout`

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Test `test_format_output_list` espera `"AAPL" in formatted` — fallará | Medio | Se actualiza el test para esperar el nuevo mensaje genérico |
| Test `test_prompt_has_tool_instructions` espera `"query_stocks_tool" in rendered` | Bajo | Este test valida el ReAct prompt (no se modifica). Sin cambios. |
| LLM ignora instrucciones de silent context | Bajo | Safety net regex ampliado sigue aplicándose post-LLM |
| DeepSeek API key vacía → fallback | Medio | `_format_output()` nuevo es seguro (sin datos) |

## Open Questions

- [x] ¿El cache usa exact match o semantic similarity? (similarity — sanitizar en lectura es suficiente)
- [ ] ¿Requerimos truncar `data_context` si es muy largo para el context window de DeepSeek? (DeepSeek tiene 64K tokens — no crítico por ahora, pero considerar para futuras iteraciones con más datos)
