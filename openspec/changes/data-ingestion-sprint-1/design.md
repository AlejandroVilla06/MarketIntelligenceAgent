# Design: Sprint 1 - Data Ingestion Layer

## Technical Approach

Implement a modular data ingestion pipeline with pluggable data sources (yfinance, Alpha Vantage, Polygon.io) for stock data and news/sentiment scrapers. Use Polars for efficient data processing and validation. All data will be saved as partitioned Parquet files in the processed directory for fast retrieval by ML models and RAG agents.

## Architecture Decisions

### Decision: Data Source Abstraction Pattern

**Choice**: Use a strategy pattern with a base `DataSource` interface and concrete implementations for each provider (yfinance, AlphaVantage, PolygonIO).

**Alternatives considered**: 
- Factory pattern with conditional logic
- Dependency injection container
- Direct calls in pipeline (no abstraction)

**Rationale**: Strategy pattern allows easy addition of new providers without modifying pipeline logic, follows Open/Closed principle, and makes testing easier with mock implementations.

### Decision: Data Validation Separation

**Choice**: Separate validation and cleaning into distinct stages after ingestion but before persistence.

**Alternatives considered**:
- Validate during ingestion (in each data source)
- Validate only at persistence time
- No validation (rely on consumers to handle bad data)

**Rationale**: Separation of concerns - ingestion focuses on fetching, validation ensures data quality, cleaning fixes common issues. This makes each stage testable and replaceable.

### Decision: Partitioned Parquet Storage

**Choice**: Store processed data in Parquet files partitioned by date and symbol (e.g., data/processed/stocks/symbol=AAPL/date=2024-01-15/data.parquet).

**Alternatives considered**:
- Single large Parquet file per symbol
- CSV/JSON format
- Database storage (SQLite/PostgreSQL)

**Rationale**: Parquet provides efficient columnar storage, compression, and fast predicate pushdown. Partitioning allows efficient querying of specific symbols/date ranges without scanning entire datasets.

### Decision: News Sentiment Pipeline Separation

**Choice**: Keep news scraping and sentiment analysis as separate stages within the news pipeline.

**Alternatives considered**:
- Combine scraping and sentiment in one step
- Perform sentiment analysis at query time (in RAG agent)
- Use external sentiment API

**Rationale**: Separation allows independent scaling and updating of sentiment models. Storing sentiment scores with news enables fast retrieval without recomputation.

## Data Flow

```
Stock Data Flow:
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│ Data Source │──▶│ Ingestion    │──▶│ Validation     │──▶│ Persistence    │
│ (yfinance,  │    │ Coordinator  │   │ & Cleaning     │   │ (Parquet)      │
│ AlphaVantage)│    │              │   │                │   │                │
└─────────────┘    └──────────────┘    └────────────────┘    └────────────────┘
                                                               │
                                                               ▼
                                                    ┌────────────────┐
                                                    │  ML Models     │
                                                    │  & RAG Agent   │
                                                    └────────────────┘

News Sentiment Flow:
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│ News Source │──▶│ Scraping     │──▶│ Sentiment      │──▶│ Persistence    │
│ (GoogleNews,│    │ Coordinator  │   │ Analysis       │   │ (Parquet)      │
│ RSS)        │    │              │   │ (TextBlob/VADER)│   │                │
└─────────────┘    └──────────────┘    └────────────────┘    └────────────────┘
                                                               │
                                                               ▼
                                                    ┌────────────────┐
                                                    │  RAG Agent     │
                                                    └────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/data_engine/pipelines/stock_pipeline.py` | Modify | Enhanced with multi-source support, fallback logic, and source selection |
