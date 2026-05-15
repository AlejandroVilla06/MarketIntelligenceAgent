# Model Cards — Market Intelligence Agent

> Documento técnico de especificación para cada agente del sistema de orquestación multi-mercado.
> Basado en el formato Google Model Cards (modelcards.withgoogle.com).

---

## Crypto Agent (CryptoSubOrchestrator)

### Identidad

| Campo | Valor |
|-------|-------|
| **Nombre** | Crypto Market Analyst |
| **Clase** | `CryptoSubOrchestrator` |
| **Módulo** | `src/market_orchestrator/crypto_sub.py` |
| **Arquetipo** | Sub-orchestrador especializado en criptomonedas |

### Modelo de Lenguaje

| Campo | Valor |
|-------|-------|
| **Modelo base** | `deepseek/deepseek-v4-flash` via OpenRouter |
| **Temperatura** | 0.3 |
| **Inicialización** | Lazy (bajo demanda en `_get_llm()`) |
| **Provider** | OpenAI-compatible (`ChatOpenAI` de LangChain) |
| **API Base** | `openai_api_base` desde configuración (default: OpenRouter) |
| **Fallback** | Sin LLM → devuelve datos crudos de CoinMarketCap |

### MCP Tools

| # | Tool | Descripción | Source |
|---|------|-------------|--------|
| 1 | `get_crypto_price(symbol)` | Precio, market cap, volumen 24h, cambio 24h/7d, supply | CoinMarketCap `quotes/latest` |
| 2 | `get_top_cryptos(limit)` | Top N criptos por capitalización de mercado | CoinMarketCap `listings/latest` |
| 3 | `get_crypto_global_metrics()` | Capitalización total, volumen 24h, dominancia BTC/ETH | CoinMarketCap `global-metrics/quotes/latest` |

**Fuente de datos**: CoinMarketCap Pro API (`pro-api.coinmarketcap.com/v1`). Plan base: 333 requests/día.

### Routing

| Campo | Valor |
|-------|-------|
| **Keywords** | `bitcoin`, `btc`, `ethereum`, `eth`, `crypto`, `cryptocurrency`, `solana`, `sol`, `xrp`, `cardano`, `ada`, `polkadot`, `dot`, `dogecoin`, `doge`, `avalanche`, `avax`, `chainlink`, `link`, `polygon`, `matic`, `uniswap`, `uni`, `coin`, `token`, `blockchain`, `defi`, `nft`, `mining`, `wallet`, `exchange`, `market cap`, `altcoin`, `stablecoin`, `usdt`, `usdc` |
| **Confianza mínima** | 0.80 (1 keyword match) |
| **Confianza alta** | 0.95 (≥2 keywords) |
| **Matching** | Substring exacto, case-insensitive |

### Widget

| Campo | Valor |
|-------|-------|
| **Componente** | `CryptoPriceCard` (`frontend/src/components/widgets/CryptoPriceCard.tsx`) |
| **Formato marker** | `[WIDGET:crypto]{json}[/WIDGET]` |
| **Campos** | `symbol`, `name?`, `price`, `change24h?`, `marketCap?`, `rank?`, `sparkline?` |
| **Rendering** | Card con borde lateral verde/rojo según cambio 24h, sparkline SVG (`SparklineChart`) |
| **Loading** | Skeleton de 3 líneas |
| **Parseo** | Regex sobre output crudo de CoinMarketCap |

### Idiomas Soportados

| Idioma | Código |
|--------|--------|
| Español | ES |
| English | EN |
| Français | FR |
| Deutsch | DE |
| Português | PT |
| Italiano | IT |

Detección automática vía `src/agents/prompts.py`. El LLM recibe instrucción explícita de responder en el mismo idioma de la consulta.

### Intención y Uso Previsto

El agente consulta datos en tiempo real de CoinMarketCap y los procesa con un LLM para generar análisis narrativo. Ideal para consultas sobre precios, tendencias, dominancia de mercado y métricas globales de criptomonedas. No debe usarse para trading automatizado ni como consejo financiero.

### Limitaciones Conocidas

- Plan base CoinMarketCap: 333 requests/día (compartido entre todas las herramientas)
- Sin datos históricos más allá de 24h/7d provistos por la API
- El sparkline no se genera actualmente desde el backend (campo opcional no poblado)
- LLM puede alucinar contexto si los datos crudos son insuficientes

