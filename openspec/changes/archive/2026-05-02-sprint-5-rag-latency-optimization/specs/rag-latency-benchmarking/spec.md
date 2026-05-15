# RAG Latency Benchmarking Specification

## Purpose

Sistema de medición de latencia para la cadena RAG del Dashboard_Bot_Bolsa. Proporciona métricas en tiempo real de TTFT y tiempo total de ejecución por componente.

## ADDED Requirements

### Requirement: Latency Instrumentation

El sistema DEBE instrumentar cada componente de la cadena RAG para registrar tiempos de ejecución con precisión de milisegundos.

#### Scenario: Medir latencia de retrieval

- GIVEN una query del usuario al agente RAG
- WHEN el sistema ejecuta retrieval en ChromaDB
- THEN DEBE registrar tiempo de inicio y fin del retrieval
- AND DEBE almacenar la diferencia como retrieval_latency_ms

#### Scenario: Medir latencia de generation

- GIVEN una respuesta del retriever con context
- WHEN el sistema envía el prompt a Ollama
- THEN DEBE registrar tiempo hasta primer token (TTFT)
- AND DEBE registrar tiempo hasta último token (total generation)

#### Scenario: Agregar latencia total de cadena

- GIVEN todas las etapas de la cadena completadas
- WHEN se calcula la suma de todas las latencias
- THEN DEBE exponer una métrica total_latency_ms
- AND DEBE incluir overhead de red y serialización

### Requirement: Benchmark Collection

El sistema DEBE almacenar métricas de latencia para análisis histórico y detección de regresiones.

#### Scenario: Guardar métricas por query

- GIVEN una query completada (éxito o error)
- WHEN la cadena RAG termina
- THEN DEBE guardar: query_id, timestamp, latencias por componente, modelo usado
- AND DEBE permitir consultas por rango de fechas

#### Scenario: Calcular percentiles

- GIVEN un conjunto de métricas de al menos 100 queries
- WHEN se solicita statistics
- THEN DEBE calcular p50, p90, p99 para cada componente
- AND DEBE identificar outliers (>2 desvíos estándar)

### Requirement: TTFT Measurement

El sistema DEBE medir Time To First Token como métrica crítica de rendimiento.

#### Scenario: TTFT en streaming

- GIVEN una request a Ollama con streaming enabled
- WHEN el primer token llega al cliente
- THEN DEBE registrar el tiempo como ttft_ms
- AND DEBE reportar esta métrica independientemente del tiempo total

#### Scenario: TTFT como KPI principal

- GIVEN métricas de latencia acumuladas
- WHEN se genera dashboard de rendimiento
- THEN DEBE mostrar TTFT como métrica principal
- AND DEBE comparar contra baseline de Sprint 4