# Market Intelligence Agent

Terminal financiera inteligente multi-mercado con IA. Consulta acciones, criptomonedas y datos macroeconomicos en lenguaje natural, con analisis aumentado por RAG y modelos de lenguaje.

---

## Stack

| Capa | Tecnologia |
|------|-----------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | Next.js 14 / Tailwind CSS 4 / shadcn/ui |
| Base de datos | Supabase (Auth + PostgreSQL) |
| Vector store | ChromaDB (RAG semantico) |
| Agentes / LLM | LangChain + OpenAI / Anthropic / DeepSeek |
| MCP | CoinMarketCap (cripto), FRED (macroeconomia) |
| ML | Modelos de anomalias y tendencias (saved en `src/ml_models/saved/`) |

---

## Requisitos

- Python 3.11 o superior
- Node.js 18 o superior
- pnpm 10 o superior (ver `package.json` -> `packageManager`)

---

## Setup rapido (2 minutos)

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd MarketIntelligenceAgent

# 2. Backend: entorno virtual y dependencias
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# Edita .env con tus API keys (OpenAI, Supabase, CoinMarketCap, FRED, etc.)

# 4. Frontend: dependencias
cd frontend
pnpm install
cd ..

# 5. Arrancar (dos terminales)

# Terminal 1 — Backend (FastAPI)
python -m uvicorn src.api.app:create_app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend (Next.js)
cd frontend && pnpm dev
```

Abri [http://localhost:3000](http://localhost:3000) en el navegador.

---

## Estructura del proyecto

```
MarketIntelligenceAgent/
├── .env.example              # Template de variables de entorno
├── requirements.txt          # Dependencias Python
├── package.json              # Root workspace (pnpm)
├── pnpm-workspace.yaml       # Configuracion monorepo
├── pnpm-lock.yaml
│
├── src/
│   ├── api/                  # FastAPI — rutas, schemas, auth, middleware
│   │   ├── app.py            # App factory con lifespan (init/shutdown)
│   │   ├── deps.py           # Dependency injection
│   │   ├── errors.py         # Manejador global de errores
│   │   ├── middleware.py     # Logging de requests
│   │   ├── state.py          # SupabaseConversationStore
│   │   ├── auth/             # JWT validator, Supabase client, user service
│   │   ├── routes/           # health, auth, chat, conversations, status
│   │   └── schemas/          # Pydantic models
│   │
│   ├── agents/               # Capa de IA
│   │   ├── query_agent.py    # Agente principal de consulta
│   │   ├── retriever.py      # RAG retriever sobre ChromaDB
│   │   ├── embedding.py      # Embeddings multilingual
│   │   ├── user_context.py   # Contexto por usuario
│   │   ├── cache/            # Semantic cache + latency tracker
│   │   ├── chains/           # Prompts y market tools (LangChain)
│   │   ├── mcp/              # MCP servers (crypto, macro, REPL)
│   │   └── memory/           # Memoria conversacional
│   │
│   ├── market_orchestrator/  # Orquestador multi-mercado
│   │   ├── orchestrator.py   # MarketOrchestrator — entry point principal
│   │   ├── router_agent.py   # Router que decide que sub-agente llamar
│   │   ├── sub_orchestrator.py
│   │   ├── crypto_sub.py     # Sub-agente cripto
│   │   ├── stocks_sub.py     # Sub-agente acciones
│   │   ├── macro_sub.py      # Sub-agente macroeconomia
│   │   └── python_repl.py    # Python REPL seguro para analisis
│   │
│   ├── config/               # Config centralizada (settings)
│   ├── data_engine/          # ETL: scrapers, pipelines, validacion, storage
│   ├── ml_models/            # Modelos de ML (anomalias, tendencias)
│   ├── ui/                   # CLI / TUI (alternativa a frontend web)
│   └── utils/                # Logging, formateo, fechas
│
├── frontend/                 # Next.js 14 App Router
│   ├── src/
│   │   ├── app/              # Paginas (chat, login, signup, auth/callback)
│   │   ├── components/       # Widgets, UI components
│   │   ├── hooks/            # useChat
│   │   ├── lib/              # API client, Supabase (client/server), types
│   │   ├── stores/           # Zustand stores (chatStore, authStore)
│   │   └── types/            # Declaraciones de tipos
│   ├── tailwind.config.ts
│   └── package.json
│
├── tests/                    # Tests pytest
├── data/                     # Datos crudos y procesados
├── sql/                      # Migraciones y queries SQL
├── logs/                     # Logs de ejecucion
└── openspec/                 # Especificaciones SDD (Spec-Driven Development)
```

---

## API Endpoints

Todos los endpoints autenticados requieren header `Authorization: Bearer <token>` (JWT de Supabase).

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/api/health` | No | Health check del server |
| POST | `/api/auth/signup` | No | Registro con email y password |
| POST | `/api/auth/login` | No | Login con email y password |
| GET | `/api/auth/oauth/{provider}` | No | Obtener URL de OAuth (google, github) |
| GET | `/api/auth/callback` | No | Callback OAuth (intercambia code por session) |
| POST | `/api/auth/logout` | Si | Cerrar sesion |
| GET | `/api/auth/me` | Si | Obtener perfil del usuario actual |
| PUT | `/api/auth/me` | Si | Actualizar perfil del usuario actual |
| POST | `/api/auth/refresh` | Si* | Refrescar access token (usa refresh_token en body) |
| GET | `/api/status` | Si | Estado del orquestador y conteo de documentos |
| POST | `/api/chat` | Si | Enviar consulta (Q&A single response) |
| GET | `/api/chat/stream` | Si | Streaming SSE de la respuesta del LLM |
| POST | `/api/reset` | Si | Resetear orquestador (reindexar ChromaDB) |
| POST | `/api/conversations` | Si | Crear nueva conversacion |
| GET | `/api/conversations` | Si | Listar conversaciones (offset, limit) |
| GET | `/api/conversations/{id}` | Si | Obtener conversacion por ID |
| DELETE | `/api/conversations/{id}` | Si | Eliminar conversacion |