---

## Macro Agent (MacroSubOrchestrator)

### Identidad

| Campo | Valor |
|-------|-------|
| **Nombre** | Macroeconomic Analyst |
| **Clase** | `MacroSubOrchestrator` |
| **Módulo** | `src/market_orchestrator/macro_sub.py` |
| **Arquetipo** | Sub-orchestrador especializado en macroeconomía |

### Modelo de Lenguaje

| Campo | Valor |
|-------|-------|
| **Modelo base** | `deepseek/deepseek-v4-flash` via OpenRouter |
| **Temperatura** | 0.3 |
| **Inicialización** | Lazy (bajo demanda en `_get_llm()`) |
| **Provider** | OpenAI-compatible (`ChatOpenAI` de LangChain) |
| **Fallback** | Sin LLM → devuelve datos crudos de FRED |

### MCP Tools

| # | Tool | Series FRED | Descripción |
|---|------|-------------|-------------|
| 1 | `get_gdp()` | `GDP` | Producto Interno Bruto de EE.UU. |
| 2 | `get_cpi()` | `CPIAUCSL` | Índice de Precios al Consumidor (inflación) |
| 3 | `get_unemployment()` | `UNRATE` | Tasa de desempleo |
| 4 | `get_federal_funds_rate()` | `FEDFUNDS` | Tasa de Fondos Federales efectiva |
| 5 | `get_treasury_yield_10y()` | `DGS10` | Rendimiento del Treasury a 10 años |
| 6 | `get_treasury_yield_2y()` | `DGS2` | Rendimiento del Treasury a 2 años |
| 7 | `get_macro_summary()` | Múltiples | Resumen de 5 indicadores clave (última observación c/u) |

**Fuente de datos**: FRED API (`api.stlouisfed.org/fred/series/observations`). Sin límite de rate conocido para API keys registradas.

### Routing

| Campo | Valor |
|-------|-------|
| **Keywords** | `gdp`, `economy`, `economic`, `macro`, `macroeconomics`, `inflation`, `cpi`, `consumer price`, `price index`, `unemployment`, `employment`, `jobs`, `labor`, `jobless`, `interest rate`, `fed rate`, `federal reserve`, `fed funds`, `treasury`, `bond yield`, `yield curve`, `dgs10`, `dgs2`, `recession`, `growth`, `gross domestic product`, `monetary policy`, `fiscal policy`, `stimulus` |
| **Confianza mínima** | 0.80 (1 keyword match) |
| **Confianza alta** | 0.95 (≥2 keywords) |
| **Matching** | Substring exacto, case-insensitive |

### Widget

| Campo | Valor |
|-------|-------|
| **Componente** | `MacroIndicator` (`frontend/src/components/widgets/MacroIndicator.tsx`) |
| **Formato marker** | `[WIDGET:macro]{json}[/WIDGET]` |
| **Campos** | `indicator`, `value`, `unit?`, `date?`, `previousValue?` |
| **Rendering** | Card con nombre del indicador, valor formateado, unidad, fecha, flecha ▲/▼ |
| **Loading** | Skeleton de 3 líneas |
| **Parseo** | Regex sobre output crudo de FRED; inferencia de unidad según tipo de indicador |

### Idiomas Soportados

| Idioma | Código |
|--------|--------|
| Español | ES |
| English | EN |
| Français | FR |
| Deutsch | DE |
| Português | PT |
| Italiano | IT |

### Intención y Uso Previsto

Agente especializado en datos macroeconómicos oficiales de la Reserva Federal. Responde consultas sobre PIB, inflación, empleo, tasas de interés y rendimientos de bonos del tesoro estadounidense. Diseñado para inversores, analistas y estudiantes que necesitan datos actualizados con contexto histórico.

### Limitaciones Conocidas

- Datos exclusivos de EE.UU. (no cubre otros países)
- La API FRED tiene latencia variable; algunas series se actualizan mensualmente
- El campo `previousValue` no se parsea actualmente desde el backend (siempre muestra ▲)
- Sin cobertura de leading indicators (PMI, consumer sentiment)

---

## Calculation Agent (CalculationExecutor)

### Identidad

| Campo | Valor |
|-------|-------|
| **Nombre** | Financial Calculator |
| **Clase** | `CalculationExecutor` |
| **Módulo** | `src/market_orchestrator/python_repl.py` |
| **Arquetipo** | Ejecutor de código Python financiero en sandbox |

