# Exploration: Multi-Market Orchestration with MCP Tools

## Current State

### Orchestrator Architecture (`src/agents/orchestrator.py`)

The current `MarketOrchestrator` is a **monolithic coordinator** with these responsibilities:

1. **Init** — stores `persist_directory` and `model_name` params
2. **Setup** — initializes `StorageInterface` → `MarketRAGRetriever` (ChromaDB) → `MarketQueryAgent` (LLM), loads Parquet data into ChromaDB, seeds demo data if empty
3. **Ask** — delegates to `MarketQueryAgent.run(query)`, handles memory injection for external history
4. **Ask Stream** — async generator variant using `agent.run_stream(query)`
5. **Reset** — clears ChromaDB + agent memory
6. **Get Status** — returns setup state + collection counts

**Flow**: `ask()` → auto-setup if needed → `agent.run(query)` → `_retrieve_raw_data()` (ChromaDB query) → `_generate_analysis()` (LLM with Silent Context pattern)

### Query Agent (`src/agents/query_agent.py`)

Two-stage pipeline (NOT a ReAct agent despite the docstring):
- **Stage 1**: `_retrieve_raw_data()` — queries ChromaDB collections (stocks/news/sentiment) based on keyword detection
- **Stage 2**: `_generate_analysis()` — sends raw data as "Silent Context" in user message + executive analysis system prompt to LLM

The agent does NOT use LangChain tools at runtime. The `market_tools.py` defines `@tool` wrappers but they're only used in the ReAct prompt template path (legacy), not in the current `run()` flow.

### Data Sources
- **Stocks**: yfinance, Alpha Vantage, Polygon.io (via `stock_pipeline.py`)
- **News**: RSS feeds, NewsAPI (via `news_pipeline.py`)
- **Sentiment**: TextBlob, VADER, Ollama/Llama (via sentiment pipeline)
- **Storage**: Polars DataFrames → Parquet files → ChromaDB vectors

### Key Files Affected
- `src/agents/orchestrator.py` — monolithic orchestrator (312 lines)
- `src/agents/query_agent.py` — two-stage pipeline agent (868 lines)
- `src/agents/chains/market_tools.py` — LangChain @tool wrappers (637 lines)
- `src/agents/chains/prompts.py` — prompt templates (345 lines)
- `src/agents/retriever.py` — ChromaDB retriever (673 lines)
- `src/config/__init__.py` — settings with Pydantic (466 lines)
- `src/api/routes/chat.py` — FastAPI chat endpoints (104 lines)
- `src/api/deps.py` — orchestrator singleton DI (62 lines)
- `src/data_engine/pipelines/stock_pipeline.py` — data source pattern (636 lines)

### Current Limitations

1. **Single-domain**: Only handles stocks/equities. No crypto, macro, or custom calculations
2. **No routing**: All queries go through the same pipeline regardless of domain
3. **No MCP integration**: Zero MCP tools, no protocol support
4. **Tight coupling**: Orchestrator directly instantiates retriever + agent, no abstraction for sub-domains
5. **Keyword-based collection selection**: `_retrieve_raw_data()` uses crude keyword matching to pick which ChromaDB collection to query
6. **Tools defined but unused**: `market_tools.py` defines 7 LangChain tools but `query_agent.py` doesn't use them (uses direct retriever calls instead)

---

## Approaches

### Approach 1: MCP-Based Hierarchical Orchestrator

Replace the monolithic orchestrator with a hierarchical pattern where a router delegates to domain-specific sub-orchestrators, each backed by MCP tools.

**Architecture**:
```
MarketOrchestrator (hierarchical)
├── RouterAgent (LLM-based intent classification)
├── StocksSubOrchestrator (existing: yfinance + ChromaDB RAG)
│   └── Tools: query_stocks, query_news, query_sentiment, correlation, etc.
├── CryptoSubOrchestrator (NEW)
│   └── MCP Server: CoinMarketCap (prices, market cap, volume, trending)
├── MacroSubOrchestrator (NEW)
│   └── MCP Server: FRED (GDP, CPI, unemployment, interest rates)
└── CalculationExecutor (NEW)
    └── MCP Server: Python REPL (NPV, IRR, Sharpe, custom calcs)
```

**MCP Integration Pattern**:
```python
# Each MCP server runs as a subprocess
# langchain-mcp-adapters loads tools into LangChain
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "coinmarketcap": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/mcp_servers/coinmarketcap_server.py"],
        "env": {"CMC_API_KEY": settings.coinmarketcap_api_key},
    },
    "fred": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/mcp_servers/fred_server.py"],
        "env": {"FRED_API_KEY": settings.fred_api_key},
    },
    "python_repl": {
        "transport": "stdio",
        "command": "python",
        "args": ["src/mcp_servers/python_repl_server.py"],
    },
})
tools = await client.get_tools()
```

