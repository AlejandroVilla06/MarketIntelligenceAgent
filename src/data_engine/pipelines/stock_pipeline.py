"""
Stock Data Pipeline
===================

Fetches stock data from multiple sources (yfinance, Alpha Vantage, Polygon.io)
and processes with Polars.
Supports: AAPL, GOOGL, NVDA, MSFT, AMZN (configurable via .env)

Features:
- Multi-source support with automatic fallback
- Source selection via configuration
- Backward compatible with existing yfinance-only setup
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol

import yfinance as yf
from polars import DataFrame, col, concat, lit

from src.config import settings
from src.utils import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger("data_engine.pipelines.stock")


# =============================================================================
# DATA SOURCE PROTOCOL
# =============================================================================

class DataSource(Protocol):
    """
    Protocol defining the interface for stock data sources.

    Any class implementing this protocol can be used as a data source
    in the StockPipeline. All sources must implement the fetch method.

    Usage:
        class MyDataSource:
            def fetch(self, symbol: str, days: int) -> DataFrame:
                ...
    """

    def fetch(self, symbol: str, days: int, interval: str = "1d") -> DataFrame:
        """
        Fetch historical stock data for a given symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical data
            interval: Data interval ("1d", "1h", "5m", etc.)

        Returns:
            Polars DataFrame with columns: date, open, high, low, close, volume, symbol
        """
        ...


# =============================================================================
# CONCRETE DATA SOURCE IMPLEMENTATIONS
# =============================================================================

class YFinanceSource:
    """
    Stock data source using Yahoo Finance (yfinance).

    Default source for historical stock data. No API key required.

    Usage:
        source = YFinanceSource()
        df = source.fetch("AAPL", days=365)
    """

    def __init__(self) -> None:
        """Initialize YFinance source."""
        log.debug("Initialized YFinance source")

    def fetch(self, symbol: str, days: int = 365, interval: str = "1d") -> DataFrame:
        """
        Fetch historical data from Yahoo Finance.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical data
            interval: Data interval ("1d", "1h", "5m", etc.)

        Returns:
            Polars DataFrame with columns: date, open, high, low, close, volume, symbol
        """
        log.info(f"YFinance: Fetching {symbol} ({days} days, {interval})")

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d", interval=interval)

        if hist.empty:
            log.warning(f"YFinance: No data returned for {symbol}")
            return DataFrame()

        df = DataFrame(hist.reset_index())
        df = df.with_columns(
            col("Date").alias("date"),
            col("Open").alias("open"),
            col("High").alias("high"),
            col("Low").alias("low"),
            col("Close").alias("close"),
            col("Volume").alias("volume"),
        ).select(["date", "open", "high", "low", "close", "volume"])

        df = df.with_columns(
            col("date").str.to_datetime(),
            col("open").cast(float),
            col("high").cast(float),
            col("low").cast(float),
            col("close").cast(float),
            col("volume").cast(int),
            lit(symbol).alias("symbol"),
        )

        log.info(f"YFinance: Fetched {len(df)} rows for {symbol}")
        return df


class AlphaVantageSource:
    """
    Stock data source using Alpha Vantage API.

    Requires API key (set ALPHA_VANTAGE_API_KEY in .env).
    Provides free tier with 25 requests/day.

    Usage:
        source = AlphaVantageSource()
        df = source.fetch("IBM", days=100)
    """

    def __init__(self) -> None:
        """Initialize Alpha Vantage source."""
        self._api_key = settings.alpha_vantage_api_key

        if not self._api_key:
            log.warning("AlphaVantage: No API key configured (ALPHA_VANTAGE_API_KEY)")
        else:
            log.debug("Initialized Alpha Vantage source")

    def fetch(self, symbol: str, days: int = 365, interval: str = "1d") -> DataFrame:
        """
        Fetch historical data from Alpha Vantage API.

        Args:
            symbol: Stock ticker symbol (e.g., "IBM")
            days: Number of days of historical data (max 100 for free tier)
            interval: Data interval - maps to Alpha Vantage output size

        Returns:
            Polars DataFrame with columns: date, open, high, low, close, volume, symbol
        """
        if not self._api_key:
            log.error("AlphaVantage: No API key available")
            return DataFrame()

        # Map interval to Alpha Vantage parameters
        if interval == "1d":
            function = "TIME_SERIES_DAILY"
            output_size = "full" if days > 100 else "compact"
        elif interval == "1h":
            function = "TIME_SERIES_INTRADAY"
            output_size = "full"
        else:
            log.warning(f"AlphaVantage: Unsupported interval '{interval}', using daily")
            function = "TIME_SERIES_DAILY"
            output_size = "compact"

        log.info(f"AlphaVantage: Fetching {symbol} ({days} days, {interval})")

        try:
            import requests

            url = "https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol,
                "outputsize": output_size,
                "apikey": self._api_key,
                "datatype": "json",
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Parse response
            if "Error Message" in data:
                log.error(f"AlphaVantage: API error - {data['Error Message']}")
                return DataFrame()
            if "Note" in data:
                log.warning(f"AlphaVantage: Rate limit - {data['Note']}")
                return DataFrame()

            # Extract time series
            time_series_key = None
            for key in data:
                if "Time Series" in key:
                    time_series_key = key
                    break

            if not time_series_key:
                log.error(f"AlphaVantage: No time series data for {symbol}")
                return DataFrame()

            time_series = data[time_series_key]

            # Convert to records
            records = []
            for date_str, values in time_series.items():
                records.append({
                    "date": datetime.strptime(date_str, "%Y-%m-%d"),
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0)),
                    "symbol": symbol,
                })

            # Limit to requested days
            records = records[:days]

            df = DataFrame(records)
            log.info(f"AlphaVantage: Fetched {len(df)} rows for {symbol}")
            return df

        except ImportError:
            log.error("AlphaVantage: 'requests' library not installed")
            return DataFrame()
        except Exception as e:
            log.error(f"AlphaVantage: Failed to fetch {symbol}: {e}")
            return DataFrame()


class PolygonIOStockSource:
    """
    Stock data source using Polygon.io API.

    Requires API key (set POLYGON_API_KEY in .env).
    Provides real-time and historical data.

    Usage:
        source = PolygonIOStockSource()
        df = source.fetch("AAPL", days=365)
    """

    def __init__(self) -> None:
        """Initialize Polygon.io source."""
        self._api_key = settings.polygon_api_key

        if not self._api_key:
            log.warning("Polygon.io: No API key configured (POLYGON_API_KEY)")
        else:
            log.debug("Initialized Polygon.io source")

    def fetch(self, symbol: str, days: int = 365, interval: str = "1d") -> DataFrame:
        """
        Fetch historical data from Polygon.io API.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical data
            interval: Data interval ("1d", "1h", "5m", etc.)

        Returns:
            Polars DataFrame with columns: date, open, high, low, close, volume, symbol
        """
        if not self._api_key:
            log.error("Polygon.io: No API key available")
            return DataFrame()

        log.info(f"Polygon.io: Fetching {symbol} ({days} days, {interval})")

        try:
            import requests
            from datetime import datetime, timedelta

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Map interval to Polygon multiplier and timespan
            multiplier, timespan = self._map_interval(interval)

            # Build API URL
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

            params = {
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000,
                "apiKey": self._api_key,
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "results" not in data or not data["results"]:
                log.warning(f"Polygon.io: No data returned for {symbol}")
                return DataFrame()

            # Convert to records
            records = []
            for item in data["results"]:
                records.append({
                    "date": datetime.fromtimestamp(item["t"] / 1000),
                    "open": item.get("o", 0),
                    "high": item.get("h", 0),
                    "low": item.get("l", 0),
                    "close": item.get("c", 0),
                    "volume": item.get("v", 0),
                    "symbol": symbol,
                })

            df = DataFrame(records)
            log.info(f"Polygon.io: Fetched {len(df)} rows for {symbol}")
            return df

        except ImportError:
            log.error("Polygon.io: 'requests' library not installed")
            return DataFrame()
        except Exception as e:
            log.error(f"Polygon.io: Failed to fetch {symbol}: {e}")
            return DataFrame()

    def _map_interval(self, interval: str) -> tuple[int, str]:
        """
        Map standard interval to Polygon.io multiplier and timespan.

        Args:
            interval: Standard interval string

        Returns:
            Tuple of (multiplier, timespan)
        """
        mapping = {
            "1d": (1, "day"),
            "1h": (1, "hour"),
            "5m": (5, "minute"),
            "15m": (15, "minute"),
            "30m": (30, "minute"),
            "1m": (1, "minute"),
        }
        return mapping.get(interval, (1, "day"))


# =============================================================================
# SOURCE REGISTRY AND FACTORY
# =============================================================================

# Registry mapping source names to classes
_SOURCE_REGISTRY: dict[str, type[DataSource]] = {
    "yfinance": YFinanceSource,
    "alphavantage": AlphaVantageSource,
    "polygon": PolygonIOStockSource,
}


def get_data_sources(
    primary_source: str | None = None,
    fallback_sources: list[str] | None = None,
) -> list[DataSource]:
    """
    Create a list of data source instances based on configuration.

    Args:
        primary_source: Primary data source name (defaults to settings.stock_data_source)
        fallback_sources: List of fallback source names

    Returns:
        List of DataSource instances in priority order
    """
    primary = primary_source or settings.stock_data_source
    sources: list[DataSource] = []

    # Try primary source first
    if primary.lower() in _SOURCE_REGISTRY:
        source_class = _SOURCE_REGISTRY[primary.lower()]
        try:
            instance = source_class()
            # Check if source is actually available (has API key, etc.)
            if _is_source_available(instance, primary.lower()):
                sources.append(instance)
                log.info(f"Primary source enabled: {primary}")
            else:
                log.warning(f"Primary source {primary} not available, trying fallbacks")
        except Exception as e:
            log.warning(f"Failed to initialize primary source {primary}: {e}")
    else:
        log.warning(f"Unknown primary source: {primary}, using default")

    # Try fallback sources
    fallback_list = fallback_sources or ["yfinance", "alphavantage", "polygon"]
    for source_name in fallback_list:
        if source_name.lower() not in _SOURCE_REGISTRY:
            log.warning(f"Unknown fallback source: {source_name}")
            continue

        # Skip if already added as primary
        if source_name.lower() == primary.lower():
            continue

        source_class = _SOURCE_REGISTRY[source_name.lower()]
        try:
            instance = source_class()
            if _is_source_available(instance, source_name.lower()):
                sources.append(instance)
                log.info(f"Fallback source enabled: {source_name}")
        except Exception as e:
            log.debug(f"Fallback source {source_name} not available: {e}")

    # If no sources available, use yfinance as last resort (no API key needed)
    if not sources:
        log.warning("No configured sources available, using yfinance as fallback")
        sources.append(YFinanceSource())

    return sources


def _is_source_available(source: DataSource, source_name: str) -> bool:
    """
    Check if a data source is actually available (has required credentials).

    Args:
        source: DataSource instance
        source_name: Name of the source

    Returns:
        True if source can be used, False otherwise
    """
    # yfinance is always available (no API key required)
    if isinstance(source, YFinanceSource):
        return True

    # Alpha Vantage requires API key
    if isinstance(source, AlphaVantageSource):
        return bool(settings.alpha_vantage_api_key)

    # Polygon.io requires API key
    if isinstance(source, PolygonIOStockSource):
        return bool(settings.polygon_api_key)

    return True


# =============================================================================
# STOCK PIPELINE
# =============================================================================

class StockPipeline:
    """
    ETL pipeline for fetching and processing stock market data.

    Responsibilities:
    - Fetch raw data from configured sources (yfinance, Alpha Vantage, Polygon.io)
    - Implement fallback mechanism if primary source fails
    - Clean and validate data
    - Save to processed/ directory as Parquet

    Features:
    - Multi-source support with automatic fallback
    - Source selection via settings.stock_data_source
    - Backward compatible with yfinance-only configuration

    Usage:
        pipeline = StockPipeline()
        df = pipeline.fetch("AAPL", days=365)
        pipeline.run()  # Process all configured symbols
    """

    def __init__(
        self,
        symbols: list[str] | None = None,
        output_dir: Path | None = None,
        primary_source: str | None = None,
        fallback_sources: list[str] | None = None,
    ) -> None:
        """
        Initialize the stock pipeline.

        Args:
            symbols: List of stock ticker symbols to fetch.
                     Defaults to settings.tracked_symbols.
            output_dir: Directory to save processed Parquet files.
                       Defaults to settings.yfinance_cache_dir.
            primary_source: Primary data source name.
                           Defaults to settings.stock_data_source.
            fallback_sources: List of fallback source names.
                            Defaults to ["yfinance", "alphavantage", "polygon"].
        """
        self.symbols = symbols or settings.tracked_symbols
        self.output_dir = output_dir or settings.yfinance_cache_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize data sources
        self.primary_source = primary_source or settings.stock_data_source
        self.fallback_sources = fallback_sources or ["yfinance", "alphavantage", "polygon"]
        self._sources = get_data_sources(self.primary_source, self.fallback_sources)

        log.info(f"StockPipeline initialized with {len(self._sources)} source(s): {[s.__class__.__name__ for s in self._sources]}")

    def fetch(
        self,
        symbol: str,
        days: int = 365,
        interval: str = "1d",
    ) -> DataFrame:
        """
        Fetch historical data for a single symbol.

        Tries each configured source in order until one succeeds.
        Implements fallback mechanism for reliability.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical data
            interval: Data interval ("1d", "1h", "5m", etc.)

        Returns:
            Polars DataFrame with columns: date, open, high, low, close, volume, symbol
            Returns empty DataFrame if all sources fail.
        """
        log.info(f"Fetching {symbol} ({days} days, {interval})")

        for i, source in enumerate(self._sources):
            source_name = source.__class__.__name__
            try:
                log.debug(f"Attempt {i + 1}/{len(self._sources)}: {source_name}")
                df = source.fetch(symbol, days=days, interval=interval)

                if df is not None and not df.is_empty():
                    log.info(f"Successfully fetched {symbol} from {source_name}")
                    return df

                log.warning(f"{source_name} returned empty data for {symbol}, trying next source")

            except Exception as e:
                log.warning(f"{source_name} failed for {symbol}: {e}, trying next source")

        # All sources failed
        log.error(f"All sources failed for {symbol}")
        return DataFrame()

    def fetch_all(self, days: int = 365, interval: str = "1d") -> DataFrame:
        """
        Fetch data for all configured symbols.

        Args:
            days: Number of days of historical data
            interval: Data interval

        Returns:
            Combined DataFrame with all symbols
        """
        log.info(f"Fetching all symbols: {self.symbols}")

        dfs: list[DataFrame] = []
        for symbol in self.symbols:
            try:
                df = self.fetch(symbol, days=days, interval=interval)
                if not df.is_empty():
                    dfs.append(df)
            except Exception as e:
                log.error(f"Failed to fetch {symbol}: {e}")

        if not dfs:
            log.warning("No data fetched for any symbol")
            return DataFrame()

        combined = concat(dfs)
        log.info(f"Total rows: {len(combined)}")
        return combined

    def save(self, df: DataFrame, filename: str | None = None) -> Path:
        """
        Save processed DataFrame to Parquet file.

        Args:
            df: DataFrame to save
            filename: Optional filename (defaults to stock_data.parquet)

        Returns:
            Path to saved file
        """
        if df.is_empty():
            raise ValueError("Cannot save empty DataFrame")

        filepath = self.output_dir / (filename or "stock_data.parquet")
        df.write_parquet(filepath)
        log.info(f"Saved to {filepath}")
        return filepath

    def run(self, days: int = 365, interval: str = "1d") -> DataFrame:
        """
        Execute full pipeline: fetch, combine, save.

        Args:
            days: Number of days of historical data
            interval: Data interval

        Returns:
            Combined DataFrame with all symbols
        """
        log.info("Starting stock pipeline")
        df = self.fetch_all(days=days, interval=interval)

        if not df.is_empty():
            self.save(df)

        log.info("Pipeline complete")
        return df


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main() -> None:
    """CLI entry point for pipeline."""
    pipeline = StockPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()