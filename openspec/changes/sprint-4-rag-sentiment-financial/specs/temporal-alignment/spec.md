# Temporal Alignment Specification

## Purpose

Define requirements for aligning sentiment and stock data with different temporal frequencies (sentiment: daily aggregates, prices: intraday or daily) into a unified DataFrame by symbol and date range. The system MUST validate temporal overlap before attempting alignment to prevent silent data loss.

## Requirements

### Requirement: Temporal Overlap Validation
The system SHALL validate that requested date ranges overlap with available data BEFORE attempting alignment. The system MUST NOT silently drop data or produce misleading aligned output.

#### Scenario: Date range fully within available data
- GIVEN sentiment data for AAPL spans 2024-01-01 to 2024-01-31
- AND stock price data for AAPL spans 2024-01-01 to 2024-01-31
- WHEN align_by_temporal_window(symbol="AAPL", start="2024-01-01", end="2024-01-31") is called
- THEN the system SHALL return a DataFrame aligned for all 31 days
- AND the response SHALL include validation_metadata:
  - sentiment_available: [2024-01-01, 2024-01-31]
  - stock_available: [2024-01-01, 2024-01-31]
  - requested: [2024-01-01, 2024-01-31]
  - aligned: [2024-01-01, 2024-01-31]
  - overlap_valid: true

#### Scenario: Date range partially outside sentiment data
- GIVEN sentiment data for AAPL spans 2024-01-15 to 2024-01-31
- AND stock price data for AAPL spans 2024-01-01 to 2024-01-31
- WHEN align_by_temporal_window(symbol="AAPL", start="2024-01-01", end="2024-01-31") is called
- THEN the DataFrame SHALL contain only the overlapping period (Jan 15-31)
- AND the response SHALL include warning: "Sentiment data missing for Jan 1-14"
- AND overlap_valid SHALL be false
- AND the response SHALL include excluded_sentiment_dates: ["2024-01-01", ..., "2024-01-14"]

#### Scenario: Date range completely outside all data
- GIVEN sentiment data for AAPL spans 2024-01-01 to 2024-01-31
- AND stock price data for AAPL spans 2024-01-01 to 2024-01-31
- WHEN align_by_temporal_window(symbol="AAPL", start="2025-01-01", end="2025-01-31") is called
- THEN the system SHALL return an empty DataFrame
- AND the response SHALL include status: "no_overlap"
- AND the response SHALL include available_range: [2024-01-01, 2024-01-31]
- AND the system SHALL raise DataNotFoundError

### Requirement: DataFrame Output Structure
The aligned DataFrame SHALL contain normalized columns from both sources.

#### Scenario: Valid alignment returned
- GIVEN valid overlapping data for AAPL
- WHEN align_by_temporal_window(symbol="AAPL", start="2024-01-01", end="2024-01-31") is called
- THEN the returned DataFrame SHALL contain columns:
  - date: ISO date string
  - symbol: string
  - sentiment_score: float (-1.0 to 1.0)
  - sentiment_label: string ("positive" | "negative" | "neutral")
  - price_close: float
  - price_volume: integer
  - price_change_pct: float
  - price_change_direction: string ("up" | "down" | "flat")
- AND each row SHALL have one entry per date in the overlap

#### Scenario: Missing sentiment for some dates in range
- GIVEN sentiment data exists only for trading days (excludes weekends)
- AND stock price data exists for all calendar days
- WHEN align_by_temporal_window(symbol="AAPL", start="2024-01-01", end="2024-01-07") is called
- THEN the DataFrame SHALL contain NaN for sentiment_score on weekend dates (Jan 6-7)
- AND the response SHALL include missing_sentiment_dates: list of dates without sentiment

### Requirement: Aggregation for Different Frequencies
The system SHALL normalize price data to match sentiment frequency when they differ.

#### Scenario: Daily sentiment with intraday prices — normalize to daily
- GIVEN sentiment data is aggregated daily
- AND price data is available at hourly frequency
- WHEN align_by_temporal_window(symbol="AAPL", start="2024-01-01", end="2024-01-31") is called
- THEN the system SHALL use daily close price (last intraday price of each day)
- AND the system SHALL compute daily volume from intraday volume
- AND the response SHALL include aggregation_note: "Price data normalized to daily (close price per day)"

### Requirement: Time Filter Parameters
The system SHALL accept explicit time filter parameters to control the alignment window.

#### Scenario: Custom time filter with lookback
- GIVEN valid data for AAPL spanning multiple months
- WHEN align_by_temporal_window(symbol="AAPL", start="2024-01-01", end="2024-01-31", lookback_days=7) is called
- THEN the system SHALL extend the effective query to include 7 days before start for context
- AND the returned DataFrame SHALL exclude the lookback period from results
- AND the lookback data SHALL only be used for computing price_change_pct

## Non-Functional Requirements

### Performance
- Alignment for a 30-day window SHALL complete within 2 seconds
- The aligned DataFrame SHALL be limited to 365 rows maximum

### Error Handling
- If symbol not found, the system SHALL raise SymbolNotFoundError with available symbols list
- If DataFrame is empty after alignment, the system SHALL raise EmptyResultError