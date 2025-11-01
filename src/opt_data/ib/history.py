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
        barSizeSetting="1 day",
        whatToShow=what_to_show,
        useRTH=use_rth,
        formatDate=2,
        keepUpToDate=False,
    )
    return list(bars)


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
