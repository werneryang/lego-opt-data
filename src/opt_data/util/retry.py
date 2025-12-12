"""
Retry utilities for handling transient failures.

This module provides decorators and utilities for automatic retry with
exponential backoff, configurable retry policies, and detailed logging.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Callable, TypeVar, Type, Tuple, Optional

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Retries a function call if it raises a retriable exception, using
    exponential backoff between attempts.

    Args:
        max_attempts: Maximum number of attempts (including initial call)
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries in seconds
        retriable_exceptions: Tuple of exception types to retry on
        on_retry: Optional callback(exception, attempt, delay) called before retry

    Returns:
        Decorated function that automatically retries on failure

    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def fetch_data():
            # May raise ConnectionError
            return request.get(url)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Handle async functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                delay = initial_delay
                last_exception = None

                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except retriable_exceptions as e:
                        last_exception = e

                        if attempt == max_attempts:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: "
                                f"{type(e).__name__}: {e}"
                            )
                            raise

                        # Calculate delay with exponential backoff
                        current_delay = min(delay, max_delay)

                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: "
                            f"{type(e).__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt, current_delay)

                        await asyncio.sleep(current_delay)
                        delay *= backoff_factor
                    except Exception as e:
                        # Non-retriable exception - fail immediately
                        logger.error(
                            f"{func.__name__} failed with non-retriable exception: "
                            f"{type(e).__name__}: {e}"
                        )
                        raise

                # Should never reach here, but satisfy type checker
                raise last_exception

            return async_wrapper

        # Handle sync functions
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                delay = initial_delay
                last_exception = None

                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except retriable_exceptions as e:
                        last_exception = e

                        if attempt == max_attempts:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: "
                                f"{type(e).__name__}: {e}"
                            )
                            raise

                        # Calculate delay with exponential backoff
                        current_delay = min(delay, max_delay)

                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: "
                            f"{type(e).__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt, current_delay)

                        time.sleep(current_delay)
                        delay *= backoff_factor
                    except Exception as e:
                        # Non-retriable exception - fail immediately
                        logger.error(
                            f"{func.__name__} failed with non-retriable exception: "
                            f"{type(e).__name__}: {e}"
                        )
                        raise

                # Should never reach here, but satisfy type checker
                raise last_exception

            return sync_wrapper

    return decorator


class RetryPolicy:
    """
    Configurable retry policy for more complex scenarios.

    Allows for more fine-grained control over retry behavior compared
    to the decorator.

    Example:
        policy = RetryPolicy(max_attempts=5, initial_delay=0.5)
        result = await policy.execute_async(risky_operation, arg1, arg2)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retriable_exceptions = retriable_exceptions

    async def execute_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute an async function with retry logic."""
        delay = self.initial_delay
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except self.retriable_exceptions as e:
                last_exception = e

                if attempt == self.max_attempts:
                    raise

                current_delay = min(delay, self.max_delay)
                logger.warning(
                    f"Retry attempt {attempt}/{self.max_attempts} after {current_delay:.1f}s"
                )

                await asyncio.sleep(current_delay)
                delay *= self.backoff_factor

        raise last_exception

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute a sync function with retry logic."""
        delay = self.initial_delay
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except self.retriable_exceptions as e:
                last_exception = e

                if attempt == self.max_attempts:
                    raise

                current_delay = min(delay, self.max_delay)
                logger.warning(
                    f"Retry attempt {attempt}/{self.max_attempts} after {current_delay:.1f}s"
                )

                time.sleep(current_delay)
                delay *= self.backoff_factor

        raise last_exception