**Pros**:
- Clean separation of concerns per domain
- MCP servers are independently testable, deployable, reusable
- `langchain-mcp-adapters` provides battle-tested integration (`pip install langchain-mcp-adapters`)
- Each MCP server can be replaced/upgraded independently
- MCP protocol enables future integrations (community servers, remote servers)
- Follows the same `DataSource` Protocol pattern already used in `stock_pipeline.py`

**Cons**:
- Significant new infrastructure (3 MCP servers + router + sub-orchestrators)
- MCP subprocess management adds operational complexity
- Async-heavy code (MCP client is async, current orchestrator is sync)
- Need to manage MCP server lifecycle (start/stop/health)

**Effort**: High (4-6 weeks for full implementation)

---

### Approach 2: Direct API Integration (No MCP)

Add new LangChain @tool wrappers directly calling CoinMarketCap, FRED, and Python execution APIs. Keep the existing orchestrator structure, add a router layer on top.

**Architecture**:
```
MarketOrchestrator (enhanced, same file)
├── RouterAgent (LLM-based or keyword-based)
├── Existing tools (query_stocks, query_news, etc.)
├── NEW: query_crypto_tool (direct CoinMarketCap HTTP)
├── NEW: query_macro_tool (direct FRED HTTP / fredapi)
└── NEW: execute_calculation_tool (restricted exec())
```

**Pros**:
- Minimal structural change — add tools to existing `market_tools.py`
- No subprocess management
- Simpler async story (direct HTTP calls)
- Faster to implement

**Cons**:
- Tighter coupling — all tools in one module
- No reusability outside this project
- `exec()` for Python calculations is inherently risky
- Doesn't leverage MCP ecosystem (no community servers, no protocol benefits)
- Harder to test in isolation

**Effort**: Medium (2-3 weeks)

---

### Approach 3: Hybrid — MCP for New Domains, Keep Existing for Stocks

Keep the current stocks/news/sentiment pipeline as-is. Add MCP servers ONLY for the new domains (crypto, macro, calculations). Add a lightweight router.

**Architecture**:
```
MarketOrchestrator (lightly refactored)
├── RouterAgent (determines domain)
├── StocksSubOrchestrator (EXISTING — no changes)
│   └── Direct retriever + agent (current flow)
├── CryptoSubOrchestrator (NEW — MCP-backed)
│   └── CoinMarketCap MCP tools
├── MacroSubOrchestrator (NEW — MCP-backed)
│   └── FRED MCP tools
└── CalculationExecutor (NEW — MCP-backed)
    └── Python REPL MCP tools
```

**Pros**:
- Zero risk to existing working functionality
- Incremental — can ship stocks-only first, add domains later
- MCP only where it adds value (new external integrations)
- Existing ChromaDB RAG stays untouched

**Cons**:
- Two different tool paradigms (direct retriever vs MCP)
- Slightly inconsistent architecture

**Effort**: Medium-High (3-4 weeks)

---

## Recommendation

**Approach 3 (Hybrid)** — and here's why, hermano:

1. **The existing stocks pipeline WORKS**. It has 18 test files, ChromaDB integration, demo data seeding, multi-language support, streaming, semantic cache. Don't touch it.

2. **MCP is the right choice for NEW external integrations**. CoinMarketCap and FRED are external APIs that benefit from the MCP abstraction — standardized tool interface, independent testing, env-based config. The Python REPL MCP server is practically a solved problem (reference implementations exist).

3. **The router is the only structural change to the orchestrator**. Instead of `ask()` → `agent.run()`, it becomes `ask()` → `router.classify()` → `sub_orchestrator.run()`. The stocks sub-orchestrator IS the current agent.

4. **Incremental delivery**. Phase 1: router + stocks (zero behavior change). Phase 2: add crypto MCP. Phase 3: add macro MCP. Phase 4: add calculation MCP.

### MCP vs Direct API — Decision Matrix

| Factor | MCP | Direct API |
|--------|-----|------------|
| Reusability | ✅ High (protocol-based) | ❌ Low (project-specific) |
| Testing | ✅ Independent subprocess | ⚠️ Needs mocking |
| Ecosystem | ✅ Community servers exist | ❌ Must build everything |
| Complexity | ⚠️ Subprocess management | ✅ Simpler |
| LangChain integration | ✅ `langchain-mcp-adapters` | ✅ `@tool` decorator |
| Security (Python exec) | ✅ Sandboxed subprocess | ❌ `exec()` in-process |

The security angle for Python execution is decisive — running `exec()` in a subprocess via MCP is inherently safer than in-process execution.

---

## MCP Server Specifications

### 1. CoinMarketCap MCP Server

**Package**: Custom (no official MCP server exists)
**Data provided**:
- Crypto prices (BTC, ETH, SOL, etc.)
- Market cap rankings
- 24h volume and % change
- Trending/gaining/losing cryptos
- Global crypto market metrics

