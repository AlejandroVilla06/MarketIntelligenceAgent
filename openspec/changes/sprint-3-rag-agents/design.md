# Design: Sprint 3 - RAG Agents for Market Intelligence

## Technical Approach

Build a 3-layer RAG system: ChromaDB-backed retriever (data layer), LangChain ReAct agent (reasoning layer), and orchestration CLI (interface layer). The retriever ingests processed Parquet data from Sprint 1/2 into vector collections; the agent wraps retriever methods as LangChain tools; the orchestrator wires them together and exposes a CLI. Refs: `market-rag-retriever` spec, `market-query-agent` spec.

## Architecture Decisions

| Decision | Choice | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Vector store | ChromaDB with persistent client | FAISS, Pinecone, Weaviate | Already in `requirements.txt` + `config.yaml`; local-first; persistent disk mode matches existing Parquet-on-disk pattern |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 | OpenAI embeddings, Cohere | Free, local, 384-dim (fast); no API dependency; matches spec requirement |
| Agent framework | LangChain ReAct agent via `create_react_agent` | Custom agent loop, LlamaIndex | `langchain>=0.2.0` already in deps; ReAct gives think→act→observe loop per spec; tool binding is native |
| LLM provider | OpenAI GPT-3.5-turbo (default), Anthropic fallback | Local LLM, Ollama | `openai_api_key` + `anthropic_api_key` already in `Settings`; GPT-3.5 cost-effective for reasoning |
| Collection strategy | 3 separate collections (stocks, news, sentiment) | Single collection with type metadata | Spec requires separate collections; enables per-type `query_*` methods; simpler metadata filtering |
| Data ingestion | Reuse `StorageInterface` to load Parquet → transform → ChromaDB | Direct pipeline integration | Decouples retrieval from ingestion schedule; follows existing pattern of `load_stocks()`/`load_news()` |
| Orchestration | Lightweight `MarketOrchestrator` class, not a framework | LangGraph, CrewAI | Overkill for single-agent; CLI is the interface; keeps agent setup explicit and testable |
| Config extension | Extend `Settings` with RAG-specific fields | Separate config file | Follows existing `pydantic-settings` pattern; `.env`-driven; single source of truth |

## Data Flow

```
data/processed/ (Parquet from Sprint 1/2)
    │
    ▼
┌─────────────────────────────┐
│ MarketRAGRetriever          │  ← Loads via StorageInterface
│  • add_stock_data(df)       │
│  • add_news_data(articles)  │
│  • add_sentiment_data(data) │
└──────────┬──────────────────┘
           │ query_stocks / query_news / query_sentiment / query_all
           ▼
┌─────────────────────────────┐
│ MarketQueryAgent            │  ← LangChain ReAct agent
│  Tools: [query_stocks,      │
│    query_news, query_       │
│    sentiment, query_all]    │
│  LLM: GPT-3.5-turbo        │
└──────────┬──────────────────┘
           │ run(query) → str
           ▼
┌─────────────────────────────┐
│ MarketOrchestrator          │  ← Wires retriever + agent
│  • setup() → index data     │
│  • ask(query) → answer      │
│  • CLI entry point          │
└─────────────────────────────┘

ChromaDB persist: data/processed/chromadb/
  ├── market_stocks/
  ├── market_news/
  └── market_sentiment/
```

### Query Flow (sequence)

