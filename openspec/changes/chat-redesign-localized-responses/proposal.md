# Proposal: Chat Redesign & Localized Responses

## Intent

El usuario reporta dos problemas críticos:
1. **Diseño feo**: El chat está al fondo de la página, se ve antiestético
2. **Respuestas robotizadas en inglés**: El agente responde siempre en inglés aunque el usuario escriba en español

El objetivo es crear un diseño de chat moderno (estilo ChatGPT/Gemini) con respuestas naturales en el idioma del usuario.

## Scope

### In Scope
- Rediseñar layout del chat: input centrado, mensajes centrado, diseño limpio
- Posicionar input en zona visible (no al fondo)
- Implementar detección de idioma en el agente para responder en español
- Crear prompts con respuestas naturales y empáticas

### Out of Scope
- No cambiar la arquitectura del orchestrator
- No agregar nuevas funcionalidades de ML

## Capabilities

### New Capabilities
- `chat-modern-layout`: Layout moderno centrado con input visible
- `agent-language-localization`: Detectar idioma y responder en el idioma del usuario
- `natural-responses`: Prompts que generan respuestas naturales, no robotizadas

### Modified Capabilities
- `empathetic-agent`: Actualizar para responder en idioma del usuario
- `custom-sidebar`: Ya no aplica (sidebar removido)

## Approach

**Diseño**: Usar `st.container()` con CSS moderno, input fijo en zona visible, mensajes centrados con max-width.

**Idioma**: Modificar la creación del agente LangGraph para pasar el prompt localized según idioma detectado. El agente debe usar `MARKET_REACT_PROMPT_ES` cuando detecta español.

**Respuestas naturales**: Crear sistema de variación de respuestas, evitar formato técnico "Answer:".

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ui/app.py` | Modified | Nuevo layout centrado, CSS modernizado |
| `src/agents/query_agent.py` | Modified | Usar prompt localized según idioma, eliminar formato robot |
| `src/agents/chains/prompts.py` | Modified | Prompts con respuestas naturales |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Prompts en español degradan calidad técnica | Medium | Mantener versión inglés disponible |
| CSS rompe en diferentes tamaños de pantalla | Low | Testing responsive |

## Rollback Plan

git revert de los 3 archivos restaura el estado anterior.

## Success Criteria

- [ ] Chat se ve moderno y limpio, input visible en zona central
- [ ] Usuario escribe en español → respuesta en español
- [ ] Usuario escribe en inglés → respuesta en inglés
- [ ] Respuestas son naturales, no tienen formato "Answer:"