**API**: CoinMarketCap API v1 (free tier: 333 calls/day)
**Key endpoint**: `https://pro-api.coinmarketcap.com/v1/cryptocurrency/`

**Tools to expose**:
```python
@mcp.tool()
def get_crypto_price(symbol: str) -> dict:
    """Get current price, market cap, 24h change for a crypto symbol."""

@mcp.tool()
def get_crypto_listings(sort: str = "market_cap", limit: int = 10) -> list[dict]:
    """Get top N cryptocurrencies by market cap, volume, or price change."""

@mcp.tool()
def get_trending_cryptos() -> list[dict]:
    """Get currently trending cryptocurrencies."""

@mcp.tool()
def get_global_metrics() -> dict:
    """Get global crypto market metrics (total market cap, BTC dominance, etc.)."""
```

### 2. FRED MCP Server

**Package**: Custom (wraps `fredapi` or direct HTTP)
**Data provided**:
- GDP growth rate
- CPI / Inflation rate
- Unemployment rate
- Federal funds rate
- Treasury yields (2y, 10y, 30y)
- Consumer confidence
- PMI (Manufacturing/services)

**API**: FRED API (free, requires API key from https://fred.stlouisfed.org/)
**Key endpoint**: `https://api.stlouisfed.org/fred/series/observations`

**Tools to expose**:
```python
@mcp.tool()
def get_economic_indicator(series_id: str, limit: int = 12) -> dict:
    """Get latest values for a FRED economic series (e.g., GDP, CPI, UNRATE)."""

@mcp.tool()
def search_indicators(query: str) -> list[dict]:
    """Search FRED for economic indicators matching a query."""

@mcp.tool()
def get_interest_rates() -> dict:
    """Get current key interest rates (Fed funds, treasury yields)."""

@mcp.tool()
def get_inflation_data() -> dict:
    """Get CPI, core CPI, and PCE inflation data."""
```

### 3. Python REPL MCP Server

**Package**: Existing MCP reference server or custom
**Data provided**: Arbitrary Python execution for financial calculations

**Tools to expose**:
```python
@mcp.tool()
def execute_python(code: str) -> str:
    """Execute Python code safely and return stdout. Available: numpy, pandas, scipy."""

@mcp.tool()
def calculate_npv(rate: float, cashflows: list[float]) -> float:
    """Calculate Net Present Value."""

@mcp.tool()
def calculate_irr(cashflows: list[float]) -> float:
    """Calculate Internal Rate of Return."""

@mcp.tool()
def calculate_sharpe(returns: list[float], risk_free_rate: float = 0.05) -> float:
    """Calculate Sharpe ratio from a series of returns."""
```

**Security**: Run in subprocess with:
- Timeout (5s default)
- No network access
- No filesystem writes
- Restricted imports (numpy, pandas, scipy, math only)

---

## Router Design

The router classifies user intent into domains. Two options:

### Option A: LLM-Based Router (Recommended)
```python
ROUTER_PROMPT = """Classify this financial query into ONE domain:
- stocks: stock prices, company analysis, earnings, equities
- crypto: cryptocurrency, bitcoin, ethereum, DeFi
- macro: GDP, inflation, interest rates, employment, economic indicators
- calculation: NPV, IRR, Sharpe ratio, financial math, portfolio optimization
- multi: requires data from multiple domains

Query: {query}
Domain:"""
```

### Option B: Keyword-Based Router (Simpler)
```python
CRYPTO_KEYWORDS = {"bitcoin", "btc", "ethereum", "eth", "crypto", "defi", "solana", ...}
MACRO_KEYWORDS = {"gdp", "inflation", "interest rate", "unemployment", "fed", "treasury", ...}
CALC_KEYWORDS = {"npv", "irr", "sharpe", "calculate", "portfolio optimization", ...}
```

**Recommendation**: Start with Option B (keyword), upgrade to Option A (LLM) when multi-domain queries become common.

---

## File Changes Needed

### New Files
```
src/agents/
├── router.py                          # RouterAgent (intent classification)
├── sub_orchestrators/
│   ├── __init__.py
│   ├── base.py                        # Abstract base sub-orchestrator
│   ├── stocks_orchestrator.py         # Wraps existing MarketQueryAgent
│   ├── crypto_orchestrator.py         # CryptoSubOrchestrator (MCP-backed)
│   ├── macro_orchestrator.py          # MacroSubOrchestrator (MCP-backed)
│   └── calculation_orchestrator.py    # CalculationExecutor (MCP-backed)

src/mcp_servers/
├── __init__.py
├── coinmarketcap_server.py            # CoinMarketCap MCP server
├── fred_server.py                     # FRED MCP server
└── python_repl_server.py             # Python REPL MCP server

tests/
├── test_router.py
├── test_crypto_orchestrator.py
├── test_macro_orchestrator.py
├── test_calculation_orchestrator.py
├── test_mcp_coinmarketcap.py
├── test_mcp_fred.py
└── test_mcp_python_repl.py
```

### Modified Files
```
src/agents/orchestrator.py             # Add router + sub-orchestrator delegation
src/config/__init__.py                 # Add: coinmarketcap_api_key, fred_api_key
src/api/deps.py                        # Update singleton init for new components
src/api/routes/chat.py                 # No changes needed (uses orchestrator.ask())
src/agents/chains/prompts.py           # Add router prompt, sub-domain prompts
```

### Unchanged Files
```
src/agents/query_agent.py              # Stays as stocks sub-orchestrator core
src/agents/retriever.py                # ChromaDB retriever — untouched
src/agents/chains/market_tools.py      # Existing tools — untouched
src/data_engine/*                      # All data pipelines — untouched
src/agents/memory/*                    # Conversation memory — untouched
src/agents/cache/*                     # Semantic cache — untouched
```

---

## Dependencies and API Keys Required

### New Python Packages
```txt
# MCP SDK
mcp>=1.0.0                    # MCP Python SDK
langchain-mcp-adapters>=0.1.0 # LangChain MCP integration

# FRED
fredapi>=0.5.1                # FRED API client (or direct HTTP with requests)

# Already have (no action needed)
requests                      # HTTP calls
numpy, pandas, scipy          # Financial calculations
python-dotenv                 # Env management
```

### API Keys Needed
| Service | Key | Cost | Where to Get |
|---------|-----|------|-------------|
| CoinMarketCap | `CMC_API_KEY` | Free (333 calls/day) | https://coinmarketcap.com/api/ |
| FRED | `FRED_API_KEY` | Free (unlimited) | https://fred.stlouisfed.org/docs/api/api_key.html |

### .env Additions
```env
# Crypto (CoinMarketCap)
coinmarketcap_api_key=your_cmc_key_here

# Macroeconomics (FRED)
fred_api_key=your_fred_key_here
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP subprocess crashes | Query fails | Health checks + auto-restart + graceful fallback to "service unavailable" message |
| CoinMarketCap rate limit (333/day) | Crypto queries stop | Cache responses (24h TTL for prices, 1h for listings), show rate limit warning |
| FRED data staleness | Outdated macro data | FRED data is already lagged (quarterly GDP, monthly CPI) — document this clearly |
| Python REPL security | Code injection | Subprocess sandbox, timeout, restricted imports, no network/fs |
| Async complexity | Bugs in orchestrator | Keep stocks path sync (existing), only new MCP paths async |
| Router misclassification | Wrong sub-orchestrator | Add confidence threshold, fall back to stocks (existing) on low confidence |
| Breaking existing tests | Regression | Phase 1 = router only, existing tests pass unchanged. New tests per sub-orchestrator |

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Create `RouterAgent` with keyword-based classification
- Create `BaseSubOrchestrator` abstract class
- Refactor `MarketOrchestrator.ask()` to route through `RouterAgent`
- `StocksSubOrchestrator` wraps existing `MarketQueryAgent` (zero behavior change)
- All existing tests pass unchanged

### Phase 2: Crypto MCP (Week 2)
- Build `CoinMarketCap MCP Server` (4 tools)
- Build `CryptoSubOrchestrator`
- Wire into router
- Tests: unit (mock CMC API) + integration (real API with test key)

### Phase 3: Macro MCP (Week 3)
- Build `FRED MCP Server` (4 tools)
- Build `MacroSubOrchestrator`
- Wire into router
- Tests: unit (mock FRED API) + integration

### Phase 4: Calculation MCP (Week 4)
- Build `Python REPL MCP Server` (4 tools with sandbox)
- Build `CalculationExecutor`
- Wire into router
- Security audit on sandboxed execution

### Phase 5: Multi-Domain Queries (Week 5-6)
- Upgrade router to LLM-based classification
- Handle queries that span domains ("How does GDP growth affect BTC price?")
- Aggregate results from multiple sub-orchestrators
- Streaming support across all sub-orchestrators

---

## Ready for Proposal

**Yes** — the exploration is complete. The orchestrator should tell the user:

1. **Recommended approach**: Hybrid (Approach 3) — keep existing stocks pipeline, add MCP for new domains
2. **Key decision**: MCP over direct API for crypto/macro/calculations (reusability, security, ecosystem)
3. **Incremental delivery**: 5 phases, each independently shippable
4. **Two API keys needed**: CoinMarketCap (free) and FRED (free)
5. **Zero risk to existing functionality**: Stocks pipeline untouched in Phase 1-4
6. **The biggest architectural change**: Adding a router layer to `MarketOrchestrator.ask()` — everything else is additive
