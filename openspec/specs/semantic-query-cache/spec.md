# Semantic Query Cache Specification

## Purpose

Caché de respuestas basado en similaridad semántica para reducir latencia de queries recurrentes. Diseño extensible para soportar múltiples modelos LLM.

## ADDED Requirements

### Requirement: Semantic Cache Interface

El sistema DEBE proporcionar una interface genérica para caching que sea agnóstica al modelo LLM usado.

#### Scenario: Cache con interface genérica

- GIVEN una query del usuario
- WHEN se consulta el cache
- THEN DEBE funcionar con cualquier modelo registrado (ollama, openai, etc.)
- AND DEBE permitir registrar nuevos modelos sin modificar código del cache

#### Scenario: Registrar modelo en cache

- GIVEN un nuevo modelo LLM configurado
- WHEN se inicializa el sistema de cache
- THEN DEBE poder registrar el modelo con su identificador
- AND DEBE guardar el modelo_id con cada entrada de cache

### Requirement: Similarity-Based Cache Lookup

El sistema DEBE buscar entradas en cache usando similaridad semántica de queries, no solo coincidencia exacta.

#### Scenario: Query similar encontrada

- GIVEN una query del usuario con vector de embedding
- WHEN se busca en el cache con threshold de similaridad >= 0.85
- THEN DEBE retornar la respuesta cacheada
- AND DEBE registrar cache_hit

#### Scenario: Query no encontrada en cache

- GIVEN una query con embedding
- WHEN la similaridad máxima con entradas existentes es < 0.85
- THEN DEBE ejecutar la cadena RAG completa
- AND DEBE almacenar la nueva query-response en cache

### Requirement: Cache Invalidation

El sistema DEBE proporcionar mecanismos de invalidación para mantener consistencia de datos.

#### Scenario: TTL expiration

- GIVEN una entrada de cache con TTL configurado
- WHEN el tiempo de vida expira
- THEN DEBE marcar la entrada como inválida
- AND DEBE no retornarla en búsquedas futuras

#### Scenario: Invalidación por update de datos

- GIVEN datos en ChromaDB fueron actualizados
- WHEN se detecta cambio en las collections consultadas
- THEN DEBE invalidar entradas de cache que usan esos datos
- AND DEBE permitir invalidación manual por collection

### Requirement: Extensible Cache Architecture

El sistema DEBE permitir extensiones para diferentes estrategias de cache sin modificar la interface core.

#### Scenario: Agregar nueva estrategia de cache

- GIVEN una nueva estrategia (ej: cache por usuario, cache por sesión)
- WHEN se implementa la interface CacheStrategy
- THEN DEBE poder integrarse sin cambios en el cache principal
- AND DEBE mantener compatibilidad con modelos existentes

#### Scenario: Modelo con parámetros diferentes

- GIVEN dos queries idénticas pero con temperatura diferente
- WHEN se consulta el cache
- THEN DEBE considerar los parámetros del modelo como parte de la key
- AND DEBE retornar cache solo si parámetros son equivalentes