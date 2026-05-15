"""
Data Validation - Schema Validation and Data Cleaning
=====================================================

Provides schema validation and data cleaning functions for
stock and news data quality assurance.

Usage:
    from src.data_engine.validation.validator import (
        validate_stock_schema,
        validate_news_schema,
        clean_stock_data,
        clean_news_data,
        generate_quality_report,
    )
"""

from __future__ import annotations

from typing import Any

import polars as pl
from polars import DataFrame

from src.config import settings
from src.utils import get_logger

log = get_logger("data_engine.validation.validator")


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

STOCK_REQUIRED_COLUMNS = {
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "symbol",
}

STOCK_COLUMN_TYPES = {
    "date": (pl.Datetime, pl.Date),
    "open": (float,),
    "high": (float,),
    "low": (float,),
    "close": (float,),
    "volume": (int,),
    "symbol": (str,),
}

NEWS_REQUIRED_COLUMNS = {
    "title",
    "source",
    "timestamp",
    "url",
    "symbol",
}

NEWS_COLUMN_TYPES = {
    "title": (str,),
    "source": (str,),
    "timestamp": (pl.Datetime, pl.Date),
    "url": (str,),
    "symbol": (str,),
}


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

def validate_stock_schema(df: DataFrame, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Validate stock data DataFrame has required columns and correct types.

    Args:
        df: DataFrame to validate
        strict: If True, fail on schema errors (log.warning otherwise)

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: list[str] = []

    if df.is_empty():
        errors.append("DataFrame is empty")
        return len(errors) == 0, errors

    # Check required columns
    columns = set(df.columns)
    missing = STOCK_REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {missing}")
        if strict:
            log.error(f"Missing required columns: {missing}")
            return False, errors

    # Check column types
    for col, expected_types in STOCK_COLUMN_TYPES.items():
        if col in df.columns:
            actual_type = df.schema[col]
            if not any(actual_type == t for t in expected_types):
                errors.append(f"Column '{col}' has wrong type: {actual_type}")
                if strict:
                    log.error(f"Column '{col}' type mismatch: {actual_type}")

    if errors and not strict:
        log.warning(f"Schema validation issues: {errors}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_news_schema(df: DataFrame, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Validate news data DataFrame has required columns and correct types.

    Args:
        df: DataFrame to validate
        strict: If True, fail on schema errors (log.warning otherwise)

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: list[str] = []

    if df.is_empty():
        errors.append("DataFrame is empty")
        return len(errors) == 0, errors

    # Check required columns
    columns = set(df.columns)
    missing = NEWS_REQUIRED_COLUMNS - columns
    if missing:
        errors.append(f"Missing required columns: {missing}")
        if strict:
            log.error(f"Missing required columns: {missing}")
            return False, errors

    # Check column types
    for col, expected_types in NEWS_COLUMN_TYPES.items():
        if col in df.columns:
            actual_type = df.schema[col]
            if not any(actual_type == t for t in expected_types):
                errors.append(f"Column '{col}' has wrong type: {actual_type}")
                if strict:
                    log.error(f"Column '{col}' type mismatch: {actual_type}")

    if errors and not strict:
        log.warning(f"Schema validation issues: {errors}")

    is_valid = len(errors) == 0
    return is_valid, errors


# =============================================================================
# DATA CLEANING
# =============================================================================

def forward_fill(df: DataFrame, columns: list[str] | None = None) -> DataFrame:
    """
    Forward fill missing values in specified columns.

    Args:
        df: DataFrame to clean
        columns: Columns to forward fill (default: all numeric columns)

    Returns:
        DataFrame with missing values filled
    """
    if df.is_empty():
        return df

    # Default to numeric columns
    if columns is None:
        columns = [col for col in df.columns if df.schema[col] in (float, int)]

    df = df.clone()

    for col in columns:
        if col in df.columns:
            df = df.with_columns([
                pl.col(col).forward_fill(),
            ])

    log.debug(f"Forward filled {len(columns)} columns")
    return df


def remove_duplicates(
    df: DataFrame,
    subset: list[str] | None = None,
) -> DataFrame:
    """
    Remove duplicate rows based on specified columns.

    Args:
        df: DataFrame to clean
        subset: Columns to consider for duplicates (default: all)

    Returns:
        DataFrame with duplicates removed
    """
    if df.is_empty():
        return df

    original_count = len(df)

    if subset is None:
        df = df.unique()
    else:
        df = df.unique(subset=subset)

    removed = original_count - len(df)
    if removed > 0:
        log.info(f"Removed {removed} duplicate rows")

    return df


def remove_invalid_prices(df: DataFrame) -> DataFrame:
    """
    Filter out rows with negative or zero prices.

    Looks for columns: open, high, low, close.

    Args:
        df: DataFrame with price columns

    Returns:
        DataFrame with only valid prices
    """
    if df.is_empty():
        return df

    original_count = len(df)

    # Filter price columns
    price_columns = ["open", "high", "low", "close"]
    for col in price_columns:
        if col in df.columns:
            df = df.filter(pl.col(col) > 0)

    removed = original_count - len(df)
    if removed > 0:
        log.info(f"Removed {removed} rows with invalid prices")

    return df


def remove_outliers_iqr(
    df: DataFrame,
    column: str = "volume",
    multiplier: float | None = None,
) -> DataFrame:
    """
    Remove outliers using IQR (Interquartile Range) method.

    Args:
        df: DataFrame with numeric column
        column: Column to check for outliers
        multiplier: IQR multiplier (default: from settings)

    Returns:
        DataFrame with outliers removed
    """
    if df.is_empty():
        return df

    if column not in df.columns:
        log.warning(f"Column '{column}' not found in DataFrame")
        return df

    # Use configured multiplier
    iqr_multiplier = multiplier or settings.validation_iqr_multiplier

    # Calculate Q1, Q3, IQR
    q1 = df.quantile(0.25, column=column)
    q3 = df.quantile(0.75, column=column)
    iqr = q3 - q1

    if iqr == 0:
        log.debug(f"IQR is 0 for {column}, skipping outlier detection")
        return df

    # Define bounds
    lower = q1 - (iqr_multiplier * iqr)
    upper = q3 + (iqr_multiplier * iqr)

    original_count = len(df)

    # Filter
    df = df.filter(
        (pl.col(column) >= lower) & (pl.col(column) <= upper)
    )

    removed = original_count - len(df)
    if removed > 0:
        log.info(f"Removed {removed} outliers from {column} (IQR method)")

    return df


def clean_stock_data(
    df: DataFrame,
    forward_fill_missing: bool | None = True,
    remove_invalid_prices_flag: bool | None = True,
    remove_outliers: bool | None = None,
) -> tuple[DataFrame, dict[str, Any]]:
    """
    Apply all cleaning operations to stock data.

    Args:
        df: Stock DataFrame
        forward_fill_missing: Apply forward fill for missing values
        remove_invalid_prices_flag: Remove rows with negative/zero prices
        remove_outliers: Remove statistical outliers using IQR

    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict)
    """
    if df.is_empty():
        return df, {"error": "empty DataFrame"}

    original_count = len(df)
    cleaning_log: dict[str, Any] = {"original_rows": original_count}

    # Forward fill
    if forward_fill_missing or (forward_fill_missing is None and settings.validation_forward_fill):
        df = forward_fill(df)
        cleaning_log["forward_fill"] = True

    # Remove invalid prices
    if remove_invalid_prices_flag:
        df = remove_invalid_prices(df)
        cleaning_log["remove_invalid_prices"] = True

    # Remove outliers
    if remove_outliers or (remove_outliers is None and settings.validation_remove_outliers):
        df = remove_outliers_iqr(df, column="volume")
        cleaning_log["remove_outliers"] = True

    cleaning_log["final_rows"] = len(df)
    cleaning_log["rows_removed"] = original_count - len(df)

    log.info(f"Stock data cleaned: {original_count} -> {len(df)} rows")

    return df, cleaning_log


def clean_news_data(df: DataFrame) -> tuple[DataFrame, dict[str, Any]]:
    """
    Apply cleaning operations to news data.

    Args:
        df: News DataFrame

    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict)
    """
    if df.is_empty():
        return df, {"error": "empty DataFrame"}

    original_count = len(df)
    cleaning_log: dict[str, Any] = {"original_rows": original_count}

    # Remove duplicates
    df = remove_duplicates(df, subset=["url"])
    cleaning_log["remove_duplicates"] = True

    cleaning_log["final_rows"] = len(df)
    cleaning_log["rows_removed"] = original_count - len(df)

    log.info(f"News data cleaned: {original_count} -> {len(df)} rows")

    return df, cleaning_log


# =============================================================================
# DATA QUALITY REPORTING
# =============================================================================

def generate_quality_report(df: DataFrame, data_type: str = "stock") -> dict[str, Any]:
    """
    Generate data quality report.

    Args:
        df: DataFrame to analyze
        data_type: Type of data ('stock' or 'news')

    Returns:
        Dictionary with quality metrics
    """
    if df.is_empty():
        return {
            "data_type": data_type,
            "rows": 0,
            "error": "empty DataFrame",
        }

    report: dict[str, Any] = {
        "data_type": data_type,
        "rows": len(df),
        "columns": list(df.columns),
        "schema": {col: str(typ) for col, typ in df.schema.items()},
    }

    # Calculate metrics for numeric columns
    numeric_cols = [col for col in df.columns if df.schema[col] in (float, int)]

    for col in numeric_cols:
        report[col] = {
            "null_count": df.column(col).null_count(),
            "null_percent": round(df.column(col).null_count() / len(df) * 100, 2),
            "min": df.column(col).min(),
            "max": df.column(col).max(),
            "mean": round(df.column(col).mean(), 2),
            "std": round(df.column(col).std(), 2) if len(df) > 1 else 0,
        }

    # Date column metrics
    if "date" in df.columns:
        dates = df.column("date")
        report["date_range"] = {
            "min": str(dates.min()),
            "max": str(dates.max()),
        }

    if "timestamp" in df.columns:
        timestamps = df.column("timestamp")
        report["timestamp_range"] = {
            "min": str(timestamps.min()),
            "max": str(timestamps.max()),
        }

    log.debug(f"Generated quality report for {data_type}: {len(df)} rows")

    return report


# =============================================================================
# CONFIGURABLE VALIDATION RULES
# =============================================================================

def validate_dataframe(
    df: DataFrame,
    data_type: str = "stock",
    strict: bool | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Perform full validation: schema check + quality report.

    Args:
        df: DataFrame to validate
        data_type: Type of data ('stock' or 'news')
        strict: Use strict mode (default: from settings)

    Returns:
        Tuple of (is_valid, validation_report dict)
    """
    if df.is_empty():
        return False, {"error": "empty DataFrame"}

    # Use configurable strict mode
    strict_mode = strict if strict is not None else settings.validation_strict_mode

    # Schema validation
    if data_type == "stock":
        is_valid, errors = validate_stock_schema(df, strict=strict_mode)
    else:
        is_valid, errors = validate_news_schema(df, strict=strict_mode)

    # Generate quality report
    quality_report = generate_quality_report(df, data_type=data_type)

    validation_report = {
        "is_valid": is_valid,
        "schema_errors": errors,
        "quality_report": quality_report,
        "strict_mode": strict_mode,
    }

    return is_valid, validation_report


__all__ = [
    "validate_stock_schema",
    "validate_news_schema",
    "forward_fill",
    "remove_duplicates",
    "remove_invalid_prices",
    "remove_outliers_iqr",
    "clean_stock_data",
    "clean_news_data",
    "generate_quality_report",
    "validate_dataframe",
]