# Proposal: Sprint 3 - RAG Agents for Market Intelligence

## Intent

Build RAG-powered agents that enable natural language queries over market data (stock prices, news, sentiment). The agents will use LangChain for orchestration and ChromaDB as the vector store, allowing semantic search and retrieval-augmented generation over processed market intelligence.

## Scope

### In Scope
- ChromaDB vector store setup with embeddings for market data
- Retriever agents for stock data, news, and sentiment queries
- Query-writing agent that translates natural language to structured queries
- Agent orchestration layer combining retrieval + LLM reasoning
- CLI interface for querying the agent
- Unit tests for retrieval and agent components

### Out of Scope
- Real-time data ingestion during agent queries
- Multi-modal queries (images, charts)
- Agent memory persistence across sessions
- Frontend UI for agent queries (Sprint 4+)
- Trading execution or recommendations

## Capabilities

### New Capabilities
- `market-rag-retriever`: ChromaDB-backed retrieval of stock data, news, sentiment
- `market-query-agent`: LangChain agent that translates NL queries to structured retrieval
- `agent-orchestration`: Coordina retrieval + LLM para responder preguntas de mercado

### Modified Capabilities
- None (pure addition)

## Approach

1. **ChromaDB Setup**: Create collections for stocks, news, sentiment with sentence-transformers embeddings
2. **Retriever Layer**: Build ChromaDB-backed retrievers per data type (stocks, news, sentiment)
3. **Query Agent**: LangChain agent with ReAct-style reasoning over retrievers
4. **CLI**: Simple command-line interface for agent queries
5. **Testing**: Unit tests with mocked ChromaDB

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/agents/` | New | RAG agent implementation |
| `src/data_engine/storage.py` | Extended | ChromaDB integration |
| `src/ui/` | Extended | CLI for agent queries |
| `tests/` | New | Agent unit tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| ChromaDB embedding quality | Medium | Use pre-trained sentence-transformers, evaluate retrieval accuracy |
| LLM hallucination on market data | Medium | Constrain with retrieval context, add confidence scores |
| Query performance at scale | Low | Add batch retrieval, limit context window |
| API cost for LLM calls | Medium | Cache responses, use cheaper models for simple queries |

## Rollback Plan

1. Remove `src/agents/` directory
2. Revert `src/data_engine/storage.py` to pre-ChromaDB version
3. Remove ChromaDB data in `data/vector_store/`
4. Remove CLI additions in `src/ui/`
5. Delete tests in `tests/test_agents.py`

## Dependencies

- LangChain >= 0.2.0
- ChromaDB >= 0.4.0
- sentence-transformers >= 2.3.0
- OpenAI API key (or Anthropic) for LLM

## Success Criteria

- [ ] Agent can answer "What was the sentiment on AAPL last week?" using retrieval
- [ ] Agent can compare "TSLA vs GM stock performance this month"
- [ ] ChromaDB collections created and populated from processed data
- [ ] Unit tests pass with >80% coverage
- [ ] CLI allows running agent queries from command line