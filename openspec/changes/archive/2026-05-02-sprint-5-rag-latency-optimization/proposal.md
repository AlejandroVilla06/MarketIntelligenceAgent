# Sprint 5 Proposal: RAG Latency Optimization

## Change Name
`sprint-5-rag-latency-optimization`

## Overview

Optimizar el rendimiento del sistema RAG del Dashboard_Bot_Bolsa enfocándose en reducir el Time To First Token (TTFT) y el tiempo total de ejecución de la cadena RAG.

## Problem Statement

El sistema actual de agentes de mercado tiene latencia alta en las consultas RAG. Las métricas críticas que necesitan mejora:
- **TTFT (Time To First Token)**: Tiempo hasta que el primer token llega al cliente
- **Tiempo total de ejecución**: Desde que se envía la query hasta que llega la respuesta completa

Stack actual: Python + LangChain + Ollama + ChromaDB

## Proposed Solution

### Phase 1: Baseline de Medición
- Instrumentar la cadena RAG existente para medir latencias en cada etapa
- Definir benchmarks de rendimiento (TTFT, tiempo de query, tiempo de generation)
- Identificar cuellos de botella específicos

### Phase 2: Caché Semántica
- Implementar caché basada en similaridad semántica de queries
- Diseño extensible para soportar múltiples modelos (distintas versiones de Ollama, modelos externos)
- TTL configurable por tipo de query

## Capabilities

### New Capabilities

1. **RAG Latency Benchmarking**
   - Sistema de medición de latencia en tiempo real
   - Métricas por componente (retrieval, generation, prompt processing)
   - Dashboard de rendimiento

2. **Semantic Query Cache**
   - Cache de respuestas basado en similaridad semántica
   - Interface genérica para múltiples modelos
   -Invalidación basada en TTL y updates de datos

### Modified Capabilities

- Ninguno inicialmente. Los cambios son aditivos.

## Affected Areas

- `src/agents/retriever.py` - ChromaDB queries
- `src/agents/chains/` - LangChain chains
- `src/llm/` - Ollama connection
- Configuración de pipeline

## Approach

1. **Medir antes de optimizar**: Phase 1 establece baseline real
2. **Diseño extensible**: La caché debe ser agnóstica al modelo
3. **Iteración**: Empezar con caché simple (exact match + similaridad), iterar según resultados

## Risks

- Cache puede devolver resultados desactualizados si no se invalida correctamente
- Overhead de similaridad puede aumentar latencia en vez de reducirla
- Ollama tiene límites de concurrencia que pueden complicar el caching

## Success Criteria

- TTFT reducido en al menos 30% para queries frecuentes
- Tiempo total de ejecución reducido en al menos 25%
- Cache hit rate > 40% para queries similares
- Sin regresiones en calidad de respuestas