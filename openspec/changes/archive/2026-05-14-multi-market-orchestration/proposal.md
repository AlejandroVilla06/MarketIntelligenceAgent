# Proposal: Multi-Market Orchestration

## Intent

Transform the monolithic stocks-only `MarketOrchestrator` into a hierarchical multi-market system. Add crypto (CoinMarketCap), macroeconomics (FRED), and Python calculation capabilities via MCP tools, with a RouterAgent that classifies intent and falls back to multi-domain synthesis when confidence is low.

## Scope

### In Scope
- Hierarchical orchestrator refactor with RouterAgent + sub-orchestrators
- RouterAgent fall-back strategy (query all sub-orchestrators when confidence < 0.7)
- CryptoSubOrchestrator backed by CoinMarketCap MCP server
- MacroSubOrchestrator backed by FRED MCP server
- Python REPL MCP server for financial calculations
- API keys config (`coinmarketcap_api_key`, `fred_api_key`)
- Unit + integration tests for each new component

### Out of Scope
- Modifying existing stocks pipeline (query_agent, retriever, market_tools)
- Migrating from ChromaDB
- Replacing LangChain with another framework
- Streaming support for new sub-orchestrators (Phase 5+)
- LLM-based router upgrade (starts keyword-based)

## Capabilities

### New Capabilities
- `hierarchical-orchestrator`: Router + sub-orchestrator delegation pattern with fall-back synthesis
- `crypto-mcp`: CoinMarketCap MCP server exposing crypto price/market data tools
- `macro-mcp`: FRED MCP server exposing macroeconomic indicator tools
- `python-repl-mcp`: Sandboxed Python subprocess execution for financial calculations

### Modified Capabilities
- `agent-orchestration`: Orchestrator changes from direct delegation to router-based dispatch (interface change, not behavior change for stocks)

## Approach

**Hybrid architecture** — existing stocks pipeline stays untouched, new domains use MCP servers.

```
MarketOrchestrator (hierarchical)
├── RouterAgent (keyword-first → LLM when needed)
│   └── Fall-back: if confidence < 0.7, query ALL sub-orchestrators → synthesize
├── StocksSubOrchestrator (EXISTING — zero-change wrapper)
├── CryptoSubOrchestrator (NEW — CoinMarketCap MCP)
├── MacroSubOrchestrator (NEW — FRED MCP)
└── CalculationExecutor (NEW — Python REPL MCP)
```

**Phases**:
1. **RouterAgent + Config**: keyword router, fall-back mechanism, base class, config fields
2. **Crypto MCP**: CoinMarketCap MCP server + sub-orchestrator
3. **Macro MCP**: FRED MCP server + sub-orchestrator
4. **Python REPL**: subprocess sandbox MCP + calculation executor
5. **Integration + Tests**: wire-up, streaming, accuracy benchmarks

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/agents/orchestrator.py` | Modified | Refactor to hierarchical routing pattern |
| `src/agents/router_agent.py` | New | Intent classification + fall-back synthesis |
| `src/agents/sub_orchestrator.py` | New | Base class for sub-orchestrators |
| `src/agents/stocks_sub.py` | New | Wrapper around existing MarketQueryAgent |
| `src/agents/crypto_sub.py` | New | CoinMarketCap MCP integration |
| `src/agents/macro_sub.py` | New | FRED MCP integration |
| `src/agents/python_repl.py` | New | Sandboxed Python execution MCP |
| `src/mcp_servers/` | New | MCP server implementations (3 servers) |
| `src/config/__init__.py` | Modified | Add `coinmarketcap_api_key`, `fred_api_key` |
| `tests/` | New | Router, crypto, macro, REPL test files |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| MCP subprocess crashes | Medium | Health checks, auto-restart, graceful degradation |
| CoinMarketCap rate limit (333/day) | Medium | Cache with 24h TTL for prices, 1h for listings |
| Router misclassification | Low | Keyword + LLM hybrid; fall-back at <0.7 confidence |
| Breaking existing stocks tests | Low | Phase 1 = router only; existing tests unchanged |
| Python exec() security | High (avoided) | Subprocess-based MCP, NOT in-process exec() |

## Rollback Plan

Revert `orchestrator.py` to direct delegation, delete `router_agent.py` + `sub_orchestrator.py` + `crypto_sub.py` + `macro_sub.py` + `python_repl.py` + `src/mcp_servers/`, remove env vars. Stocks pipeline untouched throughout.

## Dependencies

- `langchain-mcp-adapters` — LangChain ↔ MCP bridge
- `mcp` — Python MCP SDK
- `fredapi` — FRED data client
- API keys: CoinMarketCap (free, 333 calls/day), FRED (free, unlimited)

## Success Criteria

- [ ] RouterAgent classifies stocks/crypto/macro/calculo with >90% accuracy
- [ ] Fall-back triggers for ambiguous queries (confidence < 0.7), queries all sub-orchestrators
- [ ] CryptoSubOrchestrator returns real CoinMarketCap data
- [ ] MacroSubOrchestrator returns real FRED data
- [ ] PythonREPL executes financial calculations safely in subprocess
- [ ] Existing stocks pipeline unchanged (all existing tests pass)
- [ ] `"What's the GDP growth and how does it affect BTC?"` returns synthesized multi-domain answer via fall-back