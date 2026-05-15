# Tasks: Sprint 1 - Data Ingestion Layer

## Phase 1: Foundation and Infrastructure

- [x] 1.1 Create `src/data_engine/storage.py` with StorageInterface class for Parquet read/write operations
- [x] 1.2 Create `src/data_engine/pipelines/__init__.py` to export pipeline classes
- [x] 1.3 Create `src/data_engine/scrapers/__init__.py` to export news scrapers
- [x] 1.4 Create `src/data_engine/validation/__init__.py` to export validation functions
- [x] 1.5 Update `src/data_engine/__init__.py` to expose pipelines, scrapers, validation, and storage subpackages
- [x] 1.6 Update `src/config/__init__.py` to add news API keys (NEWSAPI_KEY, etc.), data source flags, and validation configuration
- [x] 1.7 Create `src/data_engine/pipelines/news_pipeline.py` skeleton with NewsPipeline class definition

## Phase 2: Core Implementation

- [x] 2.1 Enhance `src/data_engine/pipelines/stock_pipeline.py` with multi-source support:
    - Add DataSource protocol interface
    - Implement yfinance, AlphaVantage, and PolygonIO concrete classes
    - Add fallback logic and source selection based on configuration
- [x] 2.2 Implement `src/data_engine/scrapers/google_news.py`:
    - Add GoogleNewsScraper class to fetch financial news from Google News
    - Include HTML parsing with requests and BeautifulSoup
    - Return articles with title, source, timestamp, URL
- [x] 2.3 Implement `src/data_engine/scrapers/rss.py`:
    - Add RSSFeedScraper class to parse RSS feeds
    - Include feedparser integration
    - Return news entries with title, source, timestamp, URL
- [x] 2.4 Implement `src/data_engine/pipelines/news_pipeline.py`:
    - Add NewsPipeline class that coordinates scrapers
    - Include deduplication and sorting by timestamp
    - Add sentiment analysis using TextBlob and VADER
- [x] 2.5 Implement `src/data_engine/validation/validator.py`:
    - Add schema validation functions for stock and news data
    - Add data cleaning functions (forward fill, deduplication, invalid price filtering, IQR outlier removal)
    - Add data quality reporting functionality

## Phase 3: Integration, Testing, and Orchestration

- [x] 3.1 Create `tests/test_storage.py`:
    - Test Parquet read/write operations
    - Test partitioning functionality
    - Test error handling for missing files
- [x] 3.2 Create `tests/test_stock_pipeline.py`:
    - Test single source fetching (yfinance)
    - Test fallback mechanism when primary source fails
    - Test data format standardization
    - Test empty data handling
- [x] 3.3 Create `tests/test_news_pipeline.py`:
    - Test Google News scraper with mocked HTML
    - Test RSS scraper with mocked XML
    - Test sentiment analysis with known positive/negative/neutral texts
    - Test deduplication and sorting
- [x] 3.4 Create `tests/test_validation.py`:
    - Test schema validation (valid and invalid cases)
    - Test data cleaning functions
    - Test data quality report generation
- [x] 3.5 Create `run_ingestion.py` CLI script:
    - Add command-line interface to run specific ingestion jobs
    - Include options for stock data, news sentiment, or both
    - Add logging and progress reporting
    - Handle configuration from environment variables
- [x] 3.6 Create `tests/test_data_ingestion_integration.py`:
    - Test end-to-end stock pipeline with actual yfinance (small dataset)
    - Test end-to-end news pipeline with actual RSS feed
    - Verify saved Parquet files can be loaded correctly

## Phase 4: Documentation and Cleanup

- [x] 4.1 Update `README.md` with Sprint 1 accomplishments and usage instructions
- [x] 4.2 Add docstrings to all new classes and functions following existing style
- [x] 4.3 Review and fix any linting issues (if using pylint/ruff)
- [x] 4.4 Verify all imports work correctly by running a smoke test