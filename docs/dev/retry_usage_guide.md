# Retry Mechanism Usage Guide

## Overview

The `opt-data` project includes a robust retry mechanism for handling transient failures in network operations and IB API calls. This guide explains how to use the retry utilities effectively.

## Core Components

### `@retry_with_backoff` Decorator

Located in `src/opt_data/util/retry.py`, this decorator provides automatic retry with exponential backoff.

**Basic Usage**:

```python
from opt_data.util.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def my_network_operation():
    # Your code that might fail transiently
    return api_call()
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_attempts` | int | 3 | Maximum number of retry attempts |
| `initial_delay` | float | 1.0 | Initial delay in seconds before first retry |
| `backoff_factor` | float | 2.0 | Multiplier for delay between retries |
| `max_delay` | float | 60.0 | Maximum delay between retries |
| `retriable_exceptions` | tuple | `(Exception,)` | Specific exceptions to retry |
| `logger` | logging.Logger | None | Logger for retry events |

## Usage Examples

### Example 1: HTTP Requests with Custom Exceptions

```python
from opt_data.util.retry import retry_with_backoff
import requests

@retry_with_backoff(
    max_attempts=5,
    initial_delay=0.5,
    retriable_exceptions=(requests.ConnectionError, requests.Timeout),
)
def fetch_market_data(symbol):
    response = requests.get(f"https://api.example.com/quotes/{symbol}")
    response.raise_for_status()
    return response.json()
```

### Example 2: IB API Calls with Logging

```python
from opt_data.util.retry import retry_with_backoff
import logging

logger = logging.getLogger(__name__)

@retry_with_backoff(
    max_attempts=3,
    retriable_exceptions=(ConnectionError, TimeoutError, OSError),
    logger=logger,
)
def connect_to_ib(host, port):
    ib.connect(host, port, clientId=1)
    return ib
```

### Example 3: Async Functions

```python
from opt_data.util.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3)
async def fetch_contracts_async(ib, symbol):
    contracts = await ib.reqSecDefOptParamsAsync(symbol, "", "STK", 0)
    return contracts
```

## Backoff Strategy

The retry mechanism uses **exponential backoff** to avoid overwhelming the API:

```
Attempt 1: immediate
Attempt 2: wait initial_delay (default: 1s)
Attempt 3: wait initial_delay * backoff_factor (default: 2s)
Attempt 4: wait initial_delay * backoff_factor^2 (default: 4s)
...
```

**Maximum delay** is capped at `max_delay` (default: 60s).

## Real-World Applications in opt-data

### 1. IB Session Connection

In `src/opt_data/ib/session.py`:

```python
@retry_with_backoff(
    max_attempts=3,
    initial_delay=2.0,
    retriable_exceptions=(ConnectionError, TimeoutError, OSError),
)
def connect(self):
    self.ib.connect(self.host, self.port, clientId=self.client_id)
```

**Why retry here?**
- IB Gateway might be temporarily busy
- Network hiccups during startup
- Port already in use (transient)

### 2. Contract Discovery

In `src/opt_data/ib/discovery.py`:

```python
@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def _fetch_sec_def_opt_params(ib, symbol, underlying_conid):
    params = ib.reqSecDefOptParams(symbol, "", "STK", underlying_conid or 0)
    if not params:
        raise ValueError(f"No option parameters found for {symbol}")
    return params
```

**Why retry here?**
- IB API might return empty results temporarily
- Network delays in receiving response
- Brief API throttling

### 3. Contract Qualification

In `src/opt_data/ib/discovery.py`:

```python
@retry_with_backoff(max_attempts=3, initial_delay=0.5)
def _qualify_contracts_chunk(ib, contracts):
    return ib.qualifyContracts(*contracts)
```

**Why retry here?**
- Batch operations may time out
- Temporary API unavailability
- Rate limiting responses

## Best Practices

### ✅ DO

1. **Retry transient errors only**:
   ```python
   retriable_exceptions=(ConnectionError, TimeoutError)
   ```

2. **Use specific exceptions**:
   ```python
   # Good
   retriable_exceptions=(requests.ConnectionError, requests.Timeout)
   
   # Less good
   retriable_exceptions=(Exception,)  # Too broad
   ```

3. **Log retry attempts**:
   ```python
   logger = logging.getLogger(__name__)
   @retry_with_backoff(logger=logger)
   def my_function():
       ...
   ```

4. **Set reasonable limits**:
   ```python
   # For critical operations
   @retry_with_backoff(max_attempts=5, max_delay=30.0)
   
   # For quick operations
   @retry_with_backoff(max_attempts=2, initial_delay=0.5)
   ```

### ❌ DON'T

1. **Don't retry permanent errors**:
   ```python
   # Bad - authentication will never succeed on retry
   retriable_exceptions=(AuthenticationError,)
   ```

2. **Don't retry without limits**:
   ```python
   # Bad - could loop forever
   @retry_with_backoff(max_attempts=999)
   ```

3. **Don't use retry for ALL exceptions**:
   ```python
   # Bad - masks real bugs
   @retry_with_backoff(retriable_exceptions=(Exception,))
   ```

4. **Don't retry operations with side effects**:
   ```python
   # Bad - might create duplicate orders
   @retry_with_backoff()
   def place_order(ib, order):
       ib.placeOrder(...)  # Non-idempotent operation
   ```

## Monitoring Retries

Enable logging to see retry attempts:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Example output:
```
2025-11-26 10:00:00 - opt_data.ib.session - INFO - Retry attempt 1/3 for connect failed: Connection refused
2025-11-26 10:00:02 - opt_data.ib.session - INFO - Retry attempt 2/3 for connect failed: Connection refused
2025-11-26 10:00:06 - opt_data.ib.session - INFO - connect succeeded on attempt 3
```

## Testing

Test retry behavior in unit tests:

```python
from opt_data.util.retry import retry_with_backoff
import pytest

def test_retry_on_failure():
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def failing_then_succeeding():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"
    
    result = failing_then_succeeding()
    assert result == "success"
    assert call_count == 3
```

## Troubleshooting

**Q: Retries are taking too long**  
A: Reduce `initial_delay` and `max_delay`:
```python
@retry_with_backoff(initial_delay=0.5, max_delay=10.0)
```

**Q: Operation fails even with retries**  
A: Check if the exception is in `retriable_exceptions`. If it's a permanent error, retrying won't help.

**Q: Too many retry attempts**  
A: Reduce `max_attempts`:
```python
@retry_with_backoff(max_attempts=2)
```

**Q: How do I disable retries for testing?**  
A: Mock the function or set `max_attempts=1`:
```python
@retry_with_backoff(max_attempts=1)  # No retries
```

## Related Documentation

- [Troubleshooting Guide](../troubleshooting.md)
- [Logging Implementation](./retry_and_logging_implementation.md)
- [Error Handling](./error_handling_robustness_fixes.md)
