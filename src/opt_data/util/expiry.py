from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List

try:
    import pandas_market_calendars as mcal  # type: ignore
except Exception:  # pragma: no cover
    mcal = None  # type: ignore


def third_friday(year: int, month: int) -> date:
    """Return the third Friday of a given month (naive, not holiday-adjusted)."""
    # Start at the 15th (the earliest the 3rd Friday can occur)
    d = date(year, month, 15)
    # Weekday: Monday=0 ... Sunday=6; Friday=5
    offset = (4 - d.weekday()) % 7  # 4==Friday index when starting Monday=0
    return d + timedelta(days=offset)


def _holiday_adjusted_third_friday(year: int, month: int) -> date:
    """Approximate holiday adjustment: if the 3rd Friday is a full market holiday,
    shift backward by 1 day until a trading day is found. If calendar is missing,
    return naive third Friday.
    """
    tf = third_friday(year, month)
    if mcal is None:
        return tf
    cal = mcal.get_calendar("XNYS")
    d = tf
    # move back until schedule is non-empty
    while True:
        sch = cal.schedule(start_date=d, end_date=d)
        if not sch.empty:
            return d
        d = d - timedelta(days=1)


def is_standard_monthly_expiry(d: date) -> bool:
    """Check if a date is standard monthly options expiry (3rd Friday, holiday-adjusted)."""
    return d == _holiday_adjusted_third_friday(d.year, d.month)


def is_quarterly_expiry(d: date) -> bool:
    """Quarterly expiries are the standard monthly expiry in Mar/Jun/Sep/Dec."""
    return d.month in (3, 6, 9, 12) and is_standard_monthly_expiry(d)


def filter_expiries(expiries: Iterable[date], kinds: Iterable[str]) -> List[date]:
    kinds_set = {k.lower() for k in kinds}
    out: List[date] = []
    for d in expiries:
        if "monthly" in kinds_set and is_standard_monthly_expiry(d):
            out.append(d)
        elif "quarterly" in kinds_set and is_quarterly_expiry(d):
            out.append(d)
    # deduplicate while preserving order
    seen = set()
    dedup: List[date] = []
    for d in out:
        if d not in seen:
            dedup.append(d)
            seen.add(d)
    return dedup

