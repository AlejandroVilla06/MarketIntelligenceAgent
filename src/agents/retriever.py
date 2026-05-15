"""
Market RAG Retriever - ChromaDB-backed Market Data Retrieval
====================================================

ChromaDB-backed retriever for market data (stocks, news, sentiment).
Provides similarity search across vector collections.

Usage:
    from src.agents.retriever import MarketRAGRetriever
    retriever = MarketRAGRetriever()
    retriever.add_stock_data(df)
    results = retriever.query_stocks("AAPL tech stocks", k=5)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.utils import get_logger

if TYPE_CHECKING:
    from pathlib import Path

# =============================================================================
# CHROMADB COLLECTION CONSTANTS
# =============================================================================

COLLECTION_STOCKS: str = "market_stocks"
"""Collection name for stock data."""

COLLECTION_NEWS: str = "market_news"
"""Collection name for news data."""

COLLECTION_SENTIMENT: str = "market_sentiment"
"""Collection name for sentiment data."""

# =============================================================================
# EMBEDDING MODEL
# =============================================================================

EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
"""Default embedding model for vectorization."""


class MarketRAGRetriever:
    """
    ChromaDB-backed retriever for market data.

    Responsibilities:
    - Manage ChromaDB client and 3 collections (stocks, news, sentiment)
    - Add stock, news, and sentiment data as vector documents
    - Query collections via similarity search

    Usage:
        retriever = MarketRAGRetriever()
        retriever.add_stock_data(df)
        results = retriever.query_stocks("AAPL tech stocks", k=5)
    """

    def __init__(
        self,
        persist_directory: str | None = None,
    ) -> None:
        """
        Initialize ChromaDB client with 3 collections and embedding model.

        Args:
            persist_directory: Directory for ChromaDB persistence.
                           Defaults to settings.chromadb_persist_dir.
        """
        self.persist_directory = persist_directory or settings.chromadb_persist_dir
        self.collection_stocks = COLLECTION_STOCKS
        self.collection_news = COLLECTION_NEWS
        self.collection_sentiment = COLLECTION_SENTIMENT

        # Initialize ChromaDB client with persistent storage
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Initialize embedding function (shared singleton)
        from src.agents.embedding import get_embedding_model
        self._embedding_function = get_embedding_model()

        # Get or create collections
        self._stocks_collection = self._client.get_or_create_collection(
            name=self.collection_stocks,
        )
        self._news_collection = self._client.get_or_create_collection(
            name=self.collection_news,
        )
        self._sentiment_collection = self._client.get_or_create_collection(
            name=self.collection_sentiment,
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts using the embedding model.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        return self._embedding_function.encode(texts).tolist()

    # =============================================================================
    # ADD DATA METHODS
    # =============================================================================

    def add_stock_data(self, df: "pl.DataFrame") -> None:
        """
        Add stock data to the market_stocks collection.

        Document format: 'SYMBOL DATE close=X volume=Y RSI=Z'

        Args:
            df: Polars DataFrame with stock data.
                 Expected columns: symbol, date, close, volume, [rsi_14]
        """
        import polars as pl

        if df.is_empty():
            return

        # Convert DataFrame to list of dicts for processing
        rows = df.to_dicts()

        documents = []
        metadatas = []
        ids = []

        for i, row in enumerate(rows):
            # Format document string
            symbol = str(row.get("symbol", ""))
            date = str(row.get("date", ""))
            close = row.get("close", 0.0)
            volume = row.get("volume", 0)
            rsi = row.get("rsi_14", None)

            # Build document string
            doc_parts = [
                f"{symbol} {date}",
                f"close={close}",
                f"volume={volume}",
            ]
            if rsi is not None:
                doc_parts.append(f"RSI={rsi}")

            document = " ".join(doc_parts)
            documents.append(document)

            # Build metadata
            metadata = {
                "symbol": symbol,
                "date": date,
                "close": float(close),
                "volume": int(volume),
                "data_type": "stock",
            }
            if rsi is not None:
                metadata["rsi_14"] = float(rsi)

            metadatas.append(metadata)
            ids.append(f"stock_{symbol}_{date}_{i}")

        # Add to ChromaDB collection
        self._stocks_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=self._embed(documents),
        )

    def add_news_data(self, articles: list[dict]) -> None:
        """
        Add news data to the market_news collection.

        Document format: title + content
        Metadata: timestamp, source, symbol, sentiment_score

        Args:
            articles: List of news article dicts.
                      Expected keys: title, content, source, timestamp, symbol, [sentiment_score]
        """
        if not articles:
            return

        documents = []
        metadatas = []
        ids = []

        for i, article in enumerate(articles):
            title = str(article.get("title", ""))
            content = str(article.get("content", ""))
            source = str(article.get("source", ""))
            timestamp = str(article.get("timestamp", ""))
            symbol = str(article.get("symbol", ""))
            sentiment_score = article.get("sentiment_score")

            # Document is title + content
            document = f"{title}. {content}"
            documents.append(document)

            # Build metadata
            metadata = {
                "source": source,
                "timestamp": timestamp,
                "symbol": symbol,
                "data_type": "news",
            }
            if sentiment_score is not None:
                metadata["sentiment_score"] = float(sentiment_score)

            metadatas.append(metadata)
            ids.append(f"news_{symbol}_{timestamp}_{i}")

        # Add to ChromaDB collection
        self._news_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=self._embed(documents),
        )

    def add_sentiment_data(self, data: list[dict]) -> None:
        """
        Add sentiment data to the market_sentiment collection.

        Document format: 'SYMBOL sentiment X positive/negative/neutral on DATE'

        Args:
            data: List of sentiment dicts.
                  Expected keys: symbol, date, sentiment_score, sentiment_label
        """
        if not data:
            return

        documents = []
        metadatas = []
        ids = []

        for i, item in enumerate(data):
            symbol = str(item.get("symbol", ""))
            date = str(item.get("date", ""))
            sentiment_score = item.get("sentiment_score", 0.0)
            sentiment_label = str(item.get("sentiment_label", "neutral"))

            # Format document string
            document = f"{symbol} sentiment {sentiment_score} {sentiment_label} on {date}"
            documents.append(document)

            # Build metadata
            metadata = {
                "symbol": symbol,
                "date": date,
                "sentiment_score": float(sentiment_score),
                "sentiment_label": sentiment_label,
                "data_type": "sentiment",
            }

            metadatas.append(metadata)
            ids.append(f"sentiment_{symbol}_{date}_{i}")

        # Add to ChromaDB collection
        self._sentiment_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=self._embed(documents),
        )

    # =============================================================================
    # QUERY METHODS
    # =============================================================================

    def query_stocks(
        self,
        query: str,
        k: int | None = None,
    ) -> list[dict]:
        """
        Query the market_stocks collection.

        Args:
            query: Query string for similarity search.
            k: Number of results to return. Defaults to settings.rag_default_k.

        Returns:
            List of dicts with keys: document, metadata, distance
        """
        k = k or settings.rag_default_k

        results = self._stocks_collection.query(
            query_texts=[query],
            n_results=k,
            query_embeddings=self._embed([query]),
        )

        return self._format_query_results(results)

    def query_news(
        self,
        query: str,
        k: int | None = None,
    ) -> list[dict]:
        """
        Query the market_news collection.

        Args:
            query: Query string for similarity search.
            k: Number of results to return. Defaults to settings.rag_default_k.

        Returns:
            List of dicts with keys: document, metadata, distance
        """
        k = k or settings.rag_default_k

        results = self._news_collection.query(
            query_texts=[query],
            n_results=k,
            query_embeddings=self._embed([query]),
        )

        return self._format_query_results(results)

    def query_sentiment(
        self,
        query: str,
        k: int | None = None,
    ) -> list[dict]:
        """
        Query the market_sentiment collection.

        Args:
            query: Query string for similarity search.
            k: Number of results to return. Defaults to settings.rag_default_k.

        Returns:
            List of dicts with keys: document, metadata, distance
        """
        k = k or settings.rag_default_k

        results = self._sentiment_collection.query(
            query_texts=[query],
            n_results=k,
            query_embeddings=self._embed([query]),
        )

        return self._format_query_results(results)

    def query_all(
        self,
        query: str,
        k_per_collection: int | None = None,
    ) -> dict[str, list[dict]]:
        """
        Query all 3 collections and return merged results.

        Args:
            query: Query string for similarity search.
            k_per_collection: Number of results per collection. Defaults to settings.rag_default_k.

        Returns:
            Dict with keys: stocks, news, sentiment (each a list of dicts)
        """
        k = k_per_collection or settings.rag_default_k

        return {
            "stocks": self.query_stocks(query, k),
            "news": self.query_news(query, k),
            "sentiment": self.query_sentiment(query, k),
        }

    # =============================================================================
    # TEMPORAL FILTER QUERY METHODS
    # =============================================================================

    def query_by_metadata(
        self,
        collection: str,
        query: str,
        symbol: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        min_sentiment_score: float | None = None,
        max_sentiment_score: float | None = None,
        k: int | None = None,
    ) -> list[dict]:
        """
        Query a collection with metadata filters for temporal alignment.

        Implements the base query method for Phase 1 of Sprint 4,
        enabling temporal filters that the correlation tools depend on.

        Args:
            collection: One of "stocks", "news", or "sentiment".
            query: Query string for similarity search.
            symbol: Filter by symbol (e.g., "AAPL", "GOOGL").
            start_date: Filter by start date (YYYY-MM-DD format).
            end_date: Filter by end date (YYYY-MM-DD format).
            min_sentiment_score: Minimum sentiment score (0.0 to 1.0).
            max_sentiment_score: Maximum sentiment score (0.0 to 1.0).
            k: Number of results to return.

        Returns:
            List of dicts with keys: document, metadata, distance

        Raises:
            ValueError: If end_date is before start_date.
            ValueError: If collection is not one of "stocks", "news", "sentiment".
        """
        # Validate collection
        valid_collections = {"stocks", "news", "sentiment"}
        if collection not in valid_collections:
            raise ValueError(
                f"Invalid collection '{collection}'. Must be one of: {valid_collections}"
            )

        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise ValueError(
                    f"end_date '{end_date}' cannot be before start_date '{start_date}'"
                )

        # Validate sentiment score range
        if min_sentiment_score is not None and max_sentiment_score is not None:
            if min_sentiment_score > max_sentiment_score:
                raise ValueError(
                    f"min_sentiment_score {min_sentiment_score} cannot be greater than "
                    f"max_sentiment_score {max_sentiment_score}"
                )

        # Build where clause for ChromaDB filtering
        where_clause: dict = {}
        where_clause_symbol: dict = {}

        # Add symbol filter
        if symbol:
            where_clause_symbol["symbol"] = {"$eq": symbol}

        # Add symbol filter - this is the only filter ChromaDB supports well with strings
        if symbol:
            where_clause["symbol"] = {"$eq": symbol}

        # Get the appropriate collection
        collection_map = {
            "stocks": self._stocks_collection,
            "news": self._news_collection,
            "sentiment": self._sentiment_collection,
        }
        target_collection = collection_map[collection]

        # Execute query with metadata filters
        k = k or settings.rag_default_k
        
        # Always use query_embeddings when passing where clause
        if where_clause and query:
            results = target_collection.query(
                query_texts=[query],
                n_results=k,
                query_embeddings=self._embed([query]),
                where=where_clause,
            )
        elif query:
            results = target_collection.query(
                query_texts=[query],
                n_results=k,
                query_embeddings=self._embed([query]),
            )
        else:
            results = target_collection.query(
                query_texts=[""],
                n_results=k,
                where=where_clause if where_clause else None,
            )
        formatted_results = self._format_query_results(results)
        
        # Post-filter by date range and sentiment score (ChromaDB doesn't support these with strings)
        filtered_results = []
        for result in formatted_results:
            meta = result.get("metadata", {})
            match = True
            
            # Filter by date range
            if collection == "stocks":
                doc_date = meta.get("date", "")
                if start_date and doc_date and doc_date < start_date:
                    match = False
                if end_date and doc_date and doc_date > end_date:
                    match = False
            elif collection == "news":
                doc_date = meta.get("timestamp", "")[:10]  # Extract date part
                if start_date and doc_date and doc_date < start_date:
                    match = False
                if end_date and doc_date and doc_date > end_date:
                    match = False
            elif collection == "sentiment":
                doc_date = meta.get("date", "")
                if start_date and doc_date and doc_date < start_date:
                    match = False
                if end_date and doc_date and doc_date > end_date:
                    match = False
            
            # Filter by sentiment score
            if match and collection in ("news", "sentiment"):
                score = meta.get("sentiment_score")
                if min_sentiment_score is not None and (score is None or score < min_sentiment_score):
                    match = False
                if max_sentiment_score is not None and (score is None or score > max_sentiment_score):
                    match = False
            
            if match:
                filtered_results.append(result)
        
        return filtered_results

    def _format_query_results(self, results: dict) -> list[dict]:
        """
        Format ChromaDB query results into standard format.

        Args:
            results: Raw ChromaDB query results.

        Returns:
            List of dicts with keys: document, metadata, distance
        """
        if not results.get("documents") or not results["documents"][0]:
            return []

        formatted = []
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for doc, meta, distance in zip(docs, metas, distances):
            formatted.append({
                "document": doc,
                "metadata": meta,
                "distance": distance,
            })

        return formatted

    def reset(self) -> None:
        """Reset all collections (delete all data)."""
        self._client.delete_collection(name=self.collection_stocks)
        self._client.delete_collection(name=self.collection_news)
        self._client.delete_collection(name=self.collection_sentiment)

        # Recreate collections
        self._stocks_collection = self._client.get_or_create_collection(
            name=self.collection_stocks,
        )
        self._news_collection = self._client.get_or_create_collection(
            name=self.collection_news,
        )
        self._sentiment_collection = self._client.get_or_create_collection(
            name=self.collection_sentiment,
        )

    def seed_demo_data(self) -> None:
        """
        Seed demo data for testing and demonstration purposes.
        
        Adds sample stock, news, and sentiment data to ChromaDB collections
        when no real data is available.
        
        Useful for:
        - Initial demo/development without API keys
        - Testing the RAG pipeline
        - Verifying the dashboard counters work
        """
        from datetime import datetime, timedelta
        
        log = get_logger("retriever.seed_demo")
        
        # Demo stock data (last 30 days)
        symbols = ["AAPL", "GOOGL", "NVDA", "MSFT", "AMZN"]
        base_prices = {"AAPL": 175.0, "GOOGL": 140.0, "NVDA": 480.0, "MSFT": 380.0, "AMZN": 180.0}
        
        stock_records = []
        today = datetime.now()
        
        for symbol in symbols:
            base_price = base_prices.get(symbol, 100.0)
            for i in range(30):
                date = today - timedelta(days=29 - i)
                # Simulate realistic price movement
                variation = (hash(f"{symbol}{i}") % 100 - 50) / 100  # -0.5 to +0.5
                close = base_price * (1 + variation * 0.05)
                volume = 10_000_000 + (hash(f"{symbol}{i}") % 5_000_000)
                
                stock_records.append({
                    "symbol": symbol,
                    "date": date.strftime("%Y-%m-%d"),
                    "close": round(close, 2),
                    "volume": int(volume),
                    "rsi_14": 50 + (hash(f"{symbol}{i}") % 40 - 20),  # RSI 30-70
                })
        
        # Convert to Polars DataFrame
        import polars as pl
        stock_df = pl.DataFrame(stock_records)
        self.add_stock_data(stock_df)
        log.info(f"Seeded demo stock data: {len(stock_df)} records")
        
        # Demo news data
        news_articles = [
            {"title": "Apple reports strong Q4 earnings", "content": "Apple Inc. exceeded analyst expectations with record quarterly revenue driven by iPhone sales in China.", "source": "Bloomberg", "symbol": "AAPL", "sentiment_score": 0.85},
            {"title": "NVIDIA announces new AI chip", "content": "NVIDIA unveiled its next-generation AI accelerator, promising 2x performance improvement over previous generation.", "source": "Reuters", "symbol": "NVDA", "sentiment_score": 0.92},
            {"title": "Google Cloud revenue grows 28%", "content": "Alphabet's Google Cloud segment continues strong growth, beating estimates as enterprise AI adoption accelerates.", "source": "CNBC", "symbol": "GOOGL", "sentiment_score": 0.78},
            {"title": "Microsoft Azure expands AI services", "content": "Microsoft announced new AI-powered features for Azure, focusing on enterprise productivity and automation.", "source": "WSJ", "symbol": "MSFT", "sentiment_score": 0.72},
            {"title": "Amazon launches new logistics network", "content": "Amazon unveils advanced logistics system to speed up same-day delivery across major metropolitan areas.", "source": "TechCrunch", "symbol": "AMZN", "sentiment_score": 0.65},
            {"title": "Tech stocks rally on Fed comments", "content": "Technology sector leads market gains after Federal Reserve signals potential rate cuts in coming months.", "source": "Bloomberg", "symbol": "NVDA", "sentiment_score": 0.80},
            {"title": "Apple faces antitrust scrutiny in EU", "content": "European Union regulators launch formal investigation into Apple's App Store policies and NFC payments.", "source": "Reuters", "symbol": "AAPL", "sentiment_score": 0.25},
            {"title": "NVIDIA stock hits all-time high", "content": "Shares of NVIDIA surge to record levels as AI demand continues to exceed supply across data centers.", "source": "CNBC", "symbol": "NVDA", "sentiment_score": 0.95},
        ]
        
        for i, article in enumerate(news_articles):
            article["timestamp"] = (today - timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S")
        
        self.add_news_data(news_articles)
        log.info(f"Seeded demo news data: {len(news_articles)} articles")
        
        # Demo sentiment data
        sentiment_records = []
        for symbol in symbols:
            for i in range(14):
                date = today - timedelta(days=13 - i)
                score = 0.5 + (hash(f"{symbol}{i}") % 60 - 30) / 100
                label = "positive" if score > 0.6 else "negative" if score < 0.4 else "neutral"
                sentiment_records.append({
                    "symbol": symbol,
                    "date": date.strftime("%Y-%m-%d"),
                    "sentiment_score": round(score, 3),
                    "sentiment_label": label,
                })
        
        self.add_sentiment_data(sentiment_records)
        log.info(f"Seeded demo sentiment data: {len(sentiment_records)} records")

    def get_counts(self) -> dict[str, int]:
        """
        Get document counts for all collections.
        
        Returns:
            Dict with keys: stocks, news, sentiment (each an int count)
        """
        return {
            "stocks": self._stocks_collection.count(),
            "news": self._news_collection.count(),
            "sentiment": self._sentiment_collection.count(),
        }


__all__ = [
    "MarketRAGRetriever",
    "COLLECTION_STOCKS",
    "COLLECTION_NEWS",
    "COLLECTION_SENTIMENT",
    "EMBEDDING_MODEL",
]