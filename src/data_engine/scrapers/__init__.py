"""Data Scrapers - Web scraping modules for external data sources."""

from __future__ import annotations

from .google_news import GoogleNewsScraper, NewsArticle
from .rss import RSSFeedScraper, RSSArticle

__all__ = [
    "GoogleNewsScraper",
    "NewsArticle",
    "RSSFeedScraper",
    "RSSArticle",
]