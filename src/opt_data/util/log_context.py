"""
Logging context management for structured logging.

This module provides utilities for adding contextual information to logs,
making it easier to trace operations across the codebase.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Dict, Any, Optional
import logging


# Context variable for storing log context across async calls
_log_context: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})


class LogContext:
    """
    Context manager for adding structured context to logs.

    Useful for adding metadata like trade_date, symbol, operation_id
    that should be included in all log messages within a scope.

    Example:
        with LogContext(trade_date="2025-11-26", symbol="AAPL"):
            logger.info("Processing snapshot")  # Will include context
            process_data()
    """

    def __init__(self, **context):
        """
        Initialize log context.

        Args:
            **context: Key-value pairs to add to log context
        """
        self.context = context
        self.token = None

    def __enter__(self):
        # Get current context and add new fields
        current = _log_context.get().copy()
        current.update(self.context)
        self.token = _log_context.set(current)
        return self

    def __exit__(self, *args):
        # Restore previous context
        if self.token is not None:
            _log_context.reset(self.token)


def get_log_context() -> Dict[str, Any]:
    """Get the current log context."""
    return _log_context.get().copy()


def set_log_context(**context):
    """
    Set log context fields.

    Alternative to using LogContext manager for programmatic setting.
    """
    current = _log_context.get().copy()
    current.update(context)
    _log_context.set(current)


def clear_log_context():
    """Clear all log context fields."""
    _log_context.set({})


class ContextFormatter(logging.Formatter):
    """
    Custom formatter that includes log context in messages.

    Can be used to add structured context to standard logging output.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Add context to record
        context = get_log_context()
        if context:
            # Add context as extra fields on the record
            for key, value in context.items():
                setattr(record, key, value)

            # Format context string
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            record.msg = f"[{context_str}] {record.msg}"

        return super().format(record)


def configure_contextual_logging(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
):
    """
    Configure a logger to use contextual formatting.

    Args:
        logger: Logger to configure (defaults to root logger)
        level: Logging level
        format_string: Custom format string
    """
    if logger is None:
        logger = logging.getLogger()

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create handler with context formatter
    handler = logging.StreamHandler()
    handler.setFormatter(ContextFormatter(format_string))

    logger.addHandler(handler)
    logger.setLevel(level)
