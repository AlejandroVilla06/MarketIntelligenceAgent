# Cross-Collection Context Enrichment Specification

## Purpose

Define requirements for enriching agent prompts with structured context from multiple ChromaDB collections simultaneously. The system SHALL combine stock, news, and sentiment data into a unified context object, with time filtering to ensure only temporally relevant data is included.

## Requirements

### Requirement: Multi-Collection Context Retrieval
The system SHALL retrieve and combine context from stocks, news, and sentiment collections for a given symbol and time range.

#### Scenario: All three collections have data
- GIVEN stock data exists for AAPL from 2024-01-01 to 2024-01-31
- AND news data exists for AAPL from 2024-01-15 to 2024-01-31
- AND sentiment data exists for AAPL from 2024-01-01 to 2024-01-31
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[2024-01-01, 2024-01-31]) is called
- THEN the system SHALL return a structured context object with sections:
  - stocks_summary: {kpi_summary, recent_prices, volume_trend}
  - news_summary: {article_count, themes, sources}
  - sentiment_summary: {aggregate_score, dominant_sentiment, top_sentiment_days}
  - temporal_metadata: {overlap_ranges, missing_collections}

#### Scenario: Only stock and sentiment data available
- GIVEN stock data exists for AAPL from 2024-01-01 to 2024-01-31
- AND news data does not exist for AAPL
- AND sentiment data exists for AAPL from 2024-01-01 to 2024-01-31
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[2024-01-01, 2024-01-31]) is called
- THEN the response SHALL include news_summary with status: "no_data"
- AND the response SHALL include temporal_metadata: missing_collections: ["news"]

### Requirement: Time Filter for Relevance
The system SHALL apply time filtering to exclude data outside the requested date range. Data older than the filter window MUST NOT appear in the context to prevent stale information from polluting prompts.

#### Scenario: Date filter applied
- GIVEN stock data for AAPL exists for 2024-Q1 and Q2
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[2024-01-01, 2024-03-31]) is called
- THEN the stocks_summary SHALL only include data from 2024-Q1
- AND the response SHALL include applied_filter: {start: 2024-01-01, end: 2024-03-31}
- AND data outside this range SHALL NOT appear in any summary

#### Scenario: Recent news only (time decay)
- GIVEN news data exists for AAPL spanning 2024-01-01 to 2024-06-30
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[2024-01-01, 2024-06-30], recency_days=14) is called
- THEN recent news (last 14 days) SHALL be prioritized in news_summary
- AND older news SHALL be included only if fewer than 5 recent articles exist
- AND the response SHALL include recency_note: "Prioritizing news from last 14 days"

### Requirement: Summary Statistics per Collection
Each collection summary SHALL provide actionable KPIs, not raw retrieved documents.

#### Scenario: Stock summary KPIs
- GIVEN stock data for AAPL over 30 days
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[...]) is called
- THEN stocks_summary SHALL include:
  - period_return_pct: float (percentage change over period)
  - volatility: float (standard deviation of daily returns)
  - avg_volume: integer (average daily volume)
  - trend: string ("bullish" | "bearish" | "neutral")
  - recent_prices: list of {date, close} (last 5 days)

#### Scenario: Sentiment summary KPIs
- GIVEN sentiment data for AAPL over 30 days
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[...]) is called
- THEN sentiment_summary SHALL include:
  - aggregate_score: float (-1.0 to 1.0)
  - dominant_sentiment: string ("positive" | "negative" | "neutral")
  - sentiment_trend: string ("improving" | "deteriorating" | "stable")
  - top_positive_days: list of {date, score} (top 3)
  - top_negative_days: list of {date, score} (bottom 3)

#### Scenario: News summary KPIs
- GIVEN news articles for AAPL over 30 days
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[...]) is called
- THEN news_summary SHALL include:
  - article_count: integer
  - top_themes: list of strings (most common topics)
  - sentiment_distribution: {positive: N, negative: N, neutral: N}
  - recent_headlines: list of {date, headline, source} (last 5)

### Requirement: Prompt-Ready Format
The context object SHALL be serializable to a format suitable for injecting into LLM prompts.

#### Scenario: Context serialized for prompt
- GIVEN a valid cross-collection context for AAPL
- WHEN get_cross_collection_context(symbol="AAPL", date_range=[...]) is called
- THEN the system SHALL provide a to_prompt_string() method
- AND the method SHALL return a formatted string like:
  ```
  AAPL Market Context (Jan 1-31, 2024):
  STOCKS: +5.2% return, volatility 18%, avg volume 52M, trend: bullish
  NEWS: 12 articles, themes: [earnings, AI], sentiment distribution: 6 positive, 4 neutral, 2 negative
  SENTIMENT: aggregate 0.42 positive, improving trend, top positive: Jan 15 (0.78)
  ```
- AND the response SHALL include prompt_tokens_estimate: integer

## Non-Functional Requirements

### Performance
- Cross-collection context for 30-day window SHALL complete within 5 seconds
- Each collection SHALL be queried in parallel (not sequentially)

### Error Handling
- If all collections return empty, the system SHALL raise NoDataError with available collections list
- If serialization fails, the system SHALL fall back to a minimal text summary