# Market RAG Retriever Specification

## Purpose

Define the requirements for a ChromaDB-backed retriever that provides semantic search over market data (stock prices, news, sentiment). The retriever shall enable natural language querying by returning relevant context for a given query.

## Requirements

### Requirement: ChromaDB Collections

The system SHALL maintain separate ChromaDB collections for each data type: stocks, news, sentiment.

#### Scenario: Initialize collections
- GIVEN the retriever is initialized
- WHEN the system starts
- THEN the system SHALL create three ChromaDB collections: `market_stocks`, `market_news`, `market_sentiment`
- AND each collection SHALL use the sentence-transformers/all-MiniLM-L6-v2 embedding function

#### Scenario: Add stock data
- GIVEN a DataFrame with stock data (symbol, date, close, volume, technical indicators)
- WHEN add_stock_data() is called with the DataFrame
- THEN each row SHALL be added to the `market_stocks` collection with metadata including symbol, date, and relevant features
- AND the document SHALL be a text representation of the row (e.g., "AAPL 2024-01-15 close=170.2 volume=50M RSI=65")

#### Scenario: Add news data
- GIVEN a list of news articles with title, content, timestamp, and sentiment score
- WHEN add_news_data() is called with the list
- THEN each article SHALL be added to the `market_news` collection with metadata including timestamp, source, sentiment
- AND the document SHALL be the article content or title + content

#### Scenario: Add sentiment data
- GIVEN aggregated sentiment data per symbol per day
- WHEN add_sentiment_data() is called with the data
- THEN each entry SHALL be added to the `market_sentiment` collection with metadata including symbol, date, sentiment score
- AND the document SHALL be a summary like "AAPL sentiment 0.7 positive on 2024-01-15"

### Requirement: Similarity Search

The system SHALL perform similarity search over the collections to retrieve relevant context for a query.

#### Scenario: Search stocks
- GIVEN the retriever has stock data in ChromaDB
- WHEN query_stocks("What is the trend for AAPL?") is called
- THEN the system SHALL return the top k most similar documents from `market_stocks`
- AND each result SHALL include the document text, metadata, and similarity score

#### Scenario: Search news
- GIVEN the retriever has news data in ChromaDB
- WHEN query_news("Recent news about Tesla") is called
- THEN the system SHALL return the top k most similar documents from `market_news`

#### Scenario: Combined search
- GIVEN the retriever has data in all collections
- WHEN query_all("How did news affect AAPL stock last week?") is called
- THEN the system SHALL return results from all three collections, ranked by relevance
- AND the system SHALL allow weighting collections differently (e.g., news weight 0.4, stocks 0.4, sentiment 0.2)

### Requirement: Interface

The retriever SHALL provide a Python class with the following methods:

- `__init__(persist_directory: str = "data/vector_store")`
- `add_stock_data(df: pl.DataFrame) -> None`
- `add_news_data(articles: List[Dict]) -> None`
- `add_sentiment_data(data: List[Dict]) -> None`
- `query_stocks(query: str, k: int = 5) -> List[Dict]`
- `query_news(query: str, k: int = 5) -> List[Dict]`
- `query_sentiment(query: str, k: int = 5) -> List[Dict]`
- `query_all(query: str, k_per_collection: int = 3) -> Dict[str, List[Dict]]`

Each query method returns a list of dictionaries with keys: `document`, `metadata`, `distance` (or `similarity`).

## Non-Functional Requirements

### Performance
- The system SHALL load the embedding model once at initialization and reuse it.
- Adding 10,000 records SHALL complete within 30 seconds on a modern laptop.
- A single query SHALL return results within 2 seconds.

### Persistence
- The system SHALL persist ChromaDB data to disk so that collections survive restarts.
- The persist directory SHALL be configurable via the constructor.

### Error Handling
- If ChromaDB is not available, the system SHALL raise a clear ImportError.
- If the embedding model fails to load, the system SHALL log an error and raise RuntimeError.