```
User → CLI: "How did news affect AAPL last week?"
  CLI → MarketOrchestrator.ask(query)
    Orchestrator → MarketQueryAgent.run(query)
      Agent Think: "Need stock + news for AAPL last week"
      Agent Act:  query_all("AAPL stock and news last week")
        Agent Tool → MarketRAGRetriever.query_all(...)
          Retriever → ChromaDB similarity_search (3 collections)
          ChromaDB → results (doc, metadata, distance)
        Tool → formatted results back to agent
      Agent Observe: stock went up, news sentiment 0.7
      Agent Think: "Enough info to answer"
      Agent → "AAPL stock rose 3% last week alongside positive
               news sentiment (0.7), driven by earnings beat."
  CLI → User: answer string
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/agents/retriever.py` | Create | `MarketRAGRetriever` class — ChromaDB collections + similarity search |
| `src/agents/query_agent.py` | Create | `MarketQueryAgent` class — LangChain ReAct agent with retriever tools |
| `src/agents/orchestrator.py` | Create | `MarketOrchestrator` class — wires retriever + agent, exposes `ask()` |
| `src/agents/chains/market_tools.py` | Create | LangChain `@tool` definitions wrapping retriever methods |
| `src/agents/chains/prompts.py` | Create | ReAct prompt template with market-specific instructions |
| `src/agents/memory/conversation.py` | Create | Session-scoped conversation memory (per spec out-of-scope for persistence, but useful within session) |
| `src/agents/__init__.py` | Modify | Export new classes |
| `src/config/__init__.py` | Modify | Add RAG-specific settings (embedding model name, default k, collection names, LLM model) |
| `src/data_engine/storage.py` | Extend | Add `load_sentiment()` method for sentiment Parquet loading |
| `run_agent.py` | Create | CLI entry point for agent queries (mirrors `run_ingestion.py` pattern) |
| `tests/test_retriever.py` | Create | Unit tests for MarketRAGRetriever with mocked ChromaDB |
| `tests/test_query_agent.py` | Create | Unit tests for MarketQueryAgent with mocked retriever + LLM |
| `tests/test_orchestrator.py` | Create | Integration tests for orchestrator end-to-end |

## Interfaces / Contracts

### MarketRAGRetriever

```python
class MarketRAGRetriever:
    """ChromaDB-backed retriever for market data. Refs: market-rag-retriever spec."""

    def __init__(self, persist_directory: str = "data/processed/chromadb") -> None:
        """Init ChromaDB client + 3 collections with all-MiniLM-L6-v2 embeddings."""

    def add_stock_data(self, df: pl.DataFrame) -> None:
        """Add stock rows to market_stocks. Document: 'SYMBOL DATE close=X volume=Y RSI=Z'."""

    def add_news_data(self, articles: list[dict]) -> None:
        """Add news to market_news. Document: title + content. Metadata: timestamp, source, sentiment."""

    def add_sentiment_data(self, data: list[dict]) -> None:
        """Add sentiment to market_sentiment. Document: 'SYMBOL sentiment X positive on DATE'."""

    def query_stocks(self, query: str, k: int = 5) -> list[dict]:
        """Return top-k from market_stocks. Keys: document, metadata, distance."""

    def query_news(self, query: str, k: int = 5) -> list[dict]:
        """Return top-k from market_news."""

    def query_sentiment(self, query: str, k: int = 5) -> list[dict]:
        """Return top-k from market_sentiment."""

    def query_all(self, query: str, k_per_collection: int = 3) -> dict[str, list[dict]]:
        """Search all 3 collections, return merged dict. Supports weight config."""
```

### ChromaDB Document/Metadata Models

```python
# Stock document: "AAPL 2024-01-15 close=170.2 volume=50M RSI=65"
STOCK_METADATA = {
    "symbol": str,       # "AAPL"
    "date": str,         # "2024-01-15"
    "close": float,      # 170.2
    "volume": int,       # 50000000
    "rsi_14": float,     # 65.0 (if available from Sprint 2 features)
    "data_type": str,    # "stock"  (for query_all filtering)
}

# News document: article title + content
NEWS_METADATA = {
    "source": str,       # "Reuters"
    "timestamp": str,    # "2024-01-15T10:30:00"
    "symbol": str,       # "AAPL"
    "sentiment_score": float,  # 0.7
    "data_type": str,    # "news"
}

# Sentiment document: "AAPL sentiment 0.7 positive on 2024-01-15"
SENTIMENT_METADATA = {
    "symbol": str,       # "AAPL"
    "date": str,         # "2024-01-15"
    "sentiment_score": float,  # 0.7
    "sentiment_label": str,    # "positive" | "negative" | "neutral"
    "data_type": str,    # "sentiment"
}
```

