# Tasks: Sprint 3 - RAG Agents for Market Intelligence

## Phase 1: Foundation / Infrastructure

- [x] 1.1 Create `src/agents/retriever.py` with MarketRAGRetriever class skeleton and __init__ method
- [x] 1.2 Add RAG-specific settings to `src/config/__init__.py` (embedding model, collection names, LLM config)
- [x] 1.3 Extend `src/data_engine/storage.py` with `load_sentiment()` method for loading sentiment Parquet data
- [x] 1.4 Create `src/agents/__init__.py` to export new agent classes (modify existing file)
- [x] 1.5 Create ChromaDB collection constants and embedding model initialization in retriever

## Phase 2: Core Implementation

- [x] 2.1 Implement `add_stock_data()` method in MarketRAGRetriever with proper document/text formatting
- [x] 2.2 Implement `add_news_data()` method in MarketRAGRetriever with title+content document structure
- [x] 2.3 Implement `add_sentiment_data()` method in MarketRAGRetriever with sentiment summary document
- [x] 2.4 Implement query methods (`query_stocks`, `query_news`, `query_sentiment`, `query_all`) in MarketRAGRetriever
- [x] 2.5 Create `src/agents/chains/market_tools.py` with LangChain @tool wrappers for retriever methods
- [x] 2.6 Create `src/agents/chains/prompts.py` with ReAct prompt template for market queries
- [x] 2.7 Create `src/agents/query_agent.py` with MarketQueryAgent class and ReAct loop implementation
- [x] 2.8 Create `src/agents/memory/conversation.py` for session-scoped conversation memory
- [x] 2.9 Create `src/agents/orchestrator.py` with MarketOrchestrator class wiring retriever + agent

## Phase 3: Integration / Wiring

- [x] 3.1 Create `run_agent.py` CLI entry point mirroring `run_ingestion.py` pattern
- [x] 3.2 Wire orchestrator setup() method to load data via StorageInterface and index into ChromaDB
- [x] 3.3 Implement orchestrator ask() method delegation to MarketQueryAgent.run()
- [x] 3.4 Add error handling and fallback mechanisms in orchestrator and agent
- [x] 3.5 Test CLI interface with sample queries to verify end-to-end flow

## Phase 4: Testing

- [x] 4.1 Create `tests/test_retriever.py` unit tests for MarketRAGRetriever with mocked ChromaDB
- [x] 4.2 Create `tests/test_query_agent.py` unit tests for MarketQueryAgent with mocked retriever + LLM
- [x] 4.3 Create `tests/test_orchestrator.py` integration tests for orchestrator end-to-end flows
- [x] 4.4 Test document text formatting: verify DataFrame → expected document string conversion
- [x] 4.5 Test ReAct loop: verify think→act→observe→answer flow for multi-step queries
- [ ] 4.6 Run all tests to ensure >80% coverage and fix any failures (BLOCKED: dependencies not properly installed)

## Phase 5: Cleanup / Documentation

- [ ] 5.1 Review and polish code for readability and consistency with existing codebase
- [ ] 5.2 Add docstrings to all new classes and methods following project conventions
- [ ] 5.3 Verify imports are correct and remove any unused dependencies
- [ ] 5.4 Ensure ChromaDB persist directory is properly configured and created