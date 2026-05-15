# Spec: Natural Language Agent Responses

## Purpose

Eliminar respuestas robóticas del agente. El sistema actual usa temperature=0.0 (misma respuesta siempre), genera formato ReAct interno que después se limpia con regex (frágil), y produce respuestas predecibles sin personalidad.

## Requirements

### Requirement: Response Variation

The agent SHALL produce varied responses for semantically equivalent queries, avoiding identical wording for the same information.

#### Scenario: Same data, different wording
- GIVEN the same market data context
- WHEN the agent answers two identical queries in the same session
- THEN the two responses SHALL NOT be identical in wording
- AND both SHALL be factually correct

### Requirement: No Raw ReAct Format

The agent output SHALL NOT contain any ReAct formatting artifacts (Thought:/Action:/Observation:/Answer:).

#### Scenario: Clean output
- GIVEN the agent generates a response
- WHEN the output is returned to the user
- THEN the output SHALL NOT contain "Thought:", "Action:", "Observation:", "Answer:", "Question:"
- AND the output SHALL be plain natural language

### Requirement: Natural Tone

The agent SHALL adopt a conversational, professional tone appropriate for financial analysis.

#### Scenario: Conversational answer
- GIVEN the agent has retrieved market data
- WHEN it formulates the answer
- THEN it SHALL use complete sentences
- AND SHALL avoid bullet points with technical prefixes
- AND SHALL explain numbers in context (e.g., "AAPL is up 3% this week" not "AAPL: +3%")

#### Scenario: Uncertainty handling
- GIVEN the agent cannot find relevant data
- WHEN it responds
- THEN it SHALL clearly state what it couldn't find
- AND SHALL suggest alternative queries

### Requirement: Temperature Variation

The system SHALL use a non-zero temperature (0.3-0.5 range) configurable via settings, to enable response variation while maintaining factual accuracy.

#### Scenario: Configurable temperature
- GIVEN the settings file
- WHEN the agent is initialized
- THEN it SHALL read `rag_llm_temperature` from settings
- AND use that value for the LLM

#### Scenario: Factual consistency at temperature 0.3
- GIVEN temperature is set to 0.3
- WHEN the agent answers a factual question (e.g., "What was AAPL closing price yesterday?")
- THEN the factual data SHALL be correct regardless of wording variation

## Non-Functional Requirements

### Performance
- Adding response variation SHALL NOT increase response latency beyond 10%

### Constraints
- Factual accuracy SHALL NOT be sacrificed for variation
- The response cleanup SHALL happen at the prompt level (LLM instructed not to use ReAct format), NOT via post-processing regex
