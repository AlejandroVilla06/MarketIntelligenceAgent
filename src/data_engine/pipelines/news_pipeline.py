"""
News Pipeline - Financial News ETL
===================================

Fetches financial news from various sources and performs sentiment analysis.
Supports: Google News, RSS feeds (configurable via .env)

Usage:
    from src.data_engine.pipelines.news_pipeline import NewsPipeline
    pipeline = NewsPipeline()
    pipeline.run(symbols=["AAPL", "GOOGL"])
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from polars import DataFrame, concat

from src.config import settings
from src.data_engine.scrapers import GoogleNewsScraper, RSSFeedScraper
from src.data_engine.storage import StorageInterface
from src.utils import get_logger

# Import sentiment analyzers at module level for extensibility
# These are used by tests for mocking
try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    SentimentIntensityAnalyzer = None

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger("data_engine.pipelines.news")


# =============================================================================
# SENTIMENT ANALYZERS
# =============================================================================

class TextBlobSentimentAnalyzer:
    """
    Sentiment analyzer using TextBlob.

    Uses TextBlob's polarity score (-1 to 1).
    """

    def analyze(self, text: str) -> float:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Polarity score (-1 negative to 1 positive)
        """
        try:
            if TextBlob is None:
                from textblob import TextBlob

            blob = TextBlob(text)
            return blob.sentiment.polarity
        except ImportError:
            log.warning("TextBlob not installed, using 0.0 sentiment")
            return 0.0
        except Exception as e:
            log.debug(f"Sentiment analysis error: {e}")
            return 0.0


class VADERSentimentAnalyzer:
    """
    Sentiment analyzer using VADER.

    Optimized for social media and news text.
    """

    def analyze(self, text: str) -> float:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Compound score (-1 to 1)
        """
        try:
            if SentimentIntensityAnalyzer is None:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

            analyzer = SentimentIntensityAnalyzer()
            scores = analyzer.polarity_scores(text)
            return scores["compound"]
        except ImportError:
            log.warning("VADER not installed, using 0.0 sentiment")
            return 0.0
        except Exception as e:
            log.debug(f"Sentiment analysis error: {e}")
            return 0.0


class LlamaSentimentAnalyzer:
    """
    Sentiment analyzer using Llama 3.1 via Ollama + LangChain.

    Uses ChatOllama to analyze financial news sentiment with specialized
    prompts for financial context. Falls back to textblob/vader if Ollama
    is not available.

    Usage:
        analyzer = LlamaSentimentAnalyzer()
        score = analyzer.analyze("AAPL shares surge on strong earnings")
    """

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
    ) -> None:
        """
        Initialize the Llama sentiment analyzer.

        Args:
            model: Ollama model name (defaults to settings.ollama_model)
            host: Ollama host URL (defaults to settings.ollama_host)
        """
        self._model = model or settings.ollama_model
        self._host = host or settings.ollama_host
        self._llm = None
        self._initialized = False
        self._init_error: str | None = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize the Ollama connection."""
        try:
            from langchain_ollama import ChatOllama

            self._llm = ChatOllama(
                model=self._model,
                base_url=self._host,
                temperature=0.0,
                timeout=30,
            )
            self._initialized = True
            log.info(f"LlamaSentimentAnalyzer initialized (model={self._model}, host={self._host})")
        except ImportError:
            self._init_error = "langchain_ollama not installed"
            log.warning(f"LlamaSentimentAnalyzer: {self._init_error}")
        except Exception as e:
            self._init_error = str(e)
            log.warning(f"LlamaSentimentAnalyzer init failed: {e}")

    def analyze(self, text: str) -> float:
        """
        Analyze sentiment of text using Llama 3.1.

        Args:
            text: Text to analyze (financial news title/article)

        Returns:
            Sentiment score (-1 negative to 1 positive)
        """
        # Fallback if not initialized
        if not self._initialized or self._llm is None:
            log.debug(f"Llama not available, using fallback: {self._init_error}")
            return self._get_fallback_sentiment(text)

        try:
            prompt = self._build_prompt(text)
            response = self._llm.invoke(prompt)
            score = self._parse_response(response)

            log.debug(f"Llama sentiment for '{text[:50]}...': {score}")
            return score

        except Exception as e:
            log.warning(f"Llama sentiment analysis failed: {e}")
            return self._get_fallback_sentiment(text)

    def _build_prompt(self, text: str) -> str:
        """
        Build the prompt for sentiment analysis.

        Args:
            text: Text to analyze

        Returns:
            Formatted prompt string
        """
        return f"""You are a financial sentiment analyzer. Analyze the following financial news headline and return a sentiment score as a JSON object.

Rules:
- Return ONLY a JSON object with a single key "score" with value between -1.0 (very negative) and 1.0 (very positive)
- Consider financial context: "surge", "bullish", "profit" are positive; "plunge", "bearish", "loss" are negative
- Neutral news (earnings reports, announcements) should score near 0
- Return ONLY the JSON, no other text

Headline: "{text}"

Response:"""

    def _parse_response(self, response) -> float:
        """
        Parse the LLM response to extract sentiment score.

        Args:
            response: LLM response object

        Returns:
            Sentiment score between -1 and 1
        """
        try:
            # Try to get content from various response formats
            content = ""
            if hasattr(response, "content"):
                content = response.content
            elif isinstance(response, str):
                content = response

            # Extract JSON from response
            import re
            import json

            # Look for JSON object in response
            json_match = re.search(r'\{[^}]*"score"[^}]*\}', content, re.IGNORECASE)
            if json_match:
                data = json.loads(json_match.group())
                score = float(data.get("score", 0.0))
                # Clamp to valid range
                return max(-1.0, min(1.0, score))

            # Try to parse as direct float
            content_clean = content.strip().strip('"').strip("'")
            score = float(content_clean)
            return max(-1.0, min(1.0, score))

        except (ValueError, json.JSONDecodeError) as e:
            log.debug(f"Failed to parse LLM response: {e}")
            return 0.0

    def _get_fallback_sentiment(self, text: str) -> float:
        """
        Get sentiment using fallback analyzer.

        Args:
            text: Text to analyze

        Returns:
            Sentiment score from fallback
        """
        fallback = settings.sentiment_fallback.lower()

        if fallback == "vader":
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                analyzer = SentimentIntensityAnalyzer()
                scores = analyzer.polarity_scores(text)
                return scores["compound"]
            except ImportError:
                log.warning("VADER not installed, using 0.0 sentiment")
                return 0.0
        else:
            # Default to textblob
            try:
                from textblob import TextBlob
                blob = TextBlob(text)
                return blob.sentiment.polarity
            except ImportError:
                return 0.0

    @property
    def is_available(self) -> bool:
        """Check if Llama analyzer is available."""
        return self._initialized and self._llm is not None


def get_sentiment_analyzer() -> TextBlobSentimentAnalyzer | VADERSentimentAnalyzer | LlamaSentimentAnalyzer:
    """
    Get sentiment analyzer based on settings.

    Returns:
        Sentiment analyzer instance (LlamaSentimentAnalyzer, VADERSentimentAnalyzer, or TextBlobSentimentAnalyzer)
    """
    provider = settings.sentiment_provider.lower()

    if provider == "llama":
        # Try Llama, fall back if not available
        try:
            analyzer = LlamaSentimentAnalyzer()
            if analyzer.is_available:
                return analyzer
            else:
                log.warning(f"Llama not available ({analyzer._init_error}), using fallback: {settings.sentiment_fallback}")
        except Exception as e:
            log.warning(f"Failed to initialize LlamaSentimentAnalyzer: {e}")

        # Fallback to configured provider
        fallback = settings.sentiment_fallback.lower()
        if fallback == "vader":
            return VADERSentimentAnalyzer()
        return TextBlobSentimentAnalyzer()

    elif provider == "vader":
        return VADERSentimentAnalyzer()
    else:
        # Default to TextBlob
        return TextBlobSentimentAnalyzer()


# =============================================================================
# NEWS PIPELINE
# =============================================================================

class NewsPipeline:
    """
    ETL pipeline for fetching and processing financial news.

    Responsibilities:
    - Fetch news from configured sources (Google News, RSS)
    - Perform sentiment analysis on headlines
    - Deduplicate articles by URL
    - Sort by timestamp (newest first)
    - Save to processed news directory as Parquet

    Usage:
        pipeline = NewsPipeline()
        df = pipeline.run(symbols=["AAPL"])
    """

    def __init__(
        self,
        symbols: list[str] | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """
        Initialize the news pipeline.

        Args:
            symbols: List of stock ticker symbols to fetch news for.
                     Defaults to settings.tracked_symbols.
            output_dir: Directory to save processed news files.
                       Defaults to data processed directory.
        """
        self.symbols = symbols or settings.tracked_symbols
        self.output_dir = output_dir or settings.data_processed_dir / "news"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize scrapers
        self._google_scraper = GoogleNewsScraper()
        self._rss_scraper = RSSFeedScraper()

        # Initialize sentiment analyzer
        self._sentiment_analyzer = get_sentiment_analyzer()

        # Initialize storage
        self._storage = StorageInterface()

        log.info(f"NewsPipeline initialized for {len(self.symbols)} symbols")

    def fetch(
        self,
        symbol: str,
        days: int = 7,
    ) -> DataFrame:
        """
        Fetch news for a single symbol from all configured sources.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical news to fetch

        Returns:
            Polars DataFrame with columns: title, source, timestamp, url, symbol, sentiment_score
        """
        log.info(f"Fetching news for {symbol} ({days} days)")

        all_articles: list[dict] = []

        # Fetch from Google News
        try:
            google_articles = self._google_scraper.fetch(symbol, days=days)
            for article in google_articles:
                all_articles.append({
                    "title": article.title,
                    "source": article.source,
                    "timestamp": article.timestamp,
                    "url": article.url,
                    "symbol": symbol,
                })
        except Exception as e:
            log.warning(f"Google News fetch failed for {symbol}: {e}")

        # Fetch from RSS feeds if configured
        rss_feeds = self._get_rss_feeds_for_symbol(symbol)
        try:
            rss_articles = self._rss_scraper.fetch_multiple(rss_feeds)
            for article in rss_articles:
                all_articles.append({
                    "title": article.title,
                    "source": article.source,
                    "timestamp": article.timestamp,
                    "url": article.url,
                    "symbol": symbol,
                })
        except Exception as e:
            log.warning(f"RSS fetch failed for {symbol}: {e}")

        if not all_articles:
            log.warning(f"No articles fetched for {symbol}")
            return DataFrame()

        # Create DataFrame
        df = DataFrame(all_articles)
        log.info(f"Fetched {len(df)} articles for {symbol}")

        return df

    def _get_rss_feeds_for_symbol(self, symbol: str) -> list[str]:
        """
        Get RSS feed URLs for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            List of RSS feed URLs
        """
        # Default financial news feeds (can be extended via settings)
        default_feeds = [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.aol.com/aol/finance",
        ]

        # Could add symbol-specific feeds in future
        return default_feeds

    def fetch_all(self, days: int = 7) -> DataFrame:
        """
        Fetch news for all configured symbols.

        Args:
            days: Number of days of historical news to fetch

        Returns:
            Combined DataFrame with all symbols
        """
        log.info(f"Fetching news for all symbols: {self.symbols}")

        dfs: list[DataFrame] = []
        for symbol in self.symbols:
            try:
                df = self.fetch(symbol, days=days)
                if not df.is_empty():
                    dfs.append(df)
            except Exception as e:
                log.error(f"Failed to fetch news for {symbol}: {e}")

        if not dfs:
            log.warning("No news fetched for any symbol")
            return DataFrame()

        combined = concat(dfs)
        log.info(f"Total articles before processing: {len(combined)}")

        return combined

    def analyze_sentiment(self, df: DataFrame) -> DataFrame:
        """
        Analyze sentiment of news articles.

        Args:
            df: DataFrame with news articles

        Returns:
            DataFrame with sentiment_score column added
        """
        if df.is_empty():
            return df

        log.info("Analyzing sentiment")

        # Calculate sentiment for each title
        sentiments: list[float] = []
        for title in df.get_column("title").to_list():
            score = self._sentiment_analyzer.analyze(title)
            sentiments.append(score)

        df = df.with_columns([
            ("sentiment_score" if "sentiment_score" not in df.columns else "sentiment_score").alias("sentiment_score"),
        ])

        df = df.with_columns([
            sentiments,
        ])

        log.info(f"Added sentiment scores (method: {settings.sentiment_provider})")

        return df

    def deduplicate(self, df: DataFrame) -> DataFrame:
        """
        Remove duplicate articles by URL.

        Args:
            df: DataFrame with news articles

        Returns:
            DataFrame with duplicates removed
        """
        if df.is_empty():
            return df

        original_count = len(df)

        # Remove duplicates by URL
        df = df.unique(subset=["url"])

        removed = original_count - len(df)
        if removed > 0:
            log.info(f"Removed {removed} duplicate articles")

        return df

    def sort_by_timestamp(self, df: DataFrame) -> DataFrame:
        """
        Sort articles by timestamp (newest first).

        Args:
            df: DataFrame with news articles

        Returns:
            DataFrame sorted by timestamp descending
        """
        if df.is_empty():
            return df

        df = df.sort("timestamp", descending=True)

        return df

    def save(self, df: DataFrame, filename: str | None = None) -> Path:
        """
        Save processed DataFrame to Parquet file.

        Args:
            df: DataFrame to save
            filename: Optional filename (defaults to news_data.parquet)

        Returns:
            Path to saved file
        """
        if df.is_empty():
            raise ValueError("Cannot save empty DataFrame")

        filepath = self.output_dir / (filename or "news_data.parquet")
        df.write_parquet(filepath)
        log.info(f"Saved to {filepath}")
        return filepath

    def load(self, filename: str | None = None) -> DataFrame:
        """
        Load saved news data from Parquet file.

        Args:
            filename: Name of the file to load

        Returns:
            DataFrame with news data
        """
        filepath = self.output_dir / (filename or "news_data.parquet")

        if not filepath.exists():
            log.warning(f"News data file not found: {filepath}")
            return DataFrame()

        df = DataFrame.read_parquet(filepath)
        log.info(f"Loaded {len(df)} articles from {filepath}")

        return df

    def run(self, days: int = 7) -> DataFrame:
        """
        Execute full pipeline: fetch, analyze, deduplicate, sort, save.

        Args:
            days: Number of days of historical news to fetch

        Returns:
            Combined DataFrame with all symbols and sentiment
        """
        log.info("Starting news pipeline")

        # Fetch all news
        df = self.fetch_all(days=days)

        if df.is_empty():
            log.warning("No news to process")
            return df

        # Process: deduplicate, sort, analyze
        df = self.deduplicate(df)
        df = self.sort_by_timestamp(df)
        df = self.analyze_sentiment(df)

        # Save
        self.save(df)

        log.info(f"Pipeline complete: {len(df)} articles processed")
        return df


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main() -> None:
    """CLI entry point for pipeline."""
    pipeline = NewsPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()