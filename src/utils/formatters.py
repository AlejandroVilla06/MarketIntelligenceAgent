"""
Formatting Utilities
====================

Helpers for consistent data formatting across the application.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from polars import DataFrame

if TYPE_CHECKING:
    from polars import Series


# =============================================================================
# CURRENCY FORMATTING
# =============================================================================

def format_currency(
    value: float | int | None,
    symbol: str = "$",
    decimals: int = 2,
) -> str:
    """
    Format a value as currency.

    Args:
        value: Numeric value to format
        symbol: Currency symbol to prepend
        decimals: Number of decimal places

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(0.0523, symbol="€", decimals=4)
        '€0.0523'
    """
    if value is None:
        return f"{symbol}—"

    if decimals == 4:
        # For small values (e.g., forex)
        return f"{symbol}{value:,.4f}"

    return f"{symbol}{value:,.{decimals}f}"


# =============================================================================
# PERCENTAGE FORMATTING
# =============================================================================

def format_percentage(
    value: float | int | None,
    decimals: int = 2,
    include_sign: bool = True,
) -> str:
    """
    Format a value as a percentage.

    Args:
        value: Numeric value (e.g., 0.0523 for 5.23%)
        decimals: Number of decimal places
        include_sign: Whether to include + for positive values

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.0523)
        '+5.23%'
        >>> format_percentage(-0.0312, include_sign=False)
        '-3.12%'
    """
    if value is None:
        return "—%"

    formatted = f"{abs(value) * 100:.{decimals}f}%"

    if include_sign:
        if value > 0:
            return f"+{formatted}"
        elif value < 0:
            return f"-{formatted}"

    return formatted


# =============================================================================
# VOLUME FORMATTING
# =============================================================================

def format_volume(value: float | int | None) -> str:
    """
    Format a volume/value with K/M/B suffixes.

    Args:
        value: Numeric value to format

    Returns:
        Human-readable volume string

    Examples:
        >>> format_volume(1234)
        '1.23K'
        >>> format_volume(1234567)
        '1.23M'
        >>> format_volume(1234567890)
        '1.23B'
    """
    if value is None:
        return "—"

    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif abs_value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif abs_value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return str(int(value))


# =============================================================================
# TIMESTAMP FORMATTING
# =============================================================================

def format_timestamp(
    value: datetime | str | None,
    format_string: str = "%Y-%m-%d %H:%M",
    include_time: bool = True,
) -> str:
    """
    Format a datetime value.

    Args:
        value: Datetime object or ISO string
        format_string: strftime format string
        include_time: Whether to include time component

    Returns:
        Formatted timestamp string

    Examples:
        >>> format_timestamp(datetime(2024, 1, 15, 10, 30))
        '2024-01-15 10:30'
        >>> format_timestamp("2024-01-15T10:30:00", include_time=False)
        '2024-01-15'
    """
    if value is None:
        return "—"

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "Invalid date"

    if not include_time:
        format_string = "%Y-%m-%d"

    return value.strftime(format_string)


# =============================================================================
# DATAFRAME FORMATTING
# =============================================================================

def format_dataframe(
    df: DataFrame,
    max_rows: int = 10,
    max_columns: int = 8,
) -> str:
    """
    Format a Polars DataFrame as a readable string.

    Args:
        df: DataFrame to format
        max_rows: Maximum rows to display
        max_columns: Maximum columns to display

    Returns:
        Formatted string representation
    """
    if df.is_empty():
        return "Empty DataFrame"

    # Limit display
    rows = min(len(df), max_rows)
    cols = min(len(df.columns), max_columns)

    truncated = df.head(rows).select(df.columns[:cols])

    lines: list[str] = []
    lines.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append("─" * 60)

    # Header
    col_names = truncated.columns
    lines.append(" | ".join(f"{c:>15}" for c in col_names))
    lines.append("─" * 60)

    # Rows
    for row in truncated.iter_rows():
        formatted = []
        for val in row:
            if val is None:
                formatted.append("—" * 15)
            elif isinstance(val, float):
                formatted.append(f"{val:>15.4f}")
            elif isinstance(val, int):
                formatted.append(f"{val:>15,}")
            else:
                str_val = str(val)[:15]
                formatted.append(f"{str_val:>15}")
        lines.append(" | ".join(formatted))

    if len(df) > max_rows:
        lines.append(f"... ({len(df) - max_rows} more rows)")

    if len(df.columns) > max_columns:
        lines.append(f"... ({len(df.columns) - max_columns} more columns)")

    return "\n".join(lines)


# =============================================================================
# GENERIC VALUE FORMATTER
# =============================================================================

def format_value(
    value: Any,
    style: str = "auto",
) -> str:
    """
    Automatically format a value based on its type.

    Args:
        value: Value to format
        style: 'auto', 'currency', 'percentage', 'volume', 'compact'

    Returns:
        Formatted string
    """
    if value is None:
        return "—"

    if style == "auto":
        if isinstance(value, (int, float)):
            if abs(value) < 1:
                return format_percentage(value, decimals=4)
            elif abs(value) >= 1_000_000:
                return format_volume(value)
            else:
                return format_currency(value)
        else:
            return str(value)

    elif style == "currency":
        return format_currency(value)

    elif style == "percentage":
        return format_percentage(value)

    elif style == "volume":
        return format_volume(value)

    elif style == "compact":
        return format_volume(value)

    return str(value)


__all__ = [
    "format_currency",
    "format_percentage",
    "format_volume",
    "format_timestamp",
    "format_dataframe",
    "format_value",
]
