# Streamlit App Specification

## Purpose

Interfaz web Streamlit para el Dashboard_Bot_Bolsa que permite interacturar visualmente con el agente de inteligencia financiera.

## ADDED Requirements

### Requirement: Streamlit App Initialization

El sistema DEBE proporcionar una aplicación Streamlit funcional que se conecte al backend existente.

#### Scenario: App launches without errors

- GIVEN el archivo app.py con la configuración correcta
- WHEN el usuario ejecuta `streamlit run app.py`
- THEN DEBE iniciar la aplicación web sin errores de Python
- AND DEBE estar disponible en http://localhost:8501

#### Scenario: App imports orchestrator

- GIVEN la aplicación Streamlit iniciada
- WHEN se importa el módulo src.agents.orchestrator
- THEN DEBE poder instanciar MarketOrchestrator
- AND DEBE tener acceso a los métodos ask() y get_status()

### Requirement: Dark Theme with Steel Blue Accents

La interfaz DEBE usar un tema oscuro con acentos en steel blue (#4682B4) para minimizar la fatiga visual.

#### Scenario: Theme configuration applied

- GIVEN la configuración de Streamlit en .streamlit/config.toml
- WHEN la aplicación inicia
- THEN DEBE mostrar fondo oscuro (non-white)
- AND DEBE mostrar acentos en steel blue (#4682B4) en botones y elementos destacados

#### Scenario: Custom CSS for steel blue

- GIVEN CSS adicional en la aplicación
- WHEN se renderizan elementos de Streamlit
- THEN los acentos visuales deben usar steel blue (#4682B4)
- AND NO deben usar colores vibrantes o saturados

### Requirement: Sidebar Metrics Dashboard

La barra lateral DEBE mostrar métricas del sistema en tiempo real.

#### Scenario: Sidebar displays Ollama status

- GIVEN la aplicación iniciada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar estado de conexión de Ollama (conectado/desconectado)
- AND DEBE actualizarse automáticamente

#### Scenario: Sidebar displays cache stats

- GIVEN la aplicación iniciada con caché habilitada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar: hit count, miss count, hit rate percentage
- AND DEBE actualizarse después de cada query

#### Scenario: Sidebar displays document counts

- GIVEN la aplicación iniciada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar cantidad de documentos en cada colección ChromaDB:
  - market_stocks
  - market_news
  - market_sentiment

#### Scenario: Sidebar displays latency benchmarks

- GIVEN la aplicación iniciada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar últimos benchmarks de latencia:
  - TTFT promedio
  - Latencia total promedio
  - P50, P90, P99

### Requirement: Chat Interface

La interfaz DEBE proporcionar un campo de chat para enviar queries al agente.

#### Scenario: User enters query

- GIVEN la aplicación con el campo de input visible
- WHEN el usuario escribe una query en el campo de texto
- AND presiona Enter
- THEN DEBE enviar la query al MarketOrchestrator
- AND DEBE mostrar el resultado en la pantalla

#### Scenario: Chat shows loading indicator

- GIVEN el usuario envió una query
- WHEN el agente está procesando la solicitud
- THEN DEBE mostrar un indicador visual de "pensando" / spinner
- AND DEBE deshabilitar el input hasta que termine

#### Scenario: Chat displays response

- GIVEN el agente retornó una respuesta
- WHEN la respuesta está disponible
- THEN DEBE mostrar el texto de la respuesta
- AND DEBE permitir-scroll si es larga

#### Scenario: Chat history persists

- GIVEN múltiples queries enviadas
- WHEN el usuario escribe una nueva query
- THEN DEBE mantener el historial de preguntas y respuestas anteriores
- AND DEBE mostrarlas en orden cronológico

### Requirement: Session State Management

El estado DEBE persistir entre interacciones de la página para mantener el contexto del orchestrator.

#### Scenario: Orchestrator persists in session state

- GIVEN la aplicación iniciada por primera vez
- WHEN se crea el MarketOrchestrator
- THEN DEBE almacenarse en st.session_state
- AND DEBE mantenerse entre recargas de la página

#### Scenario: Query history persists in session

- GIVEN el usuario envió queries anteriores
- WHEN recarga la página del navegador
- THEN DEBE mantener el historial de conversación
- AND DEBE mostrar las queries previas al usuario

#### Scenario: Orchestrator reuses existing instance

- GIVEN ya existe un orchestrator en session_state
- WHEN se procesa una nueva query
- THEN DEBE reutilizar la instancia existente
- AND NO debe crear una nueva instancia (para evitar re-indexado)