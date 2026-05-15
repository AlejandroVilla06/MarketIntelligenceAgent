# Design: Multi-Market Orchestration

## Technical Approach

**Hybrid architecture**: the existing stocks pipeline (`MarketQueryAgent` → `MarketRAGRetriever` → ChromaDB) stays untouched. A `RouterAgent` with keyword-based classification + confidence scoring sits above a `BaseSubOrchestrator` interface. Three NEW MCP servers (crypto, macro, Python REPL) run as subprocesses, exposed to LangChain via `langchain-mcp-adapters`. The `MarketOrchestrator.ask()` becomes `router.route(query)` → `sub.answer(query)` instead of direct `agent.run(query)`.

## Architecture Decisions

| Decision | Choice | Rejected | Rationale |
|----------|--------|----------|-----------|
| **AD1: MCP placement** | `src/agents/mcp/` (3 server files) | `src/mcp_servers/` (separate top-level) | Co-locates with agents module; `deps.py` already imports from `src.agents`; keeps domain logic together |
| **AD2: Router strategy** | Keyword + confidence score, fall-back at <0.7 | LLM-only router | Phase 1 keyword is deterministic, testable, zero-latency. LLM router is Phase 5+ upgrade |
| **AD3: Async boundary** | MCP sub-orchestrators are async; stocks stays sync | Make everything async | `ask()` is already wrapped in `asyncio.to_thread()` at the API layer. New sub-orchestrators use `async def answer()`. Orchestrator dispatches sync vs async internally |
| **AD4: MCP transport** | `stdio` (subprocess) per MCP spec | HTTP/TCP ports | No port management, auto-cleanup on crash, simpler local dev. SDK `FastMCP` uses stdio by default |
| **AD5: Stocks wrapper** | `StocksSubOrchestrator` delegates to `MarketQueryAgent.run()` | Refactor query_agent into sub-orchestrator | Zero change to existing 868-line agent, zero risk to 18 test files, zero regression |
| **AD6: Config** | New `coinmarketcap_api_key`, `fred_api_key`, `mcp_repl_timeout` in `Settings` model | Separate config file | Follows existing Pydantic pattern with `Field(description=...)` + `.env` loading |

## Data Flow

```
chat.py ──orch.ask(query)──→ MarketOrchestrator
                                │
                          RouterAgent.route(query)
                           ┌────┴────┐
                    conf≥0.7          conf<0.7
                  direct route      fall-back route
                       │                  │
              ┌────────┼────────┐   asyncio.gather()
              ▼        ▼        ▼     all subs
           Stocks   Crypto   Macro        │
           (sync)   (MCP)    (MCP)   LLM synthesizes
                       │
              FastMCP client (stdio)
                       │
              crypto_server.py → CoinMarketCap HTTP
```

**Direct route**: `"BTC price"` → RouterAgent `("crypto", 0.95)` → `CryptoSub.answer()` → MCP `get_crypto_price("BTC")` → LLM formats → return.

**Fall-back route**: `"How does GDP affect BTC?"` → scores `macro=0.4, crypto=0.4` → fall-back → `asyncio.gather(stocks, crypto, macro, repl)` → LLM synthesizes unified response.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/agents/orchestrator.py` | Modify | Add `RouterAgent` delegation in `ask()` / `ask_stream()`; keep `setup()`, `reset()`, `get_status()` |
| `src/agents/router_agent.py` | Create | Keyword-based classifier with `can_handle(query) → (domain, confidence)`; fall-back `asyncio.gather()` + LLM synthesis |
| `src/agents/sub_orchestrator.py` | Create | `BaseSubOrchestrator` ABC with `can_handle()`, `async answer()`, `domain` property |
| `src/agents/stocks_sub.py` | Create | `StocksSubOrchestrator` wrapping `MarketQueryAgent.run()`; `domain="stocks"`, confidence from keyword match |
| `src/agents/crypto_sub.py` | Create | `CryptoSubOrchestrator` with `MultiServerMCPClient` → `crypto_server.py` via stdio |
| `src/agents/macro_sub.py` | Create | `MacroSubOrchestrator` with `MultiServerMCPClient` → `macro_server.py` via stdio |
| `src/agents/python_repl.py` | Create | `CalculationExecutor` with `MultiServerMCPClient` → `repl_server.py` via stdio; thin proxy |
| `src/agents/mcp/__init__.py` | Create | Package init for MCP server directory |
| `src/agents/mcp/crypto_server.py` | Create | FastMCP server: `get_crypto_price()`, `get_top_cryptos()` via CoinMarketCap HTTP |
| `src/agents/mcp/macro_server.py` | Create | FastMCP server: `get_gdp()`, `get_cpi()`, `get_unemployment()`, `get_interest_rates()` via FRED HTTP |
| `src/agents/mcp/repl_server.py` | Create | FastMCP server: `calculate_python(code)` → subprocess exec with numpy/pandas/scipy, 30s timeout, no I/O, no network |
| `src/config/__init__.py` | Modify | Add `coinmarketcap_api_key`, `fred_api_key`, `mcp_repl_timeout` (default 30) fields |
| `src/agents/__init__.py` | Modify | Add exports: `RouterAgent`, `BaseSubOrchestrator`, `StocksSubOrchestrator`, `CryptoSubOrchestrator`, `MacroSubOrchestrator`, `CalculationExecutor` |
| `src/api/deps.py` | Modify | `init_orchestrator()` initializes RouterAgent + sub-orchestrators during lifespan |
| `.env` | Modify | Add `coinmarketcap_api_key=`, `fred_api_key=`, `mcp_repl_timeout=30` |

## Interfaces / Contracts

```python
class BaseSubOrchestrator(ABC):
    """All sub-orchestrators implement this."""
    @abstractmethod
    def can_handle(self, query: str) -> tuple[bool, float]: ...
    @abstractmethod
    async def answer(self, query: str) -> str: ...
    @property
    @abstractmethod
    def domain(self) -> str: ...

class RouterAgent:
    sub_orchestrators: list[BaseSubOrchestrator]
    def route(self, query: str) -> RoutingDecision: ...
    async def execute(self, query: str) -> str: ...

# RoutingDecision is a dataclass:
#   mode: "direct" | "fallback"
#   sub: BaseSubOrchestrator | None
#   confidence: float
```

**MCP tool signatures** (exposed by each server):
- `get_crypto_price(symbol: str) → str` — CoinMarketCap `/v1/cryptocurrency/quotes/latest`
- `get_cpi() → str` — FRED series `CPIAUCSL`
- `calculate_python(code: str) → str` — restricted subprocess execution

## Testing Strategy

| Layer | Test | Approach |
|-------|------|----------|
| Unit | `test_router_stocks/crypto/macro/calculation` | Mock `BaseSubOrchestrator.can_handle()`, verify correct domain routing with confidence ≥ 0.7 |
| Unit | `test_router_fallback` | Ambiguous query → fall-back mode; verify `asyncio.gather()` called, LLM synthesize invoked |
| Unit | `test_stocks_sub_wrapper` | Verify `StocksSubOrchestrator.answer()` calls `MarketQueryAgent.run()` unchanged |
| Integration | `test_crypto_mcp_connectivity` | Start `crypto_server.py` via stdio MCP client, call `get_crypto_price("BTC")`, verify response shape |
| Integration | `test_repl_npv_calculation` | `calculate_python("import numpy as np; print(np.npv(0.1, [-100,50,60,70]))")` → correct NPV |
| Regression | `test_orchestrator.py` (all) | Existing tests pass unchanged (stocks path untouched) |
| Regression | `test_query_agent.py` (all) | Existing tests pass unchanged |

## Migration / Rollout

No data migration required. Feature is additive. Rollback: revert `orchestrator.py` to direct delegation, delete 12 new files, remove 3 config fields, revert `agents/__init__.py` exports. Existing stocks pipeline continues operating.

## Open Questions

- [ ] Should `mcp_repl_timeout` be per-call or global? Current design: global (30s default), overridable via env
- [ ] CoinMarketCap cache: TTL 24h for prices, 1h for listings — implement at MCP server level or sub-orchestrator level?
- [ ] Should streaming (`ask_stream`) support new sub-orchestrators in Phase 1, or defer to Phase 5+? Proposal says "out of scope" but `router.execute()` could yield tokens from direct route via `astream()`
