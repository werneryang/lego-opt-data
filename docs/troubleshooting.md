# Troubleshooting Guide

## Common Issues and Solutions

### 1. Contract Discovery Failures

**Symptom**: Snapshot command fails with "contracts cache missing" error

```
[snapshot:error] symbol=AAPL stage=contracts error=contracts cache missing: AAPL 2025-11-26
```

**Causes**:
- Contract cache file doesn't exist for the trade date
- Cache file is corrupt or incomplete

**Solutions**:

1. **Enable automatic cache rebuild** (Default behavior):
   The snapshot command automatically attempts to rebuild missing caches unless `--fail-on-missing-cache` is used.
   ```bash
   python -m opt_data.cli snapshot --date today --config config/opt-data.toml
   ```

2. **Strict Mode (Fail on missing)**:
   If you want to ensure no unexpected API calls are made for discovery:
   ```bash
   python -m opt_data.cli close-snapshot --date today --fail-on-missing-cache --config config/opt-data.toml
   ```

3. **Pre-generate cache using schedule**:
   ```bash
   python -m opt_data.cli schedule --simulate --date today --build-missing-cache --config config/opt-data.toml
   ```

---

### 2. Connection Errors

**Symptom**: Unable to connect to Interactive Brokers

```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Causes**:
- IB Gateway/TWS not running
- Wrong host/port configuration
- Firewall blocking connection

**Solutions**:

1. **Verify IB Gateway is running**:
   - Start IB Gateway or Trader Workstation
   - Ensure API connections are enabled in settings

2. **Check configuration**:
   ```toml
   [ib]
   host = "127.0.0.1"  # localhost for local IB Gateway
   port = 4002         # 4001 for TWS, 4002 for Gateway
   client_id = 1       # Must be unique per connection
   ```

3. **Test connection**:
   ```bash
   python -m opt_data.cli inspect connection --config config/opt-data.toml
   ```

**Note**: The connection logic includes automatic retry (3 attempts with exponential backoff).

---

### 3. Timeout Errors

**Symptom**: Snapshot collection times out

```
[snapshot:error] symbol=AAPL stage=snapshot error=Data not ready after 12.0s
```

**Causes**:
- Network latency
- Market data subscription delays
- Too many contracts requested simultaneously

**Solutions**:

1. **Increase timeout** (default: 12 seconds):
   ```bash
   python -m opt_data.cli snapshot --date today --timeout 30.0 --config config/opt-data.toml
   ```

2. **Adjust configuration**:
   ```toml
   [snapshot]
   subscription_timeout = 30.0  # seconds
   subscription_poll_interval = 0.5  # seconds
   ```

3. **Reduce contract count**:
   ```toml
   [snapshot]
   strikes_per_side = 5  # Reduce from default
   ```

**Note**: Timeout errors are now automatically flagged and filtered out in rollup processing.

---

### 4. Rollup Errors

**Symptom**: Rollup fails with KeyError or data type errors

```
KeyError: 'underlying'
```

**Causes**:
- Incompatible data format between snapshot and rollup
- Missing required columns
- Data type mismatches

**Solutions**:

1. **Verify data exists**:
   ```bash
   # Check intraday data directory
   ls -R data/clean/ib/chain/view=intraday/date=2025-11-26/
   ```

2. **Check column compatibility**:
   - Rollup expects: `underlying`, `exchange`, `conid`, `trade_date`, `slot_30m`, `sample_time`
   - Snapshot v2 automatically includes these fields
   - Legacy data may need migration

3. **Re-run with clean data**:
   ```bash
   # Clear old data and re-snapshot
   rm -rf data/clean/ib/chain/view=intraday/date=2025-11-26/
   python -m opt_data.cli snapshot --date 2025-11-26 --config config/opt-data.toml
   python -m opt_data.cli rollup --date 2025-11-26 --config config/opt-data.toml
   ```

**Note**: Rollup now gracefully handles missing columns and filters error rows automatically.

---

### 5. Retry Mechanism Issues

**Symptom**: Operations fail even with retry enabled

**Understanding Retry Behavior**:
- **Max attempts**: 3 (configurable)
- **Backoff strategy**: Exponential (1s, 2s, 4s)
- **Retriable exceptions**: `ConnectionError`, `TimeoutError`, `OSError`

**When retries won't help**:
- Authentication errors (fix credentials)
- Invalid contract specifications (fix contract parameters)
- Permanent API errors (check IB API status)

**Enable retry logging**:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

You'll see retry attempts in logs:
```
2025-11-26 10:00:00 - opt_data.util.retry - INFO - Retry attempt 1/3 for connect failed: Connection refused
```

---

### 6. Performance Issues

**Symptom**: Snapshot collection is very slow

**Diagnostics**:

1. **Check concurrent operations**:
   ```bash
   # Monitor active connections
   ps aux | grep -i "tws\|gateway"
   ```

2. **Review rate limits**:
   ```toml
   [rate_limits.snapshot]
   burst = 100
   per_minute = 60
   ```

3. **Enable performance logging**:
   - Performance metrics are automatically logged for key operations
   - Check log files in `state/run_logs/snapshot/`

**Optimizations**:
- Reduce `strikes_per_side` to limit contracts
- Use `close_snapshot` instead of intraday snapshots for end-of-day data
- Throttle discovery requests in config

---

### 7. Data Quality Flags

**Understanding quality flags**:

Common flags in `data_quality_flag` column:
- `snapshot_error`: Subscription failure or timeout
- `snapshot_timeout`: Specific timeout during data collection
- `missing_price`: Bid/ask data not available
- `missing_greeks`: Greeks (delta, gamma, etc.) not available
- `delayed_fallback`: Using delayed data instead of live
- `missing_oi`: Open interest not available

**Handling flagged data**:

1. **Filter out errors**:
   ```python
   # Rollup automatically filters snapshot_error=True
   # You can also filter manually:
   clean_df = df[~df['data_quality_flag'].str.contains('snapshot_error')]
   ```

2. **Review flagged data**:
   ```python
   # Find all flagged rows
   flagged = df[df['data_quality_flag'].apply(len) > 0]
   print(flagged[['symbol', 'strike', 'data_quality_flag']])
   ```

---

## Getting Help

### Log Files

Key log locations:
- **Snapshot logs**: `state/run_logs/snapshot/snapshot_YYYY-MM-DD_HHMM_*.log`
- **Error logs**: `state/run_logs/errors/errors_YYYYMMDD.log`
- **Performance logs**: Check stderr output or configure file logging

### Diagnostic Commands

```bash
# Test IB connection
python -m opt_data.cli inspect connection --config config/opt-data.toml

# View configuration
python -m opt_data.cli inspect config --config config/opt-data.toml

# Check data paths
python -m opt_data.cli inspect paths --config config/opt-data.toml
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Reporting Issues

When reporting issues, include:
1. Command that failed
2. Full error message and stack trace
3. Relevant log files
4. Configuration (sanitized, no credentials)
5. IB Gateway/TWS version
6. Python and package versions
