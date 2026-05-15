# UI Performance Optimization Specification

## Purpose

Optimizaciones de rendimiento en el frontend del dashboard Streamlit para reducir tiempos de carga y mejorar la experiencia del usuario.

## ADDED Requirements

### Requirement: Sidebar Metrics Caching

La sidebar DEBE cachear las métricas del sistema para evitar llamadas redundantes a APIs en cada render.

#### Scenario: Metrics cached with TTL

- GIVEN el usuario visita el dashboard
- WHEN la sidebar se renderiza por primera vez
- THEN DEBE obtener métricas de Ollama, ChromaDB y Latency Tracker
- AND DEBE cachear estos datos con TTL de 30 segundos
- AND DEBE usar valores cacheados en renders subsecuentes dentro del TTL

#### Scenario: Cache invalidated after TTL

- GIVEN métricas cacheadas con más de 30 segundos de antigüedad
- WHEN la sidebar se renderiza
- THEN DEBE realizar nuevas llamadas a las APIs
- AND DEBE actualizar el cache con los nuevos valores

#### Scenario: Manual cache invalidation

- GIVEN el usuario presiona el botón "Re-indexar Datos"
- WHEN el proceso de re-indexado termina
- THEN DEBE invalidar el cache de métricas automáticamente
- AND DEBE forzar un nuevo fetch en el siguiente render

### Requirement: Lazy Orchestrator Initialization

El orchestrator DEBE inicializarse de forma lazy para no bloquear la carga inicial del dashboard.

#### Scenario: Dashboard loads without blocking

- GIVEN el usuario abre el dashboard
- WHEN la página inicial se renderiza
- THEN DEBE mostrar la UI inmediatamente sin esperar al orchestrator
- AND DEBE inicializar el orchestrator en background
- AND DEBE mostrar un indicador de "cargando" mientras persiste

#### Scenario: Query waits for orchestrator ready

- GIVEN el usuario envía una query antes de que el orchestrator esté listo
- WHEN presiona "Enviar"
- THEN DEBE esperar hasta que el orchestrator esté inicializado
- AND DEBE ejecutar la query normalmente una vez listo

### Requirement: Partial Reruns for Chat

El chat DEBE usar actualizaciones parciales en lugar de reruns completos del script.

#### Scenario: New message added without full rerun

- GIVEN el usuario envía una query y recibe respuesta
- WHEN la respuesta se agrega al historial
- THEN DEBE actualizar solo el contenedor del historial
- AND NO debe re-renderizar toda la página

### Requirement: Loading State Optimization

La UI DEBE mostrar estados de carga específicos y no genéricos.

#### Scenario: Contextual loading message

- GIVEN el usuario envía una query de acción
- WHEN el agente está procesando
- THEN DEBE mostrar "Analizando datos de mercado..." o similar
- AND NO debe mostrar "Por favor espere..."

#### Scenario: Skeleton placeholders

- GIVEN la sidebar se está cargando por primera vez
- WHEN los datos aún no están disponibles
- THEN DEBE mostrar skeleton loaders en lugar de espacio vacío
- AND DEBE mantener la estructura visual durante la carga