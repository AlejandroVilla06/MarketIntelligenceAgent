"""
Google News Scraper - Financial News Retrieval
=============================================

Fetches financial news from Google News using web scraping.
Handles rate limiting and parsing.

Usage:
    scraper = GoogleNewsScraper()
    articles = scraper.fetch("AAPL", days=7)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from src.config import settings
from src.utils import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger("data_engine.scrapers.google_news")


@dataclass
class NewsArticle:
    """Represents a news article from Google News."""

    title: str
    source: str
    timestamp: datetime
    url: str


class GoogleNewsScraper:
    """
    Scraper for financial news from Google News.

    Fetches news articles by querying Google News search results
    for specific stock symbols. Uses requests and BeautifulSoup.

    Usage:
        scraper = GoogleNewsScraper()
        articles = scraper.fetch("AAPL", days=7)
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the Google News scraper.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

        log.debug(f"GoogleNewsScraper initialized (timeout={timeout}, retries={max_retries})")

    def fetch(
        self,
        symbol: str,
        days: int = 7,
        max_articles: int = 20,
    ) -> list[NewsArticle]:
        """
        Fetch financial news articles for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical news to fetch
            max_articles: Maximum number of articles to return

        Returns:
            List of NewsArticle dataclass instances
        """
        log.info(f"Fetching Google News for {symbol} (days={days})")

        query = f"{symbol} stock news"
        articles: list[NewsArticle] = []

        # Calculate date range
        start_date = datetime.now() - timedelta(days=days)

        for attempt in range(self.max_retries):
            try:
                # Build Google News URL
                url = "https://www.google.com/search"
                params = {
                    "q": query,
                    "tbm": "nws",  # News
                    "tbs": f"sbd:1,cd_min:{start_date.strftime('%m/%d/%Y')},cd_max:{datetime.now().strftime('%m/%d/%Y')}",
                    "format": "any",
                }

                response = self._session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Find news articles
                for article in soup.select("div.SoaBEf"):
                    try:
                        title_elem = article.select_one("div.mCBky")
                        source_elem = article.select_one("div.CEMjEf span")
                        time_elem = article.select_one("div.UB5Wbb span")
                        link_elem = article.select_one("a")

                        if not all([title_elem, link_elem]):
                            continue

                        title = title_elem.get_text(strip=True)
                        source = source_elem.get_text(strip=True) if source_elem else "Unknown"
                        url = link_elem.get("href", "")
                        if not url.startswith("http"):
                            continue

                        # Parse timestamp
                        timestamp = self._parse_timestamp(time_elem.get_text(strip=True) if time_elem else "")

                        articles.append(NewsArticle(
                            title=title,
                            source=source,
                            timestamp=timestamp,
                            url=url,
                        ))

                        if len(articles) >= max_articles:
                            break

                    except Exception as e:
                        log.debug(f"Error parsing article: {e}")
                        continue

                log.info(f"Fetched {len(articles)} articles for {symbol}")
                return articles

            except requests.exceptions.RequestException as e:
                log.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff

        log.error(f"Failed to fetch news for {symbol} after {self.max_retries} attempts")
        return articles

    def _parse_timestamp(self, time_text: str) -> datetime:
        """
        Parse timestamp text from Google News.

        Args:
            time_text: Timestamp text (e.g., "2 hours ago", "Yesterday")

        Returns:
            Parsed datetime object
        """
        import re

        time_text = time_text.lower().strip()

        # Current time reference
        now = datetime.now()

        # Handle relative time
        if "hour" in time_text:
            match = re.search(r"(\d+)", time_text)
            if match:
                hours = int(match.group(1))
                return now - timedelta(hours=hours)

        if "minute" in time_text:
            match = re.search(r"(\d+)", time_text)
            if match:
                minutes = int(match.group(1))
                return now - timedelta(minutes=minutes)

        if "day" in time_text:
            match = re.search(r"(\d+)", time_text)
            if match:
                days = int(match.group(1))
                return now - timedelta(days=days)

        if "yesterday" in time_text:
            return now - timedelta(days=1)

        # Try to parse as date
        try:
            return datetime.strptime(time_text, "%b %d, %Y")
        except ValueError:
            pass

        try:
            return datetime.strptime(time_text, "%B %d, %Y")
        except ValueError:
            pass

        # Default to now
        return now


__all__ = [
    "GoogleNewsScraper",
    "NewsArticle",
]