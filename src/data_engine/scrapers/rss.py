"""
RSS Feed Scraper - RSS/Atom Feed Parsing
=======================================

Parses RSS and Atom feeds for news aggregation.
Supports multiple configurable feed URLs.

Usage:
    scraper = RSSFeedScraper()
    articles = scraper.fetch("https://feeds.bloomberg.com/markets/news.rss")
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from dataclasses import dataclass
from urllib.parse import urlparse

import feedparser

from src.config import settings
from src.utils import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger("data_engine.scrapers.rss")


@dataclass
class RSSArticle:
    """Represents an article from an RSS/Atom feed."""

    title: str
    source: str
    timestamp: datetime
    url: str


class RSSFeedScraper:
    """
    Parser for RSS and Atom feeds.

    Parses RSS 2.0 and Atom feeds to extract news articles.
    Supports multiple configurable feed URLs.

    Usage:
        scraper = RSSFeedScraper()
        articles = scraper.fetch("https://feeds.bloomberg.com/markets/news.rss")
    """

    def __init__(
        self,
        timeout: int = 30,
    ) -> None:
        """
        Initialize the RSS feed scraper.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

        log.debug(f"RSSFeedScraper initialized (timeout={timeout})")

    def fetch(
        self,
        feed_url: str,
        max_entries: int = 20,
    ) -> list[RSSArticle]:
        """
        Fetch articles from an RSS/Atom feed.

        Args:
            feed_url: URL of the RSS or Atom feed
            max_entries: Maximum number of entries to return

        Returns:
            List of RSSArticle dataclass instances
        """
        log.info(f"Fetching RSS feed: {feed_url}")

        articles: list[RSSArticle] = []

        try:
            # Parse the feed
            feed = feedparser.parse(
                feed_url,
                timeout=self.timeout,
            )

            # Check for parse errors
            if feed.bozo:
                log.warning(f"Feed parsing issues: {feed.bozo_exception}")

            # Extract source name from URL
            parsed = urlparse(feed_url)
            source = parsed.netloc or "Unknown"

            # Extract entries
            for entry in feed.entries[:max_entries]:
                try:
                    title = entry.get("title", "")
                    if not title:
                        continue

                    # Get URL
                    url = entry.get("link", "")
                    if not url:
                        # Try to get from alternate link
                        if hasattr(entry, "links") and entry.links:
                            for link in entry.links:
                                if link.get("type", "").startswith("text/html"):
                                    url = link.get("href", "")
                                    break

                    if not url:
                        continue

                    # Get timestamp
                    timestamp = self._parse_timestamp(entry)

                    articles.append(RSSArticle(
                        title=title,
                        source=source,
                        timestamp=timestamp,
                        url=url,
                    ))

                except Exception as e:
                    log.debug(f"Error parsing entry: {e}")
                    continue

            log.info(f"Fetched {len(articles)} articles from {source}")
            return articles

        except Exception as e:
            log.error(f"Failed to fetch RSS feed {feed_url}: {e}")
            return articles

    def fetch_multiple(
        self,
        feed_urls: list[str],
        max_entries: int = 20,
    ) -> list[RSSArticle]:
        """
        Fetch articles from multiple RSS feeds.

        Args:
            feed_urls: List of RSS/Atom feed URLs
            max_entries: Maximum entries per feed

        Returns:
            Combined list of RSSArticle instances
        """
        log.info(f"Fetching {len(feed_urls)} RSS feeds")

        all_articles: list[RSSArticle] = []

        for url in feed_urls:
            articles = self.fetch(url, max_entries=max_entries)
            all_articles.extend(articles)

        log.info(f"Total articles: {len(all_articles)}")
        return all_articles

    def _parse_timestamp(self, entry: feedparser.FeedEntryParser) -> datetime:
        """
        Parse timestamp from RSS/Atom entry.

        Args:
            entry: Feed entry with possible timestamp fields

        Returns:
            Parsed datetime object
        """
        # Try multiple timestamp fields in order of preference
        timestamp_fields = ["published_parsed", "updated_parsed", "created_parsed"]

        for field in timestamp_fields:
            if hasattr(entry, field):
                value = getattr(entry, field, None)
                if value is not None:
                    try:
                        # feedparser returns time_struct
                        return datetime(
                            value.tm_year,
                            value.tm_mon,
                            value.tm_mday,
                            value.tm_hour,
                            value.tm_min,
                            value.tm_sec,
                        )
                    except (AttributeError, ValueError):
                        continue

        # Try to parse from date string
        for field in ["published", "updated", "created"]:
            if hasattr(entry, field):
                date_str = getattr(entry, field, "")
                if date_str:
                    try:
                        # Try RFC 822 format (RSS 2.0)
                        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                        pass

                    try:
                        # Try ISO 8601 format (Atom)
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

        # Default to now
        return datetime.now()


__all__ = [
    "RSSFeedScraper",
    "RSSArticle",
]