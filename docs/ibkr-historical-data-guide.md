# IBKR Historical Option Data Guide

## Overview
This guide documents the limitations and workarounds for fetching historical option data from Interactive Brokers (IBKR) using the TWS API (via `ib_insync`).

## Key Findings: Daily Bars Unavailable
IBKR **does NOT provide daily historical bars (`1 day`) for options**. Requesting them results in:
> `Error 162: No data of type EODChart is available for the exchange 'BEST' and the security type 'Option'`

This limitation applies to all standard data types:
- `TRADES`
- `MIDPOINT`
- `BID` / `ASK`
- `ADJUSTED_LAST` (Returns `Error 321`)
- `OPTION_IMPLIED_VOLATILITY`
- `HISTORICAL_VOLATILITY`

## The Solution: 8-Hour Bars
While `1 day` bars are unavailable, **`8 hours` bars ARE supported** and provide a reliable workaround for obtaining daily-equivalent data.

### Why it works
The US equity option market Regular Trading Hours (RTH) session is 6.5 hours (9:30 AM - 4:00 PM ET). An 8-hour bar is large enough to capture the entire session in a single bar (when `useRTH=True`), or a small number of bars per day (when `useRTH=False`).

### Implementation Details
IBKR aligns `8 hours` bars to fixed UTC intervals (00:00, 08:00, 16:00). For US markets, this typically results in **2 bars per trading day**:

1.  **Morning Bar**: Covers Open to ~11:00 AM/12:00 PM ET (ends at 16:00 UTC).
2.  **Afternoon Bar**: Covers ~11:00 AM/12:00 PM ET to Close.

### Code Example
To get a daily candle, request 8-hour bars and aggregate them:

```python
from ib_insync import *

# ... connection setup ...

# Fetch 8-hour bars (returns ~2 bars per day)
bars = ib.reqHistoricalData(
    contract, 
    endDateTime='',
    durationStr='1 Y',
    barSizeSetting='8 hours', 
    whatToShow='MIDPOINT',
    useRTH=True,
    formatDate=2,
    keepUpToDate=False
)

# Simple aggregation logic to merge 8h bars into 1d bars
daily_bars = []
current_day = None
day_open = day_high = day_low = day_close = day_vol = 0

for b in bars:
    b_date = b.date.date()
    if b_date != current_day:
        if current_day is not None:
            daily_bars.append({
                'date': current_day, 'open': day_open, 'high': day_high, 
                'low': day_low, 'close': day_close, 'volume': day_vol
            })
        current_day = b_date
        day_open = b.open
        day_high = b.high
        day_low = b.low
        day_volume = b.volume
    else:
        # Update current day
        day_high = max(day_high, b.high)
        day_low = min(day_low, b.low)
        day_close = b.close # Close is always the last bar's close
        day_volume += b.volume
        
# Don't forget the last day
if current_day is not None:
    daily_bars.append({
        'date': current_day, 'open': day_open, 'high': day_high, 
        'low': day_low, 'close': day_close, 'volume': day_vol
    })
```

## CLI Command: `history`

We have implemented a CLI command to automate the fetching and aggregation of daily option history using the 8-hour bar workaround.

### Usage
```bash
python -m opt_data.cli history --symbols AAPL --days 30 --config config/opt-data.toml
```

### Options
- `--symbols`: Comma-separated list of symbols (e.g., `AAPL,MSFT`).
- `--days`: Number of historical days to fetch (default: 30).
- `--force-refresh`: Bypass the contracts cache and force contract discovery (useful if cache is stale or missing).

### Output
Data is saved in JSON format:
`data/clean/ib/chain/ib/history/<SYMBOL>/<DATE>/<CONID>.json`

## Troubleshooting

### "No contracts found" Error
If you encounter `No contracts found for <SYMBOL>`, it is likely due to the moneyness filter rejecting all contracts because of a missing reference price.

**Cause:** The contract discovery logic uses a reference price (spot price) to filter strikes within a ±30% range. If this price is 0.0 (e.g., failed to fetch), no strikes will match.

**Resolution:** The `HistoryRunner` now automatically fetches the underlying's historical close price before discovery. If this persists, ensure:
1.  The underlying symbol is valid and has historical data.
2.  You are using `--force-refresh` to rebuild the cache with the correct reference price.

### "HMDS query returned no data"
This error (Error 162) is common for illiquid option contracts when requesting `MIDPOINT` data. It means no trades or quotes occurred during the requested period. This is expected behavior for deep OTM or far-expiry options.

