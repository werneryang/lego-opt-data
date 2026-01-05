from __future__ import annotations

import time
from typing import Any, Callable, Sequence, TYPE_CHECKING

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


def fetch_daily_bars(
    ib: "IB",
    contract: "Contract",
    *,
    what_to_show: str = "TRADES",
    duration: str = "2 D",
    bar_size: str = "1 day",
    end_date_time: str = "",
    use_rth: bool = True,
    format_date: int = 2,
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
        formatDate=format_date,
        keepUpToDate=False,
    )
    return list(bars) if bars else []


__all__ = ["HistoricalBars", "Throttle", "make_throttle", "fetch_daily_bars"]
