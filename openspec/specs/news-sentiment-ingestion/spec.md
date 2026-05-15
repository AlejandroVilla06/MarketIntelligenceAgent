# News Sentiment Ingestion Specification

## Purpose

Define the requirements for scraping financial news from multiple sources, performing sentiment analysis, and storing the results for consumption by the RAG agent.

## Requirements

### Requirement: News Source Support

The system SHALL support scraping financial news from multiple sources with configurable providers.

#### Scenario: Google News scraping
- GIVEN Google News is configured as a news source
- WHEN the news pipeline runs for symbol AAPL
- THEN the system SHALL scrape financial news articles related to AAPL from Google News
- AND the system SHALL return articles with title, source, timestamp, and URL

#### Scenario: RSS feed scraping
- GIVEN an RSS feed URL is configured for financial news
- WHEN the news pipeline runs
- THEN the system SHALL parse the RSS feed and extract news entries
- AND the system SHALL return entries with title, source, timestamp, and URL

#### Scenario: Multiple sources aggregation
- GIVEN multiple news sources are configured (Google News, RSS feeds)
- WHEN the news pipeline runs
- THEN the system SHALL combine results from all sources
- AND the system SHALL deduplicate articles by URL
- AND the system SHALL sort articles by timestamp descending

### Requirement: Sentiment Analysis

The system SHALL perform sentiment analysis on news articles using NLP models. The system SHALL support multiple sentiment providers: TextBlob, VADER, and Llama 3.1 via Ollama.

#### Scenario: TextBlob sentiment
- GIVEN an English news article with positive language about a stock
- WHEN sentiment analysis is performed
- THEN the system SHALL return a polarity score between -1 and 1
- AND positive text SHALL yield a score > 0
- AND negative text SHALL yield a score < 0
- AND neutral text SHALL yield a score near 0

#### Scenario: VADER sentiment for social media text
- GIVEN a financial tweet or Reddit post
- WHEN VADER sentiment analysis is performed
- THEN the system SHALL return a compound score between -1 and 1
- AND the system SHALL handle financial slang and emojis appropriately

#### Scenario: Llama 3.1 sentiment analysis
- GIVEN a financial news article
- WHEN Llama 3.1 sentiment analysis is selected as the provider
- THEN the system SHALL connect to Ollama for inference
- AND the system SHALL return a score between -1 and 1
- AND the system SHALL consider financial context in the assessment

#### Scenario: Llama fallback
- GIVEN Llama 3.1 is configured but Ollama is not available
- WHEN the news pipeline runs
- THEN the system SHALL automatically fall back to the configured fallback provider (TextBlob or VADER)
- AND the pipeline SHALL continue without error

### Requirement: News Data Persistence

The system SHALL store processed news and sentiment data for downstream consumption.

#### Scenario: Save to Parquet
- GIVEN a DataFrame with news articles and sentiment scores
- WHEN the news pipeline saves the data
- THEN the system SHALL write a Parquet file to data/processed/news/
- AND the filename SHALL include the date and symbol
- AND the system SHALL log the save location

#### Scenario: Schema preservation
- GIVEN news data with columns: ['title', 'source', 'timestamp', 'url', 'symbol', 'sentiment_score']
- WHEN the data is saved and loaded
- THEN the loaded DataFrame SHALL have the same schema
- AND all data types SHALL be preserved

### Requirement: Configurable News Sources and Keywords

The system SHALL allow configuration of news sources and keywords via environment variables.

#### Scenario: Custom news sources
- GIVEN the environment variable NEWS_SOURCES is set to "google_news,rss"
- WHEN the news pipeline initializes
- THEN the system SHALL use Google News and RSS feeds as sources
- AND the system SHALL log the configured sources

#### Scenario: Custom keywords
- GIVEN the environment variable NEWS_KEYWORDS is set to "AAPL,Apple,stock"
- WHEN the news pipeline runs for symbol AAPL
- THEN the system SHALL filter articles containing any of the keywords
- AND the system SHALL perform case-insensitive matching