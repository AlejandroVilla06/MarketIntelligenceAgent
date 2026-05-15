# Stock Data Ingestion Specification

## Purpose

Define the requirements for ingesting stock market data from multiple financial data providers (yfinance, Alpha Vantage, Polygon.io) and storing it in a processed format for downstream consumption by ML models and RAG agents.

## Requirements

### Requirement: Multiple Data Source Support

The system SHALL support fetching stock data from multiple providers with automatic fallback.

#### Scenario: Primary source available
- GIVEN yfinance is accessible and returns data for AAPL
- WHEN the stock pipeline requests data for AAPL
- THEN the system SHALL use yfinance as the primary source
- AND the system SHALL return the OHLCV data for AAPL

#### Scenario: Primary source fails, secondary succeeds
- GIVEN yfinance returns empty data for AAPL due to rate limiting
- GIVEN Alpha Vantage is configured and accessible
- WHEN the stock pipeline requests data for AAPL
- THEN the system SHALL fall back to Alpha Vantage
- AND the system SHALL return the OHLCV data for AAPL from Alpha Vantage

#### Scenario: All sources fail
- GIVEN all configured data providers (yfinance, Alpha Vantage, Polygon.io) fail or return empty data
- WHEN the stock pipeline requests data for AAPL
- THEN the system SHALL return an empty DataFrame
- AND the system SHALL log an error for each failed source

### Requirement: Data Format Standardization

The system SHALL standardize all fetched data to a common format.

#### Scenario: Standardized columns
- GIVEN data fetched from any provider
- WHEN the data is processed by the pipeline
- THEN the system SHALL return a DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']
- AND the 'date' column SHALL be of datetime type
- AND the 'open', 'high', 'low', 'close' SHALL be float type
- AND the 'volume' SHALL be integer type

### Requirement: Data Persistence

The system SHALL save processed data to Parquet files in the processed directory.

#### Scenario: Save to Parquet
- GIVEN a non-empty DataFrame with stock data
- WHEN the pipeline saves the data
- THEN the system SHALL write a Parquet file to data/processed/
- AND the filename SHALL include the date range and symbol
- AND the system SHALL log the save location

### Requirement: Configurable Symbols and Date Range

The system SHALL allow configuration of stock symbols and lookback period via environment variables.

#### Scenario: Custom symbols from config
- GIVEN the environment variable TRACKED_SYMBOLS is set to "AAPL,GOOGL"
- WHEN the pipeline initializes
- THEN the system SHALLOW use ['AAPL', 'GOOGL'] as the symbols to fetch
- AND the system SHALL log the configured symbols

#### Scenario: Custom lookback days
- GIVEN the environment variable TRAINING_LOOKBACK_DAYS is set to 100
- WHEN the pipeline runs without specifying days
- THEN the system SHALL use 100 days as the lookback period