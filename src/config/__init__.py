"""
Market Intelligence Agent - Configuration Module
=================================================

Handles environment variable loading and application settings.
Uses Pydantic for type-safe configuration management.

Usage:
    from src.config import settings
    print(settings.tracked_symbols)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# PATHS
# =============================================================================

PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.resolve()
"""Root directory of the project."""

DATA_DIR: Path = PROJECT_ROOT / "data"
"""Directory for data storage."""

DATA_RAW_DIR: Path = DATA_DIR / "raw"
"""Directory for raw data."""

DATA_PROCESSED_DIR: Path = DATA_DIR / "processed"
"""Directory for processed data."""

LOGS_DIR: Path = PROJECT_ROOT / "logs"
"""Directory for log files."""


# =============================================================================
# SETTINGS
# =============================================================================

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All values can be overridden via .env file or environment variables.
    Sensitive values (API keys) should NEVER be hardcoded.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # API Keys
    # -------------------------------------------------------------------------
    alpha_vantage_api_key: Annotated[str, Field(
        description="Alpha Vantage API key for stock data"
    )] = ""

    polygon_api_key: Annotated[str, Field(
        description="Polygon.io API key for alternative data"
    )] = ""

    openai_api_key: Annotated[str, Field(
        description="OpenAI API key for LangChain LLM"
    )] = ""

    openai_api_base: Annotated[str | None, Field(
        description="OpenAI API base URL (set this to your OpenCode Go endpoint or any OpenAI-compatible API)"
    )] = None

    anthropic_api_key: Annotated[str, Field(
        description="Anthropic API key for Claude"
    )] = ""

    newsapi_key: Annotated[str, Field(
        description="NewsAPI.org key for financial news"
    )] = ""

    # -------------------------------------------------------------------------
    # Data Source Configuration
    # -------------------------------------------------------------------------
    stock_data_source: Annotated[str, Field(
        description="Primary stock data source (yfinance, alphavantage, polygon)",
    )] = "yfinance"

    news_data_source: Annotated[str, Field(
        description="Primary news data source (google, rss, newsapi)",
    )] = "google"

    enable_stock_ingestion: Annotated[bool, Field(
        description="Enable stock data ingestion pipeline"
    )] = True

    enable_news_ingestion: Annotated[bool, Field(
        description="Enable news sentiment ingestion pipeline"
    )] = True

    # -------------------------------------------------------------------------
    # Data Validation
    # -------------------------------------------------------------------------
    validation_strict_mode: Annotated[bool, Field(
        description="Enable strict validation (fail on errors)"
    )] = False

    validation_remove_outliers: Annotated[bool, Field(
        description="Remove statistical outliers from data"
    )] = True

    validation_iqr_multiplier: Annotated[float, Field(
        description="IQR multiplier for outlier detection",
        ge=1.0,
        le=5.0,
    )] = 3.0

    validation_forward_fill: Annotated[bool, Field(
        description="Apply forward fill to missing values"
    )] = True

    # -------------------------------------------------------------------------
    # Sentiment Analysis
    # -------------------------------------------------------------------------
    sentiment_provider: Annotated[str, Field(
        description="Sentiment analysis provider (textblob, vader, llama)",
    )] = "textblob"

    ollama_host: Annotated[str, Field(
        description="Ollama host URL for Llama sentiment analysis"
    )] = "http://localhost:11434"

    ollama_model: Annotated[str, Field(
        description="Ollama model for sentiment (llama3:8b, llama3:8b-q4)"
    )] = "llama3:8b"

    sentiment_fallback: Annotated[str, Field(
        description="Fallback provider when primary fails (textblob, vader)"
    )] = "textblob"

    # -------------------------------------------------------------------------
    # Data Configuration
    # -------------------------------------------------------------------------
    tracked_symbols: Annotated[str, Field(
        description="Stock symbols to track (comma-separated)",
    )] = "AAPL,GOOGL,NVDA,MSFT,AMZN"

    data_refresh_interval: Annotated[int, Field(
        description="Data refresh interval in minutes",
        ge=1,
        le=1440,
    )] = 15

    yfinance_cache_dir: Annotated[Path, Field(
        description="yfinance cache directory"
    )] = DATA_RAW_DIR

    data_processed_dir: Annotated[Path, Field(
        description="Processed data directory"
    )] = DATA_PROCESSED_DIR

    # -------------------------------------------------------------------------
    # RSS Feeds
    # -------------------------------------------------------------------------
    rss_feed_urls: Annotated[list[str], Field(
        description="RSS feed URLs for news aggregation",
        default_factory=lambda: [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.aol.com/aol/finance",
        ]
    )]

    # -------------------------------------------------------------------------
    # Vector Database
    # -------------------------------------------------------------------------
    chromadb_persist_dir: Annotated[Path, Field(
        description="ChromaDB persistence directory"
    )] = DATA_PROCESSED_DIR / "chromadb"

    chromadb_collection_name: Annotated[str, Field(
        description="ChromaDB collection name for market memory"
    )] = "market_intelligence"

    # -------------------------------------------------------------------------
    # ML Model
    # -------------------------------------------------------------------------
    model_save_dir: Annotated[Path, Field(
        description="Directory for saved models"
    )] = PROJECT_ROOT / "src" / "ml_models" / "saved"

    training_lookback_days: Annotated[int, Field(
        description="Training data lookback period in days",
        ge=30,
        le=3650,
    )] = 365

    # -------------------------------------------------------------------------
    # ML Model Configuration - Anomaly Detection
    # -------------------------------------------------------------------------
    anomaly_n_estimators: Annotated[int, Field(
        description="Number of trees in Isolation Forest"
    )] = 100

    anomaly_contamination: Annotated[float, Field(
        description="Expected proportion of anomalies in data"
    )] = 0.1

    anomaly_max_samples: Annotated[str, Field(
        description="Max samples for Isolation Forest (auto or int)"
    )] = "auto"

    # -------------------------------------------------------------------------
    # ML Model Configuration - Trend Prediction
    # -------------------------------------------------------------------------
    trend_n_estimators: Annotated[int, Field(
        description="Number of estimators for XGBoost"
    )] = 100

    trend_max_depth: Annotated[int, Field(
        description="Maximum tree depth for XGBoost"
    )] = 6

    trend_learning_rate: Annotated[float, Field(
        description="Learning rate for XGBoost"
    )] = 0.1

    # -------------------------------------------------------------------------
    # ML Model Configuration - LSTM
    # -------------------------------------------------------------------------
    lstm_sequence_length: Annotated[int, Field(
        description="Sequence length for LSTM input"
    )] = 30

    lstm_epochs: Annotated[int, Field(
        description="Number of training epochs for LSTM"
    )] = 50

    lstm_batch_size: Annotated[int, Field(
        description="Batch size for LSTM training"
    )] = 32

    # -------------------------------------------------------------------------
    # RAG Configuration
    # -------------------------------------------------------------------------
    rag_embedding_model: Annotated[str, Field(
        description="Embedding model for RAG (sentence-transformers/all-MiniLM-L6-v2)"
    )] = "sentence-transformers/all-MiniLM-L6-v2"

    rag_default_k: Annotated[int, Field(
        description="Default number of results to retrieve per collection"
    )] = 5

    rag_collection_stocks: Annotated[str, Field(
        description="ChromaDB collection name for stocks"
    )] = "market_stocks"

    rag_collection_news: Annotated[str, Field(
        description="ChromaDB collection name for news"
    )] = "market_news"

    rag_collection_sentiment: Annotated[str, Field(
        description="ChromaDB collection name for sentiment"
    )] = "market_sentiment"

    rag_llm_model: Annotated[str, Field(
        description="LLM model for RAG agent (gpt-3.5-turbo)"
    )] = "gpt-3.5-turbo"

    rag_llm_temperature: Annotated[float, Field(
        description="LLM temperature for RAG agent (0.0=deterministic, 0.3=balanced, 0.7=creative). Must be 0.0-1.0.",
        ge=0.0,
        le=1.0,
    )] = 0.3

    rag_max_retries: Annotated[int, Field(
        description="Max retries for RAG operations"
    )] = 2

    # -------------------------------------------------------------------------
    # LLM Provider Configuration (OpenAI / DeepSeek / etc.)
    # -------------------------------------------------------------------------
    llm_provider: Annotated[str, Field(
        description="LLM provider: 'openai' (OpenAI API) or 'deepseek' (DeepSeek API) or any OpenAI-compatible"
    )] = "openai"

    deepseek_api_key: Annotated[str, Field(
        description="DeepSeek API key (if llm_provider='deepseek')"
    )] = ""

    deepseek_api_base: Annotated[str, Field(
        description="DeepSeek API base URL"
    )] = "https://api.deepseek.com"

    deepseek_model: Annotated[str, Field(
        description="DeepSeek model name"
    )] = "deepseek-chat"

    # -------------------------------------------------------------------------
    # Semantic Cache Configuration
    # -------------------------------------------------------------------------
    cache_enabled: Annotated[bool, Field(
        description="Enable semantic query cache"
    )] = True

    cache_ttl_seconds: Annotated[int, Field(
        description="Cache time-to-live in seconds (86400 = 24 hours)",
        ge=0,
    )] = 86400

    cache_similarity_threshold: Annotated[float, Field(
        description="Minimum similarity threshold for cache hit (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )] = 0.85

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: Annotated[str, Field(
        description="Logging level"
    )] = "INFO"

    log_format: Annotated[str, Field(
        description="Log message format"
    )] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    log_file: Annotated[Path, Field(
        description="Log file path"
    )] = LOGS_DIR / "market_intelligence.log"

    # -------------------------------------------------------------------------
    # Next.js UI
    # -------------------------------------------------------------------------
    next_public_api_url: Annotated[str, Field(
        description="Backend API URL for Next.js frontend"
    )] = "http://localhost:8000"

    next_public_chat_endpoint: Annotated[str, Field(
        description="Chat endpoint for Next.js frontend"
    )] = "http://localhost:8000/api/chat"

    # -------------------------------------------------------------------------
    # API Server (FastAPI)
    # -------------------------------------------------------------------------
    api_host: Annotated[str, Field(
        description="FastAPI server host"
    )] = "0.0.0.0"

    api_port: Annotated[int, Field(
        description="FastAPI server port",
        ge=1,
        le=65535,
    )] = 8000

    cors_origins: Annotated[list[str], Field(
        description="Allowed CORS origins",
        default_factory=lambda: ["http://localhost:3000"],
    )]

    api_workers: Annotated[int, Field(
        description="Number of uvicorn workers",
        ge=1,
        le=16,
    )] = 1

    api_key: Annotated[str, Field(
        description="API key for backend-to-frontend auth"
    )] = ""

    # -------------------------------------------------------------------------
    # Supabase (Auth & Database)
    # -------------------------------------------------------------------------
    supabase_url: Annotated[str, Field(
        description="Supabase project URL"
    )] = ""

    supabase_key: Annotated[str, Field(
        description="Supabase anon/public key"
    )] = ""

    supabase_jwt_secret: Annotated[str, Field(
        description="Supabase JWT secret for local token validation"
    )] = ""

    # -------------------------------------------------------------------------
    # MCP / Multi-Market Configuration
    # -------------------------------------------------------------------------
    coinmarketcap_api_key: Annotated[str, Field(
        description="CoinMarketCap API key for cryptocurrency data"
    )] = ""

    fred_api_key: Annotated[str, Field(
        description="FRED API key for macroeconomic data"
    )] = ""

    @field_validator("tracked_symbols", "rss_feed_urls", "cors_origins", mode="after")
    @classmethod
    def parse_list_fields(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated values into a list."""
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v if isinstance(v, list) else []

    @field_validator("tracked_symbols", mode="after")
    @classmethod
    def uppercase_symbols(cls, v: list[str]) -> list[str]:
        """Normalize stock symbols to uppercase."""
        return [s.upper() for s in v]

    @field_validator("chromadb_persist_dir", "yfinance_cache_dir", "model_save_dir", "log_file", "data_processed_dir", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects relative to PROJECT_ROOT."""
        if isinstance(v, str):
            return PROJECT_ROOT / v
        return v

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [
            DATA_DIR,
            DATA_RAW_DIR,
            DATA_PROCESSED_DIR,
            LOGS_DIR,
            self.chromadb_persist_dir,
            self.model_save_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Settings are loaded once and cached for the lifetime of the process.

    **Security**: In production (APP_ENV=production), ONLY system environment
    variables are used — the .env file is NEVER loaded. This prevents
    credential leaks from accidentally included .env files in the container.

    In development, .env is loaded as a fallback for convenience.

    Returns:
        Settings: Singleton settings instance
    """
    # ── Production mode: EXCLUSIVELY system env vars ──────────────────────
    # No .env file is read. All credentials MUST come from the orchestration
    # layer (Docker/K8s secrets, CI/CD pipelines, etc.).
    if os.getenv("APP_ENV", "").lower() == "production":
        settings = Settings(_env_file=None)
        settings.ensure_directories()
        return settings

    # ── Development mode: .env file fallback ──────────────────────────────
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        env_example = PROJECT_ROOT / ".env.example"
        if env_example.exists():
            load_dotenv(env_example, override=False)

    settings = Settings()
    settings.ensure_directories()
    return settings


# =============================================================================
# MODULE-LEVEL ACCESSOR
# =============================================================================

settings = get_settings()
"""Module-level settings instance for convenience."""

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "PROJECT_ROOT",
    "DATA_DIR",
    "DATA_RAW_DIR",
    "DATA_PROCESSED_DIR",
    "LOGS_DIR",
]
