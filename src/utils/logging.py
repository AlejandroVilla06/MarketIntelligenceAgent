"""
Logging Utilities
=================

Provides structured logging with Loguru.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Iterator

from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# LOG LEVELS
# =============================================================================

class LogLevel(str, Enum):
    """Standard log levels."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =============================================================================
# LOG PIPELINE
# =============================================================================

class LogPipeline:
    """
    Manages logging configuration for the application.

    Usage:
        pipeline = LogPipeline("MarketIntelligence")
        pipeline.configure()
        log = get_logger("my_module")
        log.info("Starting process")
    """

    def __init__(
        self,
        app_name: str = "MarketIntelligence",
        log_file: str | Path | None = None,
        level: str = "INFO",
        format_string: str | None = None,
    ) -> None:
        """
        Initialize log pipeline.

        Args:
            app_name: Application name for log filtering
            log_file: Optional file path for log output
            level: Minimum log level
            format_string: Custom log format string
        """
        self.app_name = app_name
        self.log_file = Path(log_file) if log_file else None
        self.level = level.upper()
        self.format_string = format_string or (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
            "<level>{message}</level>"
        )

    def configure(self) -> None:
        """Configure the global logger with handlers."""
        # Remove default handler
        logger.remove()

        # Console handler with color
        logger.add(
            sys.stdout,
            level=self.level,
            format=self.format_string,
            colorize=True,
        )

        # File handler if specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                self.log_file,
                level=self.level,
                format=self.format_string,
                rotation="10 MB",
                retention="30 days",
                compression="zip",
            )

    @contextmanager
    def session(self, operation: str) -> Iterator[logger]:
        """
        Context manager for logging operation sessions.

        Usage:
            pipeline = LogPipeline()
            pipeline.configure()
            with pipeline.session("Data Ingestion") as log:
                log.info("Starting ingestion")
                # ... do work
                log.info("Completed")
        """
        start_time = datetime.now()
        log = get_logger(self.app_name)

        log.info(f"=== Starting: {operation} ===")
        try:
            yield log
            elapsed = (datetime.now() - start_time).total_seconds()
            log.success(f"=== Completed: {operation} ({elapsed:.2f}s) ===")
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            log.error(f"=== Failed: {operation} ({elapsed:.2f}s) ===")
            log.exception(f"Error in {operation}: {e}")
            raise


# =============================================================================
# LOGGER FACTORY
# =============================================================================

def get_logger(name: str | None = None) -> logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name for identification (defaults to caller's module)

    Returns:
        A Loguru logger instance

    Usage:
        log = get_logger("data_pipeline")
        log.info("Processing batch")
        log.warning("Retrying failed item")
        log.error("Could not connect to API")
    """
    if name is None:
        # Get caller's module name
        import inspect
        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            name = caller_frame.f_globals.get("__name__", "unknown")

    return logger.bind(name=name)


# =============================================================================
# DEFAULT PIPELINE
# =============================================================================

def configure_logging(
    log_file: str | Path | None = None,
    level: str = "INFO",
) -> LogPipeline:
    """
    Configure logging with sensible defaults.

    Args:
        log_file: Optional file path for log output
        level: Minimum log level

    Returns:
        Configured LogPipeline instance
    """
    from src.config import settings

    pipeline = LogPipeline(
        app_name="MarketIntelligence",
        log_file=log_file or settings.log_file,
        level=level or settings.log_level,
        format_string=settings.log_format,
    )
    pipeline.configure()
    return pipeline


__all__ = [
    "get_logger",
    "LogPipeline",
    "LogLevel",
    "configure_logging",
]
