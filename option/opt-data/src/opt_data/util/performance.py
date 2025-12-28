"""
Performance monitoring and logging utilities.

This module provides decorators and utilities for measuring and logging
function execution time, useful for performance analysis and optimization.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Callable, TypeVar, Optional

T = TypeVar("T")


def log_performance(
    logger: Optional[logging.Logger] = None,
    operation_name: Optional[str] = None,
    level: int = logging.INFO,
    log_args: bool = False,
):
    """
    Decorator to log function execution time.

    Measures and logs how long a function takes to execute, useful for
    identifying performance bottlenecks.

    Args:
        logger: Logger to use (defaults to function's module logger)
        operation_name: Name to use in log (defaults to function name)
        level: Log level for completion message
        log_args: Whether to log function arguments

    Returns:
        Decorated function that logs execution time

    Example:
        @log_performance(logger, "data_processing")
        def process_data(df):
            # ... processing logic ...
            return result
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)

        name = operation_name or func.__name__

        # Handle async functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                if log_args:
                    logger.debug(f"{name} called with args={args}, kwargs={kwargs}")

                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    logger.log(level, f"{name} completed in {duration:.2f}s")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"{name} failed after {duration:.2f}s: {type(e).__name__}: {e}")
                    raise

            return async_wrapper

        # Handle sync functions
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                if log_args:
                    logger.debug(f"{name} called with args={args}, kwargs={kwargs}")

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    logger.log(level, f"{name} completed in {duration:.2f}s")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"{name} failed after {duration:.2f}s: {type(e).__name__}: {e}")
                    raise

            return sync_wrapper

    return decorator


class PerformanceTimer:
    """
    Context manager for timing code blocks.

    Example:
        with PerformanceTimer("data_loading", logger):
            df = pd.read_parquet(file)
    """

    def __init__(
        self,
        operation_name: str,
        logger: Optional[logging.Logger] = None,
        level: int = logging.INFO,
    ):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.level = level
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.log(self.level, f"{self.operation_name} completed in {duration:.2f}s")
        else:
            self.logger.error(
                f"{self.operation_name} failed after {duration:.2f}s: "
                f"{exc_type.__name__}: {exc_val}"
            )
        return False  # Don't suppress exceptions
