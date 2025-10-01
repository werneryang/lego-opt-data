from __future__ import annotations

from datetime import datetime, date
from zoneinfo import ZoneInfo

try:  # optional for offline environments
    import pandas_market_calendars as mcal
except Exception:  # pragma: no cover
    mcal = None  # type: ignore


ET = ZoneInfo("America/New_York")


def to_et_date(ts_utc: datetime) -> date:
    """Convert a UTC datetime to ET trading date (date component)."""
    return ts_utc.astimezone(ET).date()


def is_trading_day(d: date) -> bool:
    if mcal is None:
        # fallback: Mon-Fri naive
        return d.weekday() < 5
    cal = mcal.get_calendar("XNYS")
    schedule = cal.schedule(start_date=d, end_date=d)
    return not schedule.empty