| `src/data_engine/pipelines/__init__.py` | Create | Export enhanced StockPipeline |
| `src/data_engine/pipelines/news_pipeline.py` | Create | New pipeline for news scraping and sentiment analysis |
| `src/data_engine/scrapers/__init__.py` | Create | Export news scrapers |
| `src/data_engine/scrapers/google_news.py` | Create | Google News scraper using requests and BeautifulSoup |
| `src/data_engine/scrapers/rss.py` | Create | RSS feed scraper using feedparser |
| `src/data_engine/validation/__init__.py` | Create | Export validation functions |
| `src/data_engine/validation/validator.py` | Create | Schema validation and data cleaning functions |
| `src/data_engine/storage.py` | Create | Unified storage interface for Parquet read/write operations |
| `src/config/__init__.py` | Modify | Add news API keys, data source flags, and validation configuration |
| `tests/test_stock_pipeline.py` | Create | Unit tests for enhanced stock pipeline |
| `tests/test_news_pipeline.py` | Create | Unit tests for news pipeline |
| `tests/test_validation.py` | Create | Unit tests for validation and cleaning |
| `tests/test_storage.py` | Create | Unit tests for storage layer |
| `src/data_engine/__init__.py` | Modify | Expose new subpackages (pipelines, scrapers, validation, storage) |
| `run_ingestion.py` | Create | CLI script to orchestrate data ingestion jobs |

## Interfaces / Contracts

### DataSource Interface (Python Protocol)
```python
from typing import Protocol, runtime_checkable
import polars as pl
from datetime import datetime

@runtime_checkable
class DataSource(Protocol):
    def fetch(self, symbol: str, start_date: datetime, end_date: datetime) -> pl.DataFrame:
        """Fetch OHLCV data for symbol between start_date and end_date.
        
        Returns:
            Polars DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
            Empty DataFrame if no data available.
        """
        ...
```

### NewsArticle Data Structure
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NewsArticle:
    title: str
    source: str
    timestamp: datetime
    url: str
    symbol: str  # Related stock symbol
    sentiment_score: float  # -1 to 1
```

### Storage Interface
```python
class StorageInterface:
    def save_stocks(self, df: pl.DataFrame, partition_by: list[str] = None) -> str:
        """Save stock data as partitioned Parquet.
        
        Returns:
            Path to saved data
        """
        ...
    
    def load_stocks(self, symbols: list[str] = None, 
                   start_date: datetime = None,
                   end_date: datetime = None) -> pl.DataFrame:
        """Load stock data with optional filtering.
        
        Returns:
            Polars DataFrame with stock data
        """
        ...
    
    def save_news(self, df: pl.DataFrame, partition_by: list[str] = None) -> str:
        """Save news data as partitioned Parquet."""
        ...
    
    def load_news(self, symbols: list[str] = None,
                 start_date: datetime = None,
                 end_date: datetime = None) -> pl.DataFrame:
        """Load news data with optional filtering."""
        ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | DataSource implementations | Mock HTTP responses, test parsing logic |
| Unit | Validation functions | Test with various data quality issues (missing values, wrong types, outliers) |
| Unit | News scrapers | Mock HTML/RSS responses, test article extraction |
| Unit | Sentiment analysis | Test with known positive/negative/neutral texts |
| Unit | Storage layer | Test Parquet read/write with Polars, test partitioning |
| Integration | Stock pipeline end-to-end | Use actual yfinance (with mock fallback) to fetch and save small dataset |
| Integration | News pipeline end-to-end | Use actual RSS feeds (e.g., Yahoo Finance RSS) to fetch and process news |
| Integration | Full ingestion orchestration | Test CLI script runs all pipelines and saves expected files |
| Property-based | Data validation | Use hypothesis to generate edge case dataframes and validate invariants |

## Migration / Rollout

**No migration required.** This is a new feature addition.

- The existing `src/data_engine/pipelines/stock_pipeline.py` is enhanced but backward compatible (default behavior unchanged if only yfinance configured)
- No changes to existing data formats or storage locations
- New directories created under `src/data_engine/` do not affect existing code
- Configuration additions are optional - existing .env continues to work

To rollback:
1. Revert `src/data_engine/pipelines/stock_pipeline.py` to previous version
2. Remove newly created directories: `src/data_engine/scrapers/`, `src/data_engine/validation/`, `src/data_engine/storage.py`
3. Revert config.py additions (or ignore them - they're optional)
4. Remove test files for new components

## Open Questions

- [ ] Should we implement caching layer for API responses to reduce redundant calls?
- [ ] What sentiment analysis library should we default to? (TextBlob vs VADER vs FinBERT)
- [ ] Should we store raw news articles or only processed sentiment scores?
- [ ] How should we handle timezone conversions for datetime data from different sources?
- [ ] Should we implement automatic retry with exponential backoff for failed API calls?
