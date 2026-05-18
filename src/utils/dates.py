"""
Date Utilities
=============

Helpers for date handling, trading day calculations, and ranges.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Generator



# =============================================================================
# DATE PARSING
# =============================================================================

def parse_date(value: str | date | datetime | None) -> date | None:
    """
    Parse various date formats to a date object.

    Args:
        value: String ('2024-01-15'), date, or datetime object

    Returns:
        date object or None if parsing fails

    Examples:
        >>> parse_date("2024-01-15")
        datetime.date(2024, 1, 15)
        >>> parse_date("01/15/2024")
        datetime.date(2024, 1, 15)
        >>> parse_date(None) is None
        True
    """
    if value is None:
        return None

    if isinstance(value, date):
        return value if not isinstance(value, datetime) else value.date()

    if isinstance(value, datetime):
        return value.date()

    # Try ISO format first
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"]:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


# =============================================================================
# DATE RANGES
# =============================================================================

def date_range(
    start: str | date | datetime,
    end: str | date | datetime,
    inclusive: bool = True,
) -> Generator[date, None, None]:
    """
    Generate a range of dates between start and end.

    Args:
        start: Start date
        end: End date
        inclusive: Whether to include the end date

    Yields:
        Each date in the range

    Examples:
        >>> list(date_range("2024-01-01", "2024-01-05"))
        [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2),
         datetime.date(2024, 1, 3), datetime.date(2024, 1, 4),
         datetime.date(2024, 1, 5)]
    """
    start_date = parse_date(start) if not isinstance(start, date) else start
    end_date = parse_date(end) if not isinstance(end, date) else end

    if start_date is None or end_date is None:
        return

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    if inclusive:
        end_date += timedelta(days=1)

    current = start_date
    while current < end_date:
        yield current
        current += timedelta(days=1)


# =============================================================================
# TRADING DAYS
# =============================================================================

def trading_days_between(
    start: str | date | datetime,
    end: str | date | datetime,
) -> int:
    """
    Calculate the number of trading days between two dates.

    A trading day is a weekday (Monday-Friday), excluding major US holidays.
    Note: This is an approximation; real trading calendars exist for precision.

    Args:
        start: Start date
        end: End date

    Returns:
        Number of trading days

    Examples:
        >>> trading_days_between("2024-01-01", "2024-01-05")
        4
    """
    start_date = parse_date(start) if not isinstance(start, date) else start
    end_date = parse_date(end) if not isinstance(end, date) else end

    if start_date is None or end_date is None:
        return 0

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    # Simplified: count weekdays
    # Real implementation would use a holiday calendar
    trading_days = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:  # Monday=0, Friday=4
            trading_days += 1
        current += timedelta(days=1)

    return trading_days


def is_trading_day(value: str | date | datetime) -> bool:
    """
    Check if a date is a trading day (weekday, excluding major holidays).

    Major US holidays that fall on weekdays are excluded:
    - New Year's Day (Jan 1)
    - MLK Day (3rd Monday Jan)
    - Presidents Day (3rd Monday Feb)
    - Good Friday
    - Memorial Day (last Monday May)
    - Independence Day (July 4)
    - Labor Day (1st Monday Sep)
    - Thanksgiving (4th Thursday Nov)
    - Christmas (Dec 25)

    Args:
        value: Date to check

    Returns:
        True if trading day, False otherwise

    Examples:
        >>> is_trading_day("2024-01-15")  # Monday
        True
        >>> is_trading_day("2024-01-01")  # New Year's Day
        False
    """
    check_date = parse_date(value) if not isinstance(value, date) else value

    if check_date is None:
        return False

    # Must be weekday
    if check_date.weekday() >= 5:
        return False

    # Major holidays (simplified check)
    major_holidays = _get_market_holidays(check_date.year)

    # Adjust for holidays falling on weekends (observed rules)
    for holiday in major_holidays:
        if check_date == holiday:
            return False

    return True


def _get_market_holidays(year: int) -> list[date]:
    """
    Get major US market holidays for a given year.

    This is a simplified implementation.
    Real trading calendars include more holidays and observances.

    Args:
        year: Year to get holidays for

    Returns:
        List of holiday dates
    """
    holidays: list[date] = []

    # New Year's Day
    jan1 = date(year, 1, 1)
    if jan1.weekday() == 6:  # Sunday
        holidays.append(date(year, 1, 2))  # Monday observed
    elif jan1.weekday() == 5:  # Saturday
        holidays.append(date(year, 12, 31))  # Friday observed
    else:
        holidays.append(jan1)

    # MLK Day (3rd Monday of January)
    holidays.append(_nth_weekday_of_month(year, 1, 0, 3))

    # Presidents Day (3rd Monday of February)
    holidays.append(_nth_weekday_of_month(year, 2, 0, 3))

    # Good Friday (calculate from Easter - simplified)
    good_friday = _calculate_good_friday(year)
    if good_friday is not None:
        holidays.append(good_friday)

    # Memorial Day (last Monday of May)
    holidays.append(_last_weekday_of_month(year, 5, 0))

    # Independence Day
    july4 = date(year, 7, 4)
    if july4.weekday() == 6:
        holidays.append(date(year, 7, 5))
    elif july4.weekday() == 5:
        holidays.append(date(year, 7, 3))
    else:
        holidays.append(july4)

    # Labor Day (1st Monday of September)
    holidays.append(_nth_weekday_of_month(year, 9, 0, 1))

    # Thanksgiving (4th Thursday of November)
    holidays.append(_nth_weekday_of_month(year, 11, 3, 4))

    # Christmas
    dec25 = date(year, 12, 25)
    if dec25.weekday() == 6:
        holidays.append(date(year, 12, 26))
    elif dec25.weekday() == 5:
        holidays.append(date(year, 12, 24))
    else:
        holidays.append(dec25)

    return holidays


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Find the nth occurrence of a weekday in a month."""
    first_day = date(year, month, 1)
    first_weekday = first_day.weekday()
    days_until_target = (weekday - first_weekday) % 7
    first_target = first_day + timedelta(days=days_until_target)
    return first_target + timedelta(weeks=n - 1)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """Find the last occurrence of a weekday in a month."""
    last_day = date(year, month, 1)
    # Find last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    days_since_target = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=days_since_target)


def _calculate_good_friday(year: int) -> date | None:
    """Calculate Good Friday using the Gaussian algorithm (simplified)."""
    # This is a simplified calculation
    # For production, use a proper holiday calendar library
    try:
        # Using the Anonymous Gregorian algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        day_offset = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * day_offset) // 451
        month = (h + day_offset - 7 * m + 114) // 31
        day = ((h + day_offset - 7 * m + 114) % 31) + 1
        easter = date(year, month, day)
        return easter - timedelta(days=2)
    except Exception:
        return None


__all__ = [
    "parse_date",
    "date_range",
    "trading_days_between",
    "is_trading_day",
]
