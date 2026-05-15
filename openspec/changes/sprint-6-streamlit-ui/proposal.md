# Sprint 6 Proposal: Streamlit UI Interface

## Change Name
`sprint-6-streamlit-ui`

## Overview

Implementar una interfaz web con Streamlit para el Dashboard_Bot_Bolsa, conectando la inteligencia financiera existente (agentes, RAG, ML) con una UI visual minimalista y de bajo consumo visual.

## Problem Statement

El proyecto tiene un backend completo con:
- Agente ReAct con herramientas de mercado
- RAG con memoria financiera y caché semántica
- Modelos ML para detección de anomalías y tendencias
- Análisis de sentimiento con Ollama
- Benchmarking de latencia

**PERO** los usuarios solo pueden interactuar via CLI (`run_agent.py`), lo cual limita la adopción y experiencia de uso.

## Proposed Solution

### Enfoque: Streamlit con Tema Oscuro Steel Blue

1. **Interfaz de Chat**: Campo de texto para consultas al agente
2. **Sidebar**: Métricas del sistema (status de Ollama, caché, benchmarks)
3. **Session State**: Persistencia del orchestrator entre interacciones
4. **Feedback Visual**: Spinners durante procesamiento

## Capabilities

### New Capabilities

1. **Streamlit Web App**
   - Aplicación web ejecutable con `streamlit run app.py`
   - Tema oscuro con acentos steel blue (#4682B4)
   - Diseño minimalista sin colores vibrantes

2. **Dashboard de Métricas en Sidebar**
   - Estado de conexión de Ollama
   - Estadísticas de caché (hits, misses, TTL)
   - Benchmarks de latencia recientes
   - Conteo de documentos en ChromaDB

3. **Interfaz de Chat**
   - Input de texto para queries
   - Historial de conversación
   - Indicadores de "pensando" durante procesamiento

4. **Session State Management**
   - Persistencia de MarketOrchestrator
   - Mantiene contexto entre recargas de página

## Affected Areas

- `src/ui/app.py` — Nueva aplicación Streamlit
- `src/ui/pages/` — Páginas adicionales (opcional)
- `src/ui/components/` — Componentes reutilizables
- `requirements.txt` — Agregar streamlit
- `src/config/__init__.py` — Settings de UI (opcional)
- `.streamlit/config.toml` — Configuración de tema

## Approach

1. **Setup**: Agregar streamlit a requirements.txt, crear config.toml con tema oscuro
2. **Básico**: Crear app.py con conexión básica al orchestrator
3. **UI**: Agregar sidebar con métricas, chat interface
4. **Feedback**: Implementar loading states
5. **Refinar**: CSS custom para steel blue, optimizar UX

## Risks

- Session state puede reinicializarse durante hot-reload en desarrollo
- Queries largas necesitan timeout apropiado
- Streamlit recrea el script en cada interacción → inicialización costosa del orchestrator

## Success Criteria

- ✅ App de Streamlit inicia sin errores
- ✅ Tema oscuro con acentos steel blue implementado
- ✅ Sidebar muestra métricas (status Ollama, stats de caché, latencia)
- ✅ Interfaz de chat permite hacer queries al MarketOrchestrator
- ✅ Indicadores de carga durante procesamiento de queries
- ✅ Session state persiste entre interacciones de página