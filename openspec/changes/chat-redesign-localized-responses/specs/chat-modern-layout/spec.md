# Chat Modern Layout Specification

## Purpose

Diseño de chat moderno estilo ChatGPT con layout centrado y input visible.

## ADDED Requirements

### Requirement: Centered Chat Layout

El chat DEBE tener un diseño centrado con mensajes y input en el centro de la pantalla.

#### Scenario: Messages centered with max-width

- GIVEN la aplicación iniciada con historial de chat
- WHEN se renderizan los mensajes
- THEN DEBEN estar centrados con max-width de 700px
- AND DEBEN tener padding adecuado a los lados

#### Scenario: Input visible in central area

- GIVEN el usuario abre el dashboard
- WHEN la página carga
- THEN el input debe estar visible en la zona central de la pantalla (no al fondo)
- AND DEBE tener suficiente padding inferior

### Requirement: Clean Visual Design

El chat DEBE tener un diseño limpio sin elementos innecesarios.

#### Scenario: No sidebar visible

- GIVEN la aplicación iniciada
- WHEN se renderiza
- THEN NO debe mostrar sidebar nativa de Streamlit

#### Scenario: Welcome screen with centered content

- GIVEN no hay historial de chat
- WHEN la página carga
- THEN DEBE mostrar mensaje de bienvenida centrado

### Requirement: Modern Message Bubbles

Los mensajes DEBEN tener diseño de bubbles modernos.

#### Scenario: User message styled

- GIVEN el usuario envió un mensaje
- WHEN se renderiza
- THEN DEBE tener background oscuro, border-radius suave
- AND DEBE alinearse a la derecha/derecha-centro

#### Scenario: Assistant message styled

- GIVEN el agente respondió
- WHEN se renderiza
- THEN DEBE tener diseño limpio sin background excesivo
- AND DEBE estar alineado a la izquierda/centro-izquierda