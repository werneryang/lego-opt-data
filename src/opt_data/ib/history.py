from __future__ import annotations

import time
from typing import Any, Callable, Iterable, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ib_insync import IB
    from ib_insync.contract import Contract

HistoricalBars = Sequence[Any]
Throttle = Callable[[], None]


def make_throttle(min_interval_sec: float = 0.35) -> Throttle:
    """Return a callable enforcing a minimum interval between requests."""

    last_called = 0.0

    def wait() -> None:
        nonlocal last_called
        now = time.monotonic()
        delta = now - last_called
        if delta < min_interval_sec:
            time.sleep(min_interval_sec - delta)
        last_called = time.monotonic()

    return wait


def fetch_daily(
    ib: "IB",
    contract: "Contract",
    *,
    what_to_show: str = "TRADES",
    duration: str = "30 D",
    bar_size: str = "1 day",
    end_date_time: str = "",
    use_rth: bool = True,
    throttle: Throttle | None = None,
) -> list[Any]:
    """Fetch daily bars for *contract* using IB historical data API."""

    if throttle:
        throttle()
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end_date_time,
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow=what_to_show,
        useRTH=use_rth,
        formatDate=2,
        keepUpToDate=False,
    )
    return list(bars) if bars else []


def fetch_option_daily_aggregated(
    ib: "IB",
    contract: "Contract",
    *,
    what_to_show: str = "MIDPOINT",
    duration: str = "30 D",
    end_date_time: str = "",
    use_rth: bool = True,
    throttle: Throttle | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch daily bars for options by aggregating 8-hour bars.

    Workaround for IBKR Error 162 (No data of type EODChart).
    Requests 8-hour bars and aggregates them into single daily bars.
    """
    bars = fetch_daily(
        ib,
        contract,
        what_to_show=what_to_show,
        duration=duration,
        bar_size="8 hours",
        end_date_time=end_date_time,
        use_rth=use_rth,
        throttle=throttle,
    )

    if not bars:
        return []

    def _get_wap(bar: Any) -> float | None:
        """Best-effort read of weighted average price from BarData."""
        for attr in ("wap", "average"):
            val = getattr(bar, attr, None)
            if val is None:
                continue
            try:
                return float(val)
            except Exception:
                continue
        return None

    def _nonneg(value: Any) -> float:
        """Coerce volume/barCount to non-negative floats (quote bars use -1/-2)."""
        try:
            v = float(value)
        except Exception:
            return 0.0
        return v if v > 0 else 0.0

    daily_bars: list[dict[str, Any]] = []
    current_day = None

    # Initialize accumulators
    day_open = 0.0
    day_high = 0.0
    day_low = 0.0
    day_close = 0.0
    day_volume = 0.0
    day_count = 0.0
    day_wap_num = 0.0
    day_wap_den = 0.0

    for b in bars:
        # b.date is typically datetime.date or datetime.datetime
        # Ensure we get a date object
        b_date = b.date.date() if hasattr(b.date, "date") else b.date

        if b_date != current_day:
            # Commit previous day
            if current_day is not None:
                daily_bars.append(
                    {
                        "date": current_day.isoformat(),
                        "open": day_open,
                        "high": day_high,
                        "low": day_low,
                        "close": day_close,
                        "volume": day_volume,
                        "barCount": int(day_count),
                        "wap": (day_wap_num / day_wap_den) if day_wap_den > 0 else None,
                    }
                )

            # Start new day
            current_day = b_date
            day_open = b.open
            day_high = b.high
            day_low = b.low
            day_close = b.close
            day_volume = _nonneg(getattr(b, "volume", 0))
            day_count = _nonneg(getattr(b, "barCount", 0))
            day_wap_num = 0.0
            day_wap_den = 0.0
            wap = _get_wap(b)
            if wap is not None:
                weight = day_volume or day_count or 1.0
                day_wap_num = wap * weight
                day_wap_den = weight
        else:
            # Aggregate into current day
            day_high = max(day_high, b.high)
            day_low = min(day_low, b.low)
            day_close = b.close  # Close is always the last bar's close
            bar_volume = _nonneg(getattr(b, "volume", 0))
            bar_count = _nonneg(getattr(b, "barCount", 0))
            day_volume += bar_volume
            day_count += bar_count
            wap = _get_wap(b)
            if wap is not None:
                weight = bar_volume or bar_count or 1.0
                day_wap_num += wap * weight
                day_wap_den += weight

    # Commit last day
    if current_day is not None:
        daily_bars.append(
            {
                "date": current_day.isoformat(),
                "open": day_open,
                "high": day_high,
                "low": day_low,
                "close": day_close,
                "volume": day_volume,
                "barCount": int(day_count),
                "wap": (day_wap_num / day_wap_den) if day_wap_den > 0 else None,
            }
        )

    return daily_bars


def fetch_option_open_interest(
    ib: "IB",
    contract: "Contract",
    *,
    duration: str = "30 D",
    end_date_time: str = "",
    use_rth: bool = True,
    throttle: Throttle | None = None,
) -> list[Any]:
    """Fetch daily option open interest bars for *contract*."""

    return fetch_daily(
        ib,
        contract,
        what_to_show="OPTION_OPEN_INTEREST",
        duration=duration,
        end_date_time=end_date_time,
        use_rth=use_rth,
        throttle=throttle,
    )


def fetch_midpoint_daily(
    ib: "IB",
    contract: "Contract",
    *,
    duration: str = "30 D",
    end_date_time: str = "",
    use_rth: bool = True,
    throttle: Throttle | None = None,
) -> list[Any]:
    """Fetch daily midpoint bars for *contract* (BID/ASK midpoint)."""

    return fetch_daily(
        ib,
        contract,
        what_to_show="MIDPOINT",
        duration=duration,
        end_date_time=end_date_time,
        use_rth=use_rth,
        throttle=throttle,
    )


def bars_to_dicts(bars: Iterable[Any]) -> list[dict[str, Any]]:
    """Convert ib_insync BarData objects into plain dictionaries."""

    out: list[dict[str, Any]] = []
    for bar in bars:
        if hasattr(bar, "asDict"):
            out.append(bar.asDict())  # type: ignore[attr-defined]
        else:
            out.append(dict(bar))
    return out


__all__ = [
    "HistoricalBars",
    "Throttle",
    "make_throttle",
    "fetch_daily",
    "fetch_option_open_interest",
    "fetch_midpoint_daily",
    "bars_to_dicts",
]
