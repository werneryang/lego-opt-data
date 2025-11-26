"""
Tests for retry mechanism utilities.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, call

from opt_data.util.retry import retry_with_backoff, RetryPolicy


class TestRetryWithBackoff:
    """Test the retry_with_backoff decorator."""
    
    def test_sync_function_succeeds_immediately(self):
        """Test that a successful function is called only once."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_attempts=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_sync_function_retries_on_failure(self):
        """Test that a failing function is retried."""
        mock_func = Mock(side_effect=[
            ConnectionError("first attempt"),
            ConnectionError("second attempt"),
            "success"
        ])
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,  # Short delay for testing
            retriable_exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_sync_function_fails_after_max_attempts(self):
        """Test that function raises after max attempts."""
        mock_func = Mock(side_effect=ConnectionError("persistent error"))
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            retriable_exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(ConnectionError, match="persistent error"):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_non_retriable_exception_fails_immediately(self):
        """Test that non-retriable exceptions are not retried."""
        mock_func = Mock(side_effect=ValueError("not retriable"))
        
        @retry_with_backoff(
            max_attempts=3,
            retriable_exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError, match="not retriable"):
            test_func()
        
        # Should not retry
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_function_succeeds_immediately(self):
        """Test that a successful async function is called only once."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_function_retries_on_failure(self):
        """Test that a failing async function is retried."""
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            retriable_exceptions=(ConnectionError,)
        )
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError(f"attempt {call_count}")
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert call_count == 3
    
    def test_exponential_backoff_delay(self):
        """Test that delay increases exponentially."""
        delays = []
        
        def on_retry_callback(exception, attempt, delay):
            delays.append(delay)
        
        @retry_with_backoff(
            max_attempts=4,
            initial_delay=1.0,
            backoff_factor=2.0,
            retriable_exceptions=(ValueError,),
            on_retry=on_retry_callback,
        )
        def test_func():
            if len(delays) < 3:
                raise ValueError("retry me")
            return "success"
        
        result = test_func()
        assert result == "success"
        # Delays should be: 1.0, 2.0, 4.0
        assert delays == [1.0, 2.0, 4.0]
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        delays = []
        
        def on_retry_callback(exception, attempt, delay):
            delays.append(delay)
        
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=10.0,
            backoff_factor=2.0,
            max_delay=15.0,
            retriable_exceptions=(ValueError,),
            on_retry=on_retry_callback,
        )
        def test_func():
            if len(delays) < 4:
                raise ValueError("retry me")
            return "success"
        
        result = test_func()
        # All delays should be capped at 15.0
        assert all(d <= 15.0 for d in delays)


class TestRetryPolicy:
    """Test the RetryPolicy class."""
    
    def test_sync_execution_success(self):
        """Test successful execution with RetryPolicy."""
        policy = RetryPolicy(max_attempts=3, initial_delay=0.01)
        
        def simple_func(x):
            return x * 2
        
        result = policy.execute(simple_func, 5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_async_execution_success(self):
        """Test successful async execution with RetryPolicy."""
        policy = RetryPolicy(max_attempts=3, initial_delay=0.01)
        
        async def simple_async_func(x):
            await asyncio.sleep(0.01)
            return x * 2
        
        result = await policy.execute_async(simple_async_func, 5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_async_execution_with_retry(self):
        """Test async execution with retries."""
        policy = RetryPolicy(
            max_attempts=3,
            initial_delay=0.01,
            retriable_exceptions=(ValueError,)
        )
        
        call_count = 0
        
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"attempt {call_count}")
            return "success"
        
        result = await policy.execute_async(flaky_func)
        assert result == "success"
        assert call_count == 3
