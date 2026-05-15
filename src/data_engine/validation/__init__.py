"""Data Validation - Schema validation and data cleaning functions."""

from __future__ import annotations

from .validator import (
    validate_stock_schema,
    validate_news_schema,
    validate_dataframe,
    forward_fill,
    remove_duplicates,
    remove_invalid_prices,
    remove_outliers_iqr,
    clean_stock_data,
    clean_news_data,
    generate_quality_report,
)

# Convenience aliases
validate_schema = validate_dataframe
clean_data = clean_stock_data

__all__ = [
    "validate_stock_schema",
    "validate_news_schema",
    "validate_dataframe",
    "validate_schema",  # Alias
    "forward_fill",
    "remove_duplicates",
    "remove_invalid_prices",
    "remove_outliers_iqr",
    "clean_stock_data",
    "clean_news_data",
    "clean_data",  # Alias
    "generate_quality_report",
]