### Modelo de Ejecución

| Campo | Valor |
|-------|-------|
| **Runtime** | Python REPL en subprocess (`repl_server.py`) |
| **Mecanismo** | `exec()` con `StringIO` para captura de stdout |
| **Timeout** | 30 segundos |
| **Seguridad** | AST-based validation + restricted globals + lista de imports permitidos |

### Librerías Permitidas

| Librería | Alias | Uso |
|----------|-------|-----|
| `numpy` | `np` | Álgebra lineal, estadística, arrays |
| `pandas` | `pd` | DataFrames, rolling windows, SMA/EMA |
| `scipy` | — | Optimización numérica, interpolación |
| `math` | — | Funciones matemáticas base |
| `statistics` | — | Media, mediana, desviación estándar |
| `decimal` | — | Precisión decimal financiera |
| `datetime` | — | Manejo de fechas |
| `itertools`/`collections` | — | Estructuras auxiliares |

### Restricciones de Seguridad

| Capa | Mecanismo |
|------|-----------|
| **AST validation** | `_is_safe(code)` parsea el AST, bloquea `eval()`, `exec()`, `open()`, `__import__`, `compile()` |
| **Blocked keywords** | `import os`, `import sys`, `import subprocess`, `import shutil`, `import socket`, `import requests`, `import httpx`, `import http`, `import pathlib`, `__import__`, `eval(`, `exec(`, `open(`, `__builtins__`, `compile(`, `getattr`, `setattr`, `delattr` |
| **Restricted globals** | Solamente builtins seguros habilitados (print, range, len, sum, max, min, etc.) |
| **30s timeout** | Timeout en el servidor MCP |
| **No file I/O** | Sin acceso a sistema de archivos |
| **No network** | Sin HTTP client, sockets, ni requests |

### Cálculos Predefinidos

| Cálculo | Trigger NLP | Fórmula implementada |
|---------|-------------|----------------------|
| **NPV** | `npv`, `net present value` | `sum(CF / (1+r)^t) - Initial` |
| **Sharpe Ratio** | `sharpe` | `(μ_annual - Rf) / σ_annual` |
| **Simple Moving Average** | `moving average`, `sma` | `rolling(window=5).mean()`, `rolling(window=10).mean()` |
| **IRR** | `irr`, `internal rate` | No implementado directamente (devuelve hint para usar `calculate_python`) |

### Widget

| Campo | Valor |
|-------|-------|
| **Componente** | `CalcResult` (`frontend/src/components/widgets/CalcResult.tsx`) |
| **Formato marker** | `[WIDGET:calc]{json}[/WIDGET]` |
| **Campos** | `formula`, `result` (number o string), `interpretation?` |
| **Rendering** | Card con nombre de fórmula, resultado numérico, interpretación textual |
| **Loading** | Skeleton de 3 líneas |
| **Interpretación** | Reglas hardcodeadas según fórmula (NPV > 0 ✅, Sharpe > 2 ⭐⭐⭐⭐⭐) |

### Cross-Session History

| Campo | Valor |
|-------|-------|
| **Método** | `get_recent_history(user_id, limit=10)` |
| **Backend** | Supabase (`conversations` + `messages`) |
| **Filtro** | Por `user_id` para aislamiento |
| **Formato** | Últimos N conversaciones, últimos 6 mensajes por conversación, truncados a 200 chars |
| **Cacheado** | No — consulta directa a Supabase en cada llamado |

### Routing

| Campo | Valor |
|-------|-------|
| **Keywords** | `calculate`, `calculation`, `compute`, `formula`, `npv`, `irr`, `sh root`, `var`, `value at risk`, `beta`, `alpha`, `standard deviation`, `volatility`, `correlation`, `covariance`, `regression`, `moving average`, `sma`, `ema`, `rsi`, `ratio`, `metric`, `analysis`, `what if`, `cálculo`, `calcular`, `fórmula` |
| **Confianza mínima** | 0.75 (1 keyword) |
| **Confianza alta** | 0.95 (≥2 keywords) |

### Intención y Uso Previsto

Ejecuta cálculos financieros en un entorno Python sandboxeado. Ideal para consultas numéricas que requieren fórmulas (NPV, Sharpe Ratio, SMA). No debe usarse para ejecutar código arbitrario ni acceder a datos externos.

### Limitaciones Conocidas

- Solo cálculos predefinidos (NPV, Sharpe, SMA) tienen templates; otros requieren código manual
- Sin visualización de distribuciones ni plots
- La interpretación del resultado es hardcodeada por fórmula
- Cross-session history solo disponible con Supabase configurado

---

## Stocks Agent (StocksSubOrchestrator) — Legacy Wrapper

### Identidad

| Campo | Valor |
|-------|-------|
| **Nombre** | Stock Market Analyst |
| **Clase** | `StocksSubOrchestrator` |
| **Módulo** | `src/market_orchestrator/stocks_sub.py` |
| **Arquetipo** | Wrapper transparente sobre pipeline existente |

### Pipeline Legacy (sin cambios)

```
StocksSubOrchestrator
  └─ MarketQueryAgent (src/agents/query_agent.py)
       ├─ MarketRAGRetriever (src/agents/retriever.py)
       │    ├─ ChromaDB (market_stocks, market_news, market_sentiment collections)
       │    ├─ Sentence Transformers (all-MiniLM-L6-v2)
       │    └─ Semantic Cache con similariedad ≥ 0.85
       ├─ LangChain con ChatOpenAI
       └─ yfinance (datos de mercado en tiempo real)
```

### Estado del Pipeline

| Componente | Estado | Líneas modificadas |
|------------|--------|-------------------|
| `StocksSubOrchestrator` | **NUEVO** (wrapper) | 52 líneas |
| `MarketQueryAgent` | **Intacto** | 0 |
| `MarketRAGRetriever` | **Intacto** | 0 |
| `query_agent.py` tests | **Intactos** | 18 tests |
| ChromaDB collections | **Intactas** | 0 |
| Semantic Cache | **Intacto** | 0 |
| LangChain prompts | **Intactos** | 0 |

### Routing

| Campo | Valor |
|-------|-------|
| **Keywords** | `stock`, `stocks`, `market`, `equity`, `equities`, `share`, `shares`, `aapl`, `msft`, `googl`, `nvda`, `amzn`, `tsla`, `meta`, `price`, `volume`, `rsi`, `market cap`, `pe ratio`, `dividend`, `earnings`, `revenue`, `profit`, `sec filing`, `ipo`, `acción`, `acciones`, `bolsa`, `precio`, `cotización` |
| **Confianza mínima** | 0.75 (1 keyword) |
| **Confianza media** | 0.80 (2 keywords) |
| **Confianza alta** | 0.95 (≥3 keywords) |

### Compatibilidad

| Aspecto | Detalle |
|---------|---------|
| **Streamlit legacy** | Compatible vía `ask()` y `get_status()` |
| **Multi-idioma** | ES, EN, FR, DE, PT, IT (detección automática en prompts) |
| **Semantic Cache** | Threshold 0.85, TTL 24h |
| **Streaming** | `ask_stream()` divide en tokens por espacio |
| **RAG** | 3 colecciones ChromaDB: stocks, news, sentiment |

### Widget

No implementa widget marker propio. El agente legacy devuelve texto plano analizado. El frontend puede parsear outputs estructurados si están presentes en el texto.

### Intención y Uso Previsto

Wrapper de compatibilidad que permite al RouterAgent tratar el pipeline RAG existente como un sub-orchestrador más. Consultas sobre acciones, mercados bursátiles, análisis fundamental y técnico. Pipeline probado con 18 tests existentes sin modificaciones.

### Limitaciones Conocidas

- No streaming nativo (solo token splitting simulado)
- Sin widget marker dedicado (hereda formato legacy)
- Dependencia de yfinance (sujeto a rate limits no oficiales)
- RAG latencia: ~1-3s por consulta (incluye embedding + retrieval + LLM)

---

## RouterAgent — Diagrama de Flujo de Routing

```
                    ┌──────────────────────┐
                    │    USER QUERY         │
                    │  "How is Bitcoin and  │
                    │   US GDP doing?"      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    RouterAgent       │
                    │   .route(query)      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Iterate sub-       │
                    │   orchestrators      │
                    │   calling            │
                    │   .can_handle(query) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Matches found?     │
                    └──────┬──────┬────────┘
                           │      │
                      ┌────▼──┐ ┌▼──────────┐
                      │ 0     │ │ 1          │
                      │ matches│ │ match      │
                      └───┬───┘ └─────┬──────┘
                          │           │
              ┌───────────▼──┐   ┌────▼──────┐
              │  ≥ 2 matches │   │ Confidence │
              │              │   │ ≥ 0.7?     │
              └───┬──────────┘   └──┬───┬─────┘
                  │                 │   │
                  │            ┌────▼┐ ┌▼────────┐
                  │            │ YES │ │ NO      │
                  │            └──┬──┘ └──┬──────┘
                  │               │       │
            ┌─────▼───────────────▼───────▼───────┐
            │          FALL-BACK MODE              │
            │  Query ALL sub-orchestrators         │
            │  Synthesize with LLM                 │
            └─────────────────┬───────────────────┘
                              │
                  ┌───────────▼───────────┐
                  │   DIRECT ROUTE        │
                  │   Delegate to best    │
                  │   sub-orchestrator    │
                  └───────────────────────┘
```

### Lógica de Decisión

```
1. can_handle(query) → (bool, confidence) para cada sub-orchestrator
2. Si 0 matches → FALLBACK (query all, synthesize)
3. Si 1 match Y confidence ≥ 0.7 → DIRECT (delegar al sub-orchestrador)
4. Si 1 match Y confidence < 0.7 → FALLBACK
5. Si ≥ 2 matches (MULTI-TOPIC) → FALLBACK forzado
```

### Thresholds de Confianza

| Sub-orchestrator | 1 keyword | 2 keywords | 3+ keywords |
|-----------------|-----------|------------|-------------|
| Crypto | 0.80 | 0.95 | 0.95 |
| Macro | 0.80 | 0.95 | 0.95 |
| Calculation | 0.75 | 0.95 | 0.95 |
| Stocks | 0.75 | 0.80 | 0.95 |

**Threshold global de ruteo directo**: 0.70 (constante `_CONFIDENCE_THRESHOLD` en `router_agent.py`).

---

## Arquitectura General

```
                    ┌─────────────────────────────┐
                    │     MarketOrchestrator       │
                    │   (src/market_orchestrator/  │
                    │    orchestrator.py)          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │        RouterAgent           │
                    │   (router_agent.py)          │
                    └──────┬──────┬──────┬────────┘
                           │      │      │
              ┌────────────▼┐ ┌───▼───┐ ┌▼───────────┐
              │  CryptoSub  │ │Macro  │ │Calculation  │
              │  Orchestrator│ │Sub    │ │Executor     │
              │  (crypto)   │ │Orch.  │ │(calc)       │
              └──────┬──────┘ └───┬───┘ └──────┬──────┘
                     │            │            │
              ┌──────▼────┐ ┌─────▼─────┐ ┌────▼──────┐
              │CoinMarket │ │FRED API   │ │Python REPL │
              │Cap API    │ │(Federal   │ │(numpy,     │
              │(3 tools)  │ │Reserve)   │ │pandas, etc)│
              └───────────┘ │(7 tools)  │ └────────────┘
                            └───────────┘

              ┌─────────────────────────────────────┐
              │  StocksSubOrchestrator (wraps       │
              │   MarketQueryAgent + ChromaDB RAG)  │
              └─────────────────────────────────────┘
```

### Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Orquestación** | FastAPI, LangChain |
| **Agentes** | ChatOpenAI (OpenRouter) + deepseek/deepseek-v4-flash |
| **MCP Framework** | `mcp.server.fastmcp` (Python MCP SDK) |
| **Vector DB** | ChromaDB + sentence-transformers (all-MiniLM-L6-v2) |
| **Datos stocks** | yfinance |
| **Datos crypto** | CoinMarketCap Pro API |
| **Datos macro** | FRED API (Federal Reserve) |
| **Cálculos** | Python REPL sandbox (AST validation) |
| **Persistencia** | Supabase (PostgreSQL + Auth) |
| **Frontend** | Next.js 14 (App Router), Tailwind CSS, shadcn/ui |
| **Widgets** | CryptoPriceCard, MacroIndicator, CalcResult, DataTable |
| **Testing** | pytest (397+ tests) |
| **Cache** | Semantic cache con threshold 0.85, TTL 24h |

---

*Documento generado a partir del código fuente. Última actualización: 2026-05-15.*
