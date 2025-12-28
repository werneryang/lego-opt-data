from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

try:  # optional for offline environments
    import pandas_market_calendars as mcal
except Exception:  # pragma: no cover
    mcal = None  # type: ignore


ET = ZoneInfo("America/New_York")
DEFAULT_OPEN_TIME = time(hour=9, minute=30)
DEFAULT_CLOSE_TIME = time(hour=16, minute=0)


@dataclass(frozen=True)
class TradingSession:
    market_open: datetime
    market_close: datetime
    early_close: bool = False


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


def get_trading_session(d: date) -> TradingSession:
    """Return the trading session for the given date in ET."""

    default_open = datetime.combine(d, DEFAULT_OPEN_TIME, tzinfo=ET)
    default_close = datetime.combine(d, DEFAULT_CLOSE_TIME, tzinfo=ET)

    if mcal is None:
        return TradingSession(default_open, default_close, False)

    cal = mcal.get_calendar("XNYS")
    schedule = cal.schedule(start_date=d, end_date=d)

    if schedule.empty:
        return TradingSession(default_open, default_close, False)

    row = schedule.iloc[0]
    market_open = row["market_open"].tz_convert(ET).to_pydatetime()
    market_close = row["market_close"].tz_convert(ET).to_pydatetime()

    if market_close <= market_open:
        return TradingSession(default_open, default_close, False)

    early_close = market_close.time() < DEFAULT_CLOSE_TIME
    return TradingSession(market_open, market_close, early_close)
