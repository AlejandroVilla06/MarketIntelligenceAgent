# Agent Language Localization Specification

## Purpose

El agente debe detectar el idioma del usuario y responder en el mismo idioma con respuestas naturales.

## ADDED Requirements

### Requirement: Language Detection at Query Level

El sistema DEBE detectar el idioma del usuario ANTES de procesar la query.

#### Scenario: User writes in Spanish

- GIVEN el usuario escribe "¿cómo está Apple hoy?"
- WHEN el sistema procesa la query
- THEN DEBE detectar idioma como "es"
- AND DEBE usar prompt en español para la respuesta

#### Scenario: User writes in English

- GIVEN el usuario writes "how is Apple doing today?"
- WHEN el sistema procesa la query
- THEN DEBE detectar idioma como "en"
- AND DEBE usar prompt en inglés para la respuesta

### Requirement: Prompt Selection Based on Language

El sistema DEBE seleccionar el prompt según el idioma detectado.

#### Scenario: Spanish prompt used for Spanish query

- GIVEN idioma detectado es "es"
- WHEN se ejecuta el agente ReAct
- THEN DEBE usar MARKET_REACT_PROMPT_ES
- AND NO usar el prompt original en inglés

#### Scenario: English prompt used for English query

- GIVEN idioma detectado es "en"
- WHEN se ejecuta el agente ReAct
- THEN DEBE usar MARKET_REACT_PROMPT_EN
- AND NO usar el prompt original

### Requirement: Natural Response Format

Las respuestas DEBEN ser naturales, sin formato técnico robotizado.

#### Scenario: No "Answer:" prefix in response

- GIVEN el agente generó una respuesta
- WHEN se muestra al usuario
- THEN NO debe contener "Answer:" o formato "Thought: Action:"
- AND DEBE ser texto fluido y natural

#### Scenario: Response in user's language

- GIVEN el idioma detectado es español
- WHEN el agente genera la respuesta
- THEN DEBE generar la respuesta completamente en español
- AND DEBE usar terminología financiera en español

### Requirement: Fallback to User's Language

Si el agente no puede responder en el idioma del usuario, DEBE indicar la limitación.

#### Scenario: Agent cannot respond in detected language

- GIVEN idioma detectado no es español ni inglés
- WHEN el agente genera la respuesta
- THEN DEBE responder en inglés por defecto
- AND DEBE mantener tono amigable