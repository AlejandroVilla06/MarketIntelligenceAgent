# Delta for market-query-agent
## MODIFIED Requirements

### Requirement: Agent Architecture

The system SHALL use a LangChain agent with access to tools representing the retriever's query methods and the new correlation and temporal analysis tools.

#### Scenario: Initialize agent with new tools
- GIVEN a market-rag-retriever instance
- WHEN the MarketQueryAgent is initialized with the retriever
- THEN the system SHALL create a LangChain agent with tools:
  - `query_stocks`: for stock data questions
  - `query_news`: for news data questions
  - `query_sentiment`: for sentiment data questions
  - `query_all`: for cross-domain questions
  - `get_sentiment_price_correlation`: for correlation questions (NEW)
  - `align_by_temporal_window`: for temporal alignment questions (NEW)
  - `get_cross_collection_context`: for enriched multi-collection context (NEW)
- AND the agent SHALL use a language model (e.g., OpenAI GPT-3.5-turbo or similar) for reasoning

(Previously: Agent had only 4 tools — query_stocks, query_news, query_sentiment, query_all)

### Requirement: Natural Language Understanding

The system SHALL interpret user queries in natural language and decide which tool(s) to use.

#### Scenario: Correlation-focused query
- GIVEN the agent is initialized
- WHEN the user asks "How did sentiment correlate with AAPL's stock price last month?"
- THEN the agent SHALL select the `get_sentiment_price_correlation` tool
- AND the agent SHALL generate a query with symbol="AAPL" and window_days=30

#### Scenario: Multi-collection enriched query
- GIVEN the agent is initialized
- WHEN the user asks "Give me a complete market picture for TSLA over the past week"
- THEN the agent SHALL select the `get_cross_collection_context` tool
- AND the agent SHALL generate a query with symbol="TSLA" and date_range=[7 days ago, today]

#### Scenario: Time-filtered query (unchanged)
- GIVEN the agent is initialized
- WHEN the user asks "What was the closing price of AAPL last Friday?"
- THEN the agent SHALL select the `query_stocks` tool (or `query_all` with stock preference)
- AND the agent SHALL generate a query string suitable for the retriever

#### Scenario: Mixed query (unchanged)
- GIVEN the agent is initialized
- WHEN the user asks "How did the news about Apple's earnings affect its stock price?"
- THEN the agent SHALL select the `query_all` tool
- AND the agent SHALL generate a query that can be split or run across collections

## ADDED Requirements

### Requirement: Correlation Tool Integration

The system SHALL provide the `get_sentiment_price_correlation` tool as part of the agent's toolset with proper error handling for edge cases.

#### Scenario: Correlation computed successfully
- GIVEN the agent has access to sentiment and stock data for the requested symbol
- WHEN the user asks a correlation question
- THEN the agent SHALL call `get_sentiment_price_correlation` with appropriate parameters
- AND the agent SHALL present the correlation coefficient and direction in natural language

#### Scenario: No data overlap — informative error
- GIVEN the agent is asked about correlation for a symbol with no temporal overlap
- WHEN `get_sentiment_price_correlation` returns status: "no_overlap"
- THEN the agent SHALL explain: "There is no overlapping sentiment and price data for the requested period. Available ranges: [dates]"
- AND the agent SHALL NOT provide a correlation value

#### Scenario: Insufficient data — informative error
- GIVEN the agent is asked about correlation with fewer than 10 data points
- WHEN `get_sentiment_price_correlation` returns status: "insufficient_data"
- THEN the agent SHALL explain: "Not enough data points (N) to compute statistically significant correlation. Need at least 10."

### Requirement: Temporal Alignment Tool Integration

The system SHALL provide the `align_by_temporal_window` tool to handle queries about aligned time series.

#### Scenario: Temporal alignment requested
- GIVEN the agent has aligned data for the requested symbol
- WHEN the user asks "Show me AAPL's sentiment and price aligned for January"
- THEN the agent SHALL call `align_by_temporal_window` with symbol="AAPL" and date_range
- AND the agent SHALL present the aligned DataFrame in a readable format (e.g., table)

#### Scenario: Partial overlap warning presented
- GIVEN `align_by_temporal_window` returns a result with overlap_valid=false
- WHEN the agent processes the result
- THEN the agent SHALL include the warning about missing data in the response
- AND the agent SHALL specify which collection is missing data

### Requirement: Cross-Collection Context Tool Integration

The system SHALL provide the `get_cross_collection_context` tool for comprehensive market queries.

#### Scenario: Full context retrieved
- GIVEN the agent is asked for a complete market picture
- WHEN `get_cross_collection_context` returns a full context object
- THEN the agent SHALL summarize each section (stocks, news, sentiment) in natural language
- AND the agent SHALL present KPIs (return, volatility, aggregate sentiment score)

#### Scenario: Missing collection handled gracefully
- GIVEN `get_cross_collection_context` returns status: "no_data" for a collection
- WHEN the agent processes the result
- THEN the agent SHALL exclude the missing collection from the response
- AND the agent SHALL state: "No [collection] data available for the requested period"