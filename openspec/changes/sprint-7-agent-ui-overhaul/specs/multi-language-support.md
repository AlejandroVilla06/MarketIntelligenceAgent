# Spec: Multi-Language Support

## Purpose

Agregar detección robusta de cualquier idioma en las queries del usuario y capacidad de respuesta en ese mismo idioma. Reemplazar la detección actual por keywords (solo ES/EN) con un detector basado en modelos de lenguaje.

## Requirements

### Requirement: Language Detection

The system SHALL detect the language of any user query using a statistical language detection library.

#### Scenario: Detect Spanish
- GIVEN a user query containing Spanish text
- WHEN `detect_language()` is called
- THEN it SHALL return the ISO 639-1 code for Spanish (`"es"`)

#### Scenario: Detect English
- GIVEN a user query containing English text
- WHEN `detect_language()` is called
- THEN it SHALL return `"en"`

#### Scenario: Detect French
- GIVEN a user query "Quel est le prix de l'action Apple?"
- WHEN `detect_language()` is called
- THEN it SHALL return `"fr"`

#### Scenario: Detect Portuguese
- GIVEN a user query "Qual é o sentimento do mercado para NVDA?"
- WHEN `detect_language()` is called
- THEN it SHALL return `"pt"`

#### Scenario: Detect German
- GIVEN a user query "Wie hat sich die Aktie von Tesla entwickelt?"
- WHEN `detect_language()` is called
- THEN it SHALL return `"de"`

#### Scenario: Fallback on detection failure
- GIVEN a very short or ambiguous query (e.g., "AAPL")
- WHEN `detect_language()` is called
- THEN it SHALL return `"en"` as default fallback

### Requirement: Multi-Language Response

The agent SHALL generate responses in the same language as the user query.

#### Scenario: Response in Spanish
- GIVEN a query detected as Spanish
- WHEN the agent generates a response
- THEN the system prompt SHALL instruct the LLM to respond in Spanish
- AND the output SHALL be in Spanish

#### Scenario: Response in French
- GIVEN a query detected as French
- WHEN the agent generates a response
- THEN the system prompt SHALL instruct the LLM to respond in French

#### Scenario: Language-agnostic capability
- GIVEN the agent is initialized
- WHEN the user switches languages mid-conversation
- THEN the agent SHALL detect each query independently
- AND respond in the language of the latest query

### Requirement: Prompt Selection

The system SHALL dynamically construct system prompts that include the detected language as a parameter, rather than maintaining separate prompt templates per language.

#### Scenario: Dynamic language prompt
- GIVEN a detected language code `"fr"`
- WHEN the system prompt is constructed
- THEN it SHALL include `"You MUST respond in French"` as an instruction
- AND the rest of the prompt SHALL remain in English (tool descriptions stay English)

## Non-Functional Requirements

### Performance
- Language detection SHALL complete in under 50ms
- The detection library SHALL be loaded lazily (first call)

### Reliability
- If the detection library fails to load, the system SHALL fall back to keyword-based detection
- If the detected language is not supported by the LLM, the system SHALL fall back to English