### MarketQueryAgent

```python
class MarketQueryAgent:
    """LangChain ReAct agent over market retriever. Refs: market-query-agent spec."""

    def __init__(self, retriever: MarketRAGRetriever, model_name: str = "gpt-3.5-turbo") -> None:
        """Create LangChain agent with 4 tools + LLM. Single init, reuse LLM."""

    def run(self, query: str) -> str:
        """Execute ReAct loop: think → act (tool) → observe → answer.
        Returns answer string. On LLM error: fallback to direct retrieval.
        On no data: 'I do not have enough information.'"""
```

### MarketOrchestrator

```python
class MarketOrchestrator:
    """Coordinates retriever + agent + data loading. Refs: agent-orchestration."""

    def __init__(self, persist_directory: str | None = None, model_name: str | None = None) -> None:
        """Init retriever + agent. Uses Settings defaults if not overridden."""

    def setup(self, storage: StorageInterface | None = None) -> None:
        """Load data from Parquet via StorageInterface, index into ChromaDB.
        Skips collections that already have data (idempotent)."""

    def ask(self, query: str) -> str:
        """Delegate to MarketQueryAgent.run(). Main entry point."""

    def reset(self) -> None:
        """Clear all ChromaDB collections. For re-indexing."""
```

### Config Extensions

```python
# Added to Settings class in src/config/__init__.py
rag_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
rag_default_k: int = 5
rag_collection_stocks: str = "market_stocks"
rag_collection_news: str = "market_news"
rag_collection_sentiment: str = "market_sentiment"
rag_llm_model: str = "gpt-3.5-turbo"
rag_llm_temperature: float = 0.0  # Deterministic for factual retrieval
rag_max_retries: int = 2
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `MarketRAGRetriever` add/query methods | Mock `chromadb.Client`; verify collection.add called with correct docs/metadata |
| Unit | `MarketQueryAgent` tool selection | Mock LLM responses; verify correct tool invoked for stock/news/mixed queries |
| Unit | `MarketOrchestrator.ask()` | Mock retriever + agent; verify delegation and error fallback |
| Unit | Document text formatting | Known input DataFrame → expected document string (e.g., "AAPL 2024-01-15 close=170.2") |
| Integration | Retriever with real ChromaDB (in-memory) | Add data, query, assert similarity results returned |
| Integration | Agent ReAct loop with mocked LLM | Verify think→act→observe→answer flow for multi-step queries |
| E2E | Full orchestrator: load Parquet → index → query → answer | Requires sample Parquet files; validate answer contains expected data |

## Migration / Rollout

**No migration required.** Pure addition — no existing code modified except:

- `src/config/__init__.py`: Extended with new settings fields (backward compatible — all have defaults)
- `src/data_engine/storage.py`: Extended with `load_sentiment()` (additive, no breaking changes)
- `src/agents/__init__.py`: Updated exports (currently empty)

Rollback per proposal: remove `src/agents/` new files, revert `storage.py` and `config/__init__.py` additions, delete `run_agent.py` and `tests/test_*agent*`.

## Open Questions

- [ ] Should `query_all` merge and re-rank results, or return per-collection results and let the LLM decide relevance? (Leaning: per-collection return, LLM reasons over them — simpler, avoids custom ranking logic)
- [ ] Should we add a `hybrid_search` combining ChromaDB similarity + metadata filtering (e.g., `WHERE symbol='AAPL'`)? Not in spec, but common need.
- [ ] What LLM temperature for the agent? Proposing 0.0 for factual grounding, but may need 0.1 for query reformulation creativity.
- [ ] Should `setup()` auto-detect new Parquet data and incrementally update collections, or always rebuild? (Leaning: rebuild for simplicity, incremental as future enhancement)
