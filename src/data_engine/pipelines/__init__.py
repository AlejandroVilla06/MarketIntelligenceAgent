"""Data Pipelines - ETL workflows for various data sources."""

from __future__ import annotations

from .news_pipeline import NewsPipeline
from .stock_pipeline import StockPipeline

__all__ = [
    "NewsPipeline",
    "StockPipeline",
]