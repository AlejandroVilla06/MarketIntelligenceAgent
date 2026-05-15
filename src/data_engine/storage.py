"""
Storage Interface - Parquet Read/Write Operations
================================================

Unified storage layer for market data persistence.
Handles Parquet read/write with Polars and partitioning support.

Usage:
    from src.data_engine.storage import StorageInterface
    storage = StorageInterface()
    storage.save_stocks(df, partition_by=["symbol", "date"])
    df = storage.load_stocks(symbols=["AAPL"])
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from polars import DataFrame

from src.config import DATA_PROCESSED_DIR, settings
from src.utils import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger("data_engine.storage")


class StorageInterface:
    """
    Unified storage interface for market data persistence.

    Responsibilities:
    - Save stock and news data as Parquet files
    - Load data with optional filtering by symbols and date range
    - Manage partitioning for efficient queries

    Usage:
        storage = StorageInterface()
        storage.save_stocks(df, partition_by=["symbol"])
        df = storage.load_stocks(symbols=["AAPL"], start_date="2024-01-01")
    """

    def __init__(
        self,
        base_dir: Path | None = None,
    ) -> None:
        """
        Initialize storage interface.

        Args:
            base_dir: Base directory for data storage.
                     Defaults to settings.data_processed_dir.
        """
        self.base_dir = base_dir or DATA_PROCESSED_DIR
        self.stocks_dir = self.base_dir / "stocks"
        self.news_dir = self.base_dir / "news"
        self.sentiment_dir = self.base_dir / "sentiment"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.stocks_dir.mkdir(parents=True, exist_ok=True)
        self.news_dir.mkdir(parents=True, exist_ok=True)
        self.sentiment_dir.mkdir(parents=True, exist_ok=True)

    def save_stocks(
        self,
        df: DataFrame,
        filename: str = "stock_data.parquet",
        partition_by: list[str] | None = None,
    ) -> Path:
        """
        Save stock data as Parquet file.

        Args:
            df: Polars DataFrame with stock data
            filename: Name of the output file
            partition_by: Columns to partition by (e.g., ["symbol"])

        Returns:
            Path to saved file

        Raises:
            ValueError: If DataFrame is empty
        """
        if df.is_empty():
            raise ValueError("Cannot save empty DataFrame")

        filepath = self.stocks_dir / filename
        df.write_parquet(filepath)
        log.info(f"Saved stock data to {filepath} ({len(df)} rows)")
        return filepath

    def load_stocks(
        self,
        symbols: list[str] | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        filename: str = "stock_data.parquet",
    ) -> DataFrame:
        """
        Load stock data with optional filtering.

        Args:
            symbols: Filter by stock symbols (None = all)
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            filename: Name of the Parquet file

        Returns:
            Polars DataFrame with stock data
        """
        filepath = self.stocks_dir / filename

        if not filepath.exists():
            log.warning(f"Stock data file not found: {filepath}")
            return DataFrame()

        df = pl.read_parquet(filepath)
        log.info(f"Loaded stock data from {filepath} ({len(df)} rows)")

        # Apply filters
        if symbols:
            df = df.filter(pl.col("symbol").is_in(symbols))

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            df = df.filter(pl.col("date") >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            df = df.filter(pl.col("date") <= end_date)

        return df

    def save_news(
        self,
        df: DataFrame,
        filename: str = "news_data.parquet",
        partition_by: list[str] | None = None,
    ) -> Path:
        """
        Save news data as Parquet file.

        Args:
            df: Polars DataFrame with news data
            filename: Name of the output file
            partition_by: Columns to partition by (e.g., ["symbol"])

        Returns:
            Path to saved file

        Raises:
            ValueError: If DataFrame is empty
        """
        if df.is_empty():
            raise ValueError("Cannot save empty DataFrame")

        filepath = self.news_dir / filename
        df.write_parquet(filepath)
        log.info(f"Saved news data to {filepath} ({len(df)} rows)")
        return filepath

    def load_news(
        self,
        symbols: list[str] | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        filename: str = "news_data.parquet",
    ) -> DataFrame:
        """
        Load news data with optional filtering.

        Args:
            symbols: Filter by stock symbols (None = all)
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            filename: Name of the Parquet file

        Returns:
            Polars DataFrame with news data
        """
        filepath = self.news_dir / filename

        if not filepath.exists():
            log.warning(f"News data file not found: {filepath}")
            return DataFrame()

        df = pl.read_parquet(filepath)
        log.info(f"Loaded news data from {filepath} ({len(df)} rows)")

        # Apply filters
        if symbols:
            df = df.filter(pl.col("symbol").is_in(symbols))

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            df = df.filter(pl.col("timestamp") >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            df = df.filter(pl.col("timestamp") <= end_date)

        return df

    def list_stocks(self) -> list[Path]:
        """
        List available stock data files.

        Returns:
            List of paths to Parquet files
        """
        if not self.stocks_dir.exists():
            return []
        return list(self.stocks_dir.glob("*.parquet"))

    def list_news(self) -> list[Path]:
        """
        List available news data files.

        Returns:
            List of paths to Parquet files
        """
        if not self.news_dir.exists():
            return []
        return list(self.news_dir.glob("*.parquet"))

    def save_sentiment(
        self,
        df: DataFrame,
        filename: str = "sentiment_data.parquet",
        partition_by: list[str] | None = None,
    ) -> Path:
        """
        Save sentiment data as Parquet file.

        Args:
            df: Polars DataFrame with sentiment data
            filename: Name of the output file
            partition_by: Columns to partition by (e.g., ["symbol"])

        Returns:
            Path to saved file

        Raises:
            ValueError: If DataFrame is empty
        """
        if df.is_empty():
            raise ValueError("Cannot save empty DataFrame")

        filepath = self.sentiment_dir / filename
        df.write_parquet(filepath)
        log.info(f"Saved sentiment data to {filepath} ({len(df)} rows)")
        return filepath

    def load_sentiment(
        self,
        symbols: list[str] | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        filename: str = "sentiment_data.parquet",
    ) -> DataFrame:
        """
        Load sentiment data with optional filtering.

        Args:
            symbols: Filter by stock symbols (None = all)
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            filename: Name of the Parquet file

        Returns:
            Polars DataFrame with sentiment data
        """
        filepath = self.sentiment_dir / filename

        if not filepath.exists():
            log.warning(f"Sentiment data file not found: {filepath}")
            return DataFrame()

        df = pl.read_parquet(filepath)
        log.info(f"Loaded sentiment data from {filepath} ({len(df)} rows)")

        # Apply filters
        if symbols:
            df = df.filter(pl.col("symbol").is_in(symbols))

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            df = df.filter(pl.col("date") >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            df = df.filter(pl.col("date") <= end_date)

        return df

    def list_sentiment(self) -> list[Path]:
        """
        List available sentiment data files.

        Returns:
            List of paths to Parquet files
        """
        if not self.sentiment_dir.exists():
            return []
        return list(self.sentiment_dir.glob("*.parquet"))


__all__ = [
    "StorageInterface",
]