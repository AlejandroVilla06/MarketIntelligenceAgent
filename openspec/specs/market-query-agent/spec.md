# Market Query Agent Specification

## Purpose

Define the requirements for a LangChain-based agent that translates natural language queries into structured retrieval operations over the market data retriever. The agent shall use reasoning (ReAct style) to determine which data sources to query and how to combine the results.

## Requirements

### Requirement: Agent Architecture

The system SHALL use a LangChain agent with access to tools representing the retriever's query methods.

#### Scenario: Initialize agent
- GIVEN a market-rag-retriever instance
- WHEN the MarketQueryAgent is initialized with the retriever
- THEN the system SHALL create a LangChain agent with tools:
    - `query_stocks`: for stock data questions
    - `query_news`: for news data questions
    - `query_sentiment`: for sentiment data questions
    - `query_all`: for cross-domain questions
- AND the agent SHALL use a language model (e.g., OpenAI GPT-3.5-turbo or similar) for reasoning

### Requirement: Natural Language Understanding

The system SHALL interpret user queries in natural language and decide which tool(s) to use.

#### Scenario: Stock-focused query
- GIVEN the agent is initialized
- WHEN the user asks "What was the closing price of AAPL last Friday?"
- THEN the agent SHALL select the `query_stocks` tool (or `query_all` with stock preference)
- AND the agent SHALL generate a query string suitable for the retriever (e.g., "AAPL close price last Friday")

#### Scenario: News-focused query
- GIVEN the agent is initialized
- WHEN the user asks "What news affected TSLA stock this week?"
- THEN the agent SHALL select the `query_news` tool (or `query_all` with news preference)
- AND the agent SHALL generate a query string (e.g., "Tesla news this week")

#### Scenario: Mixed query
- GIVEN the agent is initialized
- WHEN the user asks "How did the news about Apple's earnings affect its stock price?"
- THEN the agent SHALL select the `query_all` tool
- AND the agent SHALL generate a query that can be split or run across collections

### Requirement: Reasoning Loop (ReAct)

The agent SHALL follow a Reasoning and Acting (ReAct) loop: think, act, observe, until it has enough information to answer.

#### Scenario: Simple retrieval
- GIVEN the agent is initialized
- WHEN the user asks "What is the current RSI for AAPL?"
- THEN the agent SHALL:
    1. Think: I need to get the latest RSI for AAPL from stock data.
    2. Act: Use the `query_stocks` tool with query "AAPL RSI"
    3. Observe: Get results from the retriever
    4. Think: I have the RSI value, now I can answer.
    5. Answer: The RSI for AAPL is 65.

#### Scenario: Multi-step reasoning
- GIVEN the agent is initialized
- WHEN the user asks "Was the sentiment for MSFT positive when the stock price increased last week?"
- THEN the agent SHALL:
    1. Think: I need to check both sentiment and stock price for MSFT last week.
    2. Act: Use `query_all` with query "MSFT stock price last week"
    3. Observe: Get stock data showing increase
    4. Think: Now check sentiment for the same period.
    5. Act: Use `query_all` with query "MSFT sentiment last week"
    6. Observe: Get sentiment data showing positive
    7. Think: Both conditions are met, so answer yes.
    8. Answer: Yes, the sentiment was positive when the stock increased.

### Requirement: Interface

The agent SHALL provide a Python class with the following methods:

- `__init__(retriever: MarketRAGRetriever, model_name: str = "gpt-3.5-turbo")`
- `run(query: str) -> str` : returns the answer to the user's query as a string.

The agent SHALL handle errors gracefully, returning a helpful message if the retriever or LLM fails.

## Non-Functional Requirements

### Performance
- The agent SHALL initialize the LLM once and reuse it.
- A typical query SHALL complete within 10 seconds (depending on LLM latency).

### Reliability
- If the LLM returns an invalid format, the agent SHALL attempt to retry or fallback to a simple retrieval.
- The agent SHALL log its reasoning steps for debugging (if enabled).

### Constraints
- The agent SHALL not make up information; it must base its answer on the retrieved context.
- If no relevant data is found, the agent SHALL state that it does not have enough information.
