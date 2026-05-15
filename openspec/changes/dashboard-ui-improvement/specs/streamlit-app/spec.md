# Delta for Streamlit App

## MODIFIED Requirements

### Requirement: Sidebar Metrics Dashboard

La barra lateral DEBE mostrar métricas del sistema en tiempo real con diseño profesional, soporte de cacheo y componentes custom.

(Previously: La barra lateral DEBE mostrar métricas del sistema en tiempo real.)

#### Scenario: Sidebar displays Ollama status

- GIVEN la aplicación iniciada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar estado de conexión de Ollama (conectado/desconectado)
- AND DEBE actualizarse automáticamente cada 30 segundos
- AND DEBE usar indicadores visuales de color según estado

#### Scenario: Sidebar displays cache stats

- GIVEN la aplicación iniciada con caché habilitada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar: hit count, miss count, hit rate percentage
- AND DEBE actualizarse después de cada query
- AND DEBE usar tarjetas visuales para mostrar métricas

#### Scenario: Sidebar displays document counts

- GIVEN la aplicación iniciada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar cantidad de documentos en cada colección ChromaDB:
  - market_stocks
  - market_news
  - market_sentiment
- AND DEBE mostrar en tarjetas con diseño profesional

#### Scenario: Sidebar displays latency benchmarks

- GIVEN la aplicación iniciada
- WHEN el usuario abre la sidebar
- THEN DEBE mostrar últimos benchmarks de latencia:
  - TTFT promedio
  - Latencia total promedio
  - P50, P90, P99

#### Scenario: Sidebar uses custom container

- GIVEN la aplicación iniciada
- WHEN la sidebar se renderiza
- THEN DEBE usar componentes custom con st.container()
- AND DEBE tener secciones colapsables
- AND DEBE mantener jerarquía visual clara

### Requirement: Chat Interface

La interfaz DEBE proporcionar un campo de chat para enviar queries al agente con respuestas empáticas y soporte multilingüe.

(Previously: La interfaz DEBE proporcionar un campo de chat para enviar queries al agente.)

#### Scenario: User enters query

- GIVEN la aplicación con el campo de input visible
- WHEN el usuario escribe una query en el campo de texto
- AND presiona Enter
- THEN DEBE enviar la query al MarketOrchestrator
- AND DEBE mostrar el resultado en la pantalla
- AND DEBE detectar el idioma del usuario

#### Scenario: Chat shows loading indicator

- GIVEN el usuario envió una query
- WHEN el agente está procesando la solicitud
- THEN DEBE mostrar un indicador visual contextual ("Analizando datos de mercado...")
- AND DEBE deshabilitar el input hasta que termine

#### Scenario: Chat displays response

- GIVEN el agente retornó una respuesta
- WHEN la respuesta está disponible
- THEN DEBE mostrar el texto de la respuesta en el idioma del usuario
- AND DEBE usar un tono amigable y empático
- AND DEBE permitir scroll si es larga

#### Scenario: Chat history persists

- GIVEN múltiples queries enviadas
- WHEN el usuario escribe una nueva query
- THEN DEBE mantener el historial de preguntas y respuestas anteriores
- AND DEBE mostrarlas en orden cronológico

#### Scenario: Agent responds in user's language

- GIVEN el usuario envía una query en español
- WHEN el agente genera la respuesta
- THEN DEBE responder completamente en español
- AND DEBE usar tono amigable y empático

### Requirement: Professional Visual Design

La interfaz DEBE usar un diseño profesional con jerarquía visual clara y componentes bien estructurados.

#### Scenario: Visual hierarchy is clear

- GIVEN el dashboard renderizado
- WHEN el usuario observa la interfaz
- THEN DEBE distinguir claramente entre títulos, métricas y contenido
- AND DEBE usar spacing consistente de 16px entre secciones
- AND DEBE usar tipografía con diferentes tamaños para niveles

#### Scenario: Theme colors applied correctly

- GIVEN la configuración de tema en config.toml
- WHEN la interfaz se renderiza
- THEN DEBE usar la paleta de colores del tema oscuro
- AND DEBE usar steel blue (#4682B4) para elementos interactivos
- AND DEBE usar verde/rojo/amarillo para estados

#### Scenario: Custom CSS for components

- GIVEN CSS adicional en la aplicación
- WHEN se renderizan elementos de Streamlit
- THEN DEBE usar estilos custom para botones, inputs y mensajes
- AND DEBE mantener consistencia visual en toda la interfaz

## ADDED Requirements

### Requirement: Performance Optimization

El dashboard DEBE optimizar el rendimiento para tiempos de carga rápidos.

#### Scenario: Dashboard loads quickly

- GIVEN el usuario abre el dashboard
- WHEN la página inicial se renderiza
- THEN DEBE mostrar la UI inmediatamente
- AND DEBE inicializar el orchestrator en background
- AND DEBE no bloquear la carga con operaciones pesadas

#### Scenario: Metrics cached appropriately

- GIVEN métricas obtenidas previamente
- WHEN la sidebar se renderiza
- THEN DEBE usar valores cacheados si tienen menos de 30 segundos
- AND DEBE invalidar cache después de re-indexar datos