\* `/api/auth/refresh` usa el `refresh_token` en el body, no el access token.

---

## Comandos utiles

```bash
# Backend
python -m uvicorn src.api.app:create_app --reload  # Dev con hot-reload
pytest tests/                                        # Ejecutar tests
pytest tests/ -v                                     # Tests verbose
pytest tests/test_api_health.py                      # Test especifico

# Frontend
cd frontend
pnpm dev          # Dev server en :3000
pnpm build        # Build de produccion
pnpm start        # Servir build
pnpm lint         # Linter (TypeScript)
```

---

## Variables de entorno clave

El archivo `.env.example` contiene todas las variables necesarias. Las mas importantes:

| Variable | Descripcion |
|----------|-------------|
| `openai_api_key` | API key de OpenAI (o OpenRouter) |
| `supabase_url` / `supabase_key` | Credenciales de Supabase (auth + DB) |
| `coinmarketcap_api_key` | API key de CoinMarketCap (via MCP) |
| `fred_api_key` | API key de FRED (macroeconomia) |
| `anthropic_api_key` | API key de Anthropic (opcional) |
| `alpha_vantage_api_key` | API key de Alpha Vantage (acciones) |

---

## Licencia

Proyecto privado. Todos los derechos reservados.

## Contribucion

1. Crea un branch desde `main` con el formato `tipo/descripcion` (ej: `feat/mcp-fred-integration`)
2. Hace tus cambios siguiendo la arquitectura existente
3. Asegurate de que los tests pasen: `pytest tests/`
4. Abri un Pull Request describiendo que cambia y por que

Para reportar bugs o sugerir features, abri un issue en el repositorio.

---

## Arquitectura

El diseno sigue una arquitectura de micro-agentes con un orquestador central. Cada mercado (acciones, cripto, macro) tiene un sub-agente especializado. La capa de RAG sobre ChromaDB provee contexto aumentado, y los MCP servers encapsulan APIs externas. El frontend en Next.js se comunica via REST+SSE con el backend FastAPI.

Para una descripcion detallada de la arquitectura, patrones y decisiones de diseno, consulta `ARCHITECTURE.md` (proximamente).
