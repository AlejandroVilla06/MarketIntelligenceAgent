# Sentiment-Price Correlation Specification

## Purpose

Define requirements for correlating Llama 3.1 sentiment analysis scores with stock price movements. The system MUST provide statistical correlation metrics (Pearson, Spearman) aligned by symbol and time window, with explicit time filtering to prevent meaningless correlations when data does not overlap.

## Requirements

### Requirement: Time-Windowed Correlation
The system SHALL compute correlation only when sentiment and stock data overlap in the requested time window. If no overlap exists, the system SHALL return a clear warning and NOT a misleading correlation value.

#### Scenario: Full overlap — correlation computed
- GIVEN sentiment data exists for AAPL from 2024-01-01 to 2024-01-31
- AND stock price data exists for AAPL from 2024-01-01 to 2024-01-31
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the system SHALL return correlation stats for the 30-day overlapping window
- AND the response SHALL include start_date and end_date of the actual overlap used

#### Scenario: Partial overlap — correlation with warning
- GIVEN sentiment data exists for AAPL from 2024-01-15 to 2024-01-31
- AND stock price data exists for AAPL from 2024-01-01 to 2024-01-31
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the system SHALL compute correlation for the 16-day overlap (Jan 15-31)
- AND the response SHALL include warning: "Overlap limited to 16 days — results may not be statistically significant"
- AND the response SHALL include actual_overlap_days: 16

#### Scenario: No overlap — error returned
- GIVEN sentiment data exists for AAPL from 2024-01-01 to 2024-01-15
- AND stock price data exists for AAPL from 2024-02-01 to 2024-02-28
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the system SHALL return result with status: "no_overlap"
- AND the response SHALL include available_sentiment_range and available_price_range
- AND the system SHALL NOT fabricate a correlation value

### Requirement: Correlation Metrics
The system SHALL compute multiple correlation metrics to capture different relationship patterns.

#### Scenario: Positive correlation detected
- GIVEN sentiment and stock data for AAPL over 30 days with positive relationship
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the system SHALL return a dictionary with keys:
  - pearson_coefficient: float between -1.0 and 1.0
  - spearman_coefficient: float between -1.0 and 1.0
  - sentiment_direction: "positive" | "negative" | "neutral"
  - price_direction: "up" | "down" | "flat"
  - p_value: float (statistical significance threshold)

#### Scenario: Negative correlation detected
- GIVEN sentiment and stock data where sentiment moves opposite to price
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the pearson_coefficient SHALL be negative (e.g., -0.65)
- AND the spearman_coefficient SHALL also be negative

### Requirement: Per-Day Breakdown
The system SHALL return per-day data so callers can inspect the raw relationship.

#### Scenario: Daily data returned
- GIVEN valid sentiment and stock data overlap for AAPL
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the response SHALL include a daily_breakdown list with:
  - date: ISO date string
  - sentiment_score: float (-1.0 to 1.0)
  - price_close: float
  - price_change_pct: float
- AND the list SHALL be sorted by date ascending

### Requirement: Minimum Data Threshold
The system SHALL NOT compute correlation with fewer than 10 overlapping data points.

#### Scenario: Insufficient data points
- GIVEN fewer than 10 overlapping sentiment/stock data points
- WHEN get_sentiment_price_correlation(symbol="AAPL", window_days=30) is called
- THEN the system SHALL return status: "insufficient_data"
- AND the response SHALL include overlap_count: {actual count}
- AND the response SHALL NOT compute correlation metrics

## Non-Functional Requirements

### Performance
- Correlation computation for 30-day window SHALL complete within 3 seconds
- Daily breakdown list SHALL be limited to 365 entries maximum (truncate oldest)

### Error Handling
- If symbol not found in either collection, the system SHALL raise SymbolNotFoundError
- If Ollama is unavailable for sentiment, the system SHALL fall back to stored sentiment scores