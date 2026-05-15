# Sprint 6 Design: Streamlit UI

## Architecture Decisions

### AD-1: Streamlit como Framework de UI

**Decision**: Usar Streamlit en lugar de Flask/Django o Next.js

**Rationale**:
- ✅ Integración nativa con Python (el stack del proyecto)
- ✅ Desarrollo rápido - no requiere frontend separad
- ✅ Soporte nativo para session state
- ✅ Theming oscuro configurable
- ✅ Components nativos para inputs, métricas, spinners

**Alternatives Considered**:
- Flask + HTML template: Más control pero requiere desarrollo frontend
- Next.js: Excesivo para este proyecto (ya hay config en settings)

### AD-2: Session State para Orchestrator

**Decision**: Almacenar MarketOrchestrator en st.session_state para persistencia

**Rationale**:
- ✅ API nativa de Streamlit para estado
- ✅ Mantiene el orchestrator indexado entre interacciones
- ✅ Evita re-indexado costoso en cada query

**Implementation**:
```python
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MarketOrchestrator()
    st.session_state.orchestrator.setup()
```

### AD-3: Tema Oscuro via config.toml + Custom CSS

**Decision**: Configurar tema oscuro en .streamlit/config.toml + CSS adicional para steel blue

**Rationale**:
- ✅ config.toml ofrece configuración base del tema
- ✅ Custom CSS permite precisión en acentos específicos
- ✅ Separation of concerns: config vs styling

**Implementation**:
- config.toml: `theme.base = "dark"`
- app.py: `st.markdown()` con CSS para acentos #4682B4

### AD-4: Métricas del Sidebar como Funciones de Utility

**Decision**: Crear funciones helper en `src/ui/utils.py` para obtener métricas

**Rationale**:
- ✅ Reutilizable entre diferentes páginas
- ✅ Separa lógica de UI de lógica de métricas
- ✅ Facilita testing

**Functions**:
- `get_ollama_status()` → connected/disconnected/unavailable
- `get_cache_stats()` → dict con hits, misses, hit_rate
- `get_document_counts()` → dict con counts por colección
- `get_latency_metrics()` → dict con TTFT, p50, p90, p99

### AD-5: Loading State con st.spinner

**Decision**: Usar `st.spinner("Pensando...")` durante procesamiento de queries

**Rationale**:
- ✅ API nativa de Streamlit
- ✅ UX clara: usuario sabe que hay procesamiento en curso
- ✅ Bloquea input automáticamente

**Implementation**:
```python
with st.spinner("Analizando tu consulta..."):
    response = orchestrator.ask(query)
```

## Component Structure

```
src/ui/
├── app.py              # Main Streamlit app (entry point)
├── components/
│   ├── chat.py         # Chat interface component
│   ├── sidebar.py      # Sidebar metrics component
│   └── loading.py      # Loading indicator helpers
├── utils/
│   └── metrics.py      # Metrics retrieval functions
└── styles/
    └── theme.py        # Custom CSS for steel blue
```

## Data Flow

```
User Input → st.text_input → st.session_state.orchestrator.ask()
                                    ↓
                            MarketOrchestrator
                                    ↓
                            MarketQueryAgent
                                    ↓
                            RAG + Cache + LLM
                                    ↓
                            Response String
                                    ↓
                        st.markdown(response)
```

## Key Technical Details

### 1. Imports Correctos para el Backend
```python
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.orchestrator import MarketOrchestrator
from src.config import settings
```

### 2. Configuración de Tema
**.streamlit/config.toml**:
```toml
[theme]
base = "dark"
primaryColor = "#4682B4"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
```

### 3. CSS Custom para Steel Blue
```python
st.markdown("""
<style>
    .stButton > button {
        background-color: #4682B4;
    }
    .accent {
        color: #4682B4;
    }
</style>
""", unsafe_allow_html=True)
```

## Testing Strategy

- Unit tests para funciones en utils/metrics.py
- Integration test: verificar que app.py puede importar orchestrator
- Manual test: ejecutar `streamlit run app.py` y verificar UI

## Dependencies to Add

```
streamlit>=1.30.0
```

(ya existe en requirements.txt - verificar)