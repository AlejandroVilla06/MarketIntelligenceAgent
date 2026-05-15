# Delta for market-rag-retriever
## ADDED Requirements

### Requirement: Metadata-Based Filtering Query

The system SHALL provide a method to query ChromaDB collections by metadata filters (symbol, date range) WITHOUT semantic similarity search. This enables precise temporal alignment and correlation queries where the system already knows the exact filter criteria.

#### Scenario: Filter by symbol only
- GIVEN the retriever has stock data in ChromaDB
- WHEN query_by_metadata(collection="stocks", symbol="AAPL") is called
- THEN the system SHALL return all documents where metadata.symbol == "AAPL"
- AND the results SHALL be ordered by date ascending

#### Scenario: Filter by symbol and date range
- GIVEN the retriever has stock data in ChromaDB
- WHEN query_by_metadata(collection="stocks", symbol="AAPL", start_date="2024-01-01", end_date="2024-01-31") is called
- THEN the system SHALL return all documents where:
  - metadata.symbol == "AAPL"
  - AND metadata.date >= "2024-01-01"
  - AND metadata.date <= "2024-01-31"
- AND the results SHALL be ordered by date ascending

#### Scenario: Filter by sentiment score range
- GIVEN the retriever has sentiment data in ChromaDB
- WHEN query_by_metadata(collection="sentiment", symbol="AAPL", min_score=0.5) is called
- THEN the system SHALL return all documents where:
  - metadata.symbol == "AAPL"
  - AND metadata.sentiment_score >= 0.5

#### Scenario: Empty result for non-existent symbol
- GIVEN the retriever has stock data in ChromaDB
- WHEN query_by_metadata(collection="stocks", symbol="XYZ999") is called
- THEN the system SHALL return an empty list
- AND the response SHALL include available_symbols_sample: list of 5 symbols from the collection

#### Scenario: Invalid date range — error
- GIVEN the retriever is initialized
- WHEN query_by_metadata(collection="stocks", start_date="2024-01-31", end_date="2024-01-01") is called
- THEN the system SHALL raise ValueError with message: "end_date must be after start_date"

## ADDED Requirements

### Requirement: Interface Extension

The retriever class SHALL add the following method:

- `query_by_metadata(collection: str, symbol: str = None, start_date: str = None, end_date: str = None, min_score: float = None, max_score: float = None, k: int = 1000) -> List[Dict]`

Parameters:
- `collection`: one of "stocks", "news", "sentiment"
- `symbol`: optional ticker symbol filter
- `start_date`: optional ISO date string (inclusive)
- `end_date`: optional ISO date string (inclusive)
- `min_score`: optional minimum sentiment score filter
- `max_score`: optional maximum sentiment score filter
- `k`: maximum number of results (default 1000)

Returns a list of dictionaries with keys: `document`, `metadata`, `distance`.