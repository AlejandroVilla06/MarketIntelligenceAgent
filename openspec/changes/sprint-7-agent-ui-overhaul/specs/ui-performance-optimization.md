# Spec: UI Performance Optimization

## Purpose

Optimizar el dashboard para reducir tiempos de carga y evitar rerenders innecesarios. El sistema actual inicializa el orchestrator eager (typing en carga), no cachea métricas repetitivas, y hace rerenders completos en cada interacción.

## Requirements

### Requirement: Lazy Orchestrator Initialization

The orchestrator SHALL be initialized only when the user submits their first query, not on page load.

#### Scenario: Dashboard loads without orchestrator
- GIVEN the user opens the dashboard
- WHEN the page loads
- THEN the orchestrator SHALL NOT be initialized yet
- AND the welcome screen SHALL display immediately
- AND the page SHALL load in under 1 second

#### Scenario: First query triggers initialization
- GIVEN the dashboard is loaded without orchestrator
- WHEN the user submits their first query
- THEN the orchestrator SHALL be initialized
- AND a loading indicator SHALL display during initialization
- AND the query SHALL be processed after initialization

### Requirement: Metrics Caching

System metrics (document counts, latency stats) SHALL be cached with a TTL to avoid redundant calls to ChromaDB.

#### Scenario: Cached metrics
- GIVEN the sidebar requests document counts
- WHEN `get_document_counts()` is called
- THEN the result SHALL be cached with `@st.cache_data(ttl=30)`
- AND subsequent calls within 30 seconds SHALL return cached data

#### Scenario: Cache invalidation
- GIVEN the user triggers a data refresh
- WHEN they click "Refresh Data"
- THEN the cache SHALL be cleared
- AND fresh data SHALL be loaded

### Requirement: Session State Optimization

The system SHALL minimize Streamlit rerenders by using `st.fragment` for independent UI sections.

#### Scenario: Fragment-based sidebar
- GIVEN the sidebar displays metrics
- WHEN the user sends a chat message
- THEN only the chat area SHALL rerender
- AND the sidebar SHALL NOT rerender

#### Scenario: Streaming responses
- GIVEN the agent is generating a response
- WHEN the LLM streams tokens
- THEN the UI SHALL display tokens incrementally
- AND SHALL NOT block the UI

### Requirement: Asset Loading

CSS and static assets SHALL be loaded efficiently.

#### Scenario: External CSS
- GIVEN the dashboard loads
- WHEN CSS is applied
- THEN the external `dashboard.css` SHALL be loaded via `st.markdown` with `<link>` or inline read
- AND no CSS SHALL be hardcoded in Python strings

## Non-Functional Requirements

### Performance Targets
- Initial page load: < 1 second (from ~5s current)
- Chat response display: < 500ms overhead beyond LLM latency
- Sidebar metrics: < 100ms (cached)

### Constraints
- No external caching infrastructure (Redis, Memcached)
- Only Streamlit-native caching (`@st.cache_data`, `st.fragment`, `st.session_state`)
