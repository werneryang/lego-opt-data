#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from opt_data.util.calendar import get_trading_session, is_trading_day


ET = ZoneInfo("America/New_York")


def _parse_clock(value: str) -> time:
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid clock: {value} (expected HH:MM)")
    hour = int(parts[0])
    minute = int(parts[1])
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid clock: {value} (expected HH:MM)")
    return time(hour=hour, minute=minute)


def _parse_date(value: str, now_et: datetime) -> date:
    if value == "today":
        return now_et.date()
    return date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute streaming duration (seconds) until market close."
    )
    parser.add_argument(
        "--date",
        default="today",
        help="Trade date in ET (YYYY-MM-DD) or 'today'",
    )
    parser.add_argument(
        "--start-clock",
        default="09:35",
        help="ET clock for the intended start time (HH:MM)",
    )
    args = parser.parse_args()

    now_et = datetime.now(ET)
    trade_date = _parse_date(args.date, now_et)

    if not is_trading_day(trade_date):
        print("0")
        return

    session = get_trading_session(trade_date)
    start_time = datetime.combine(trade_date, _parse_clock(args.start_clock), tzinfo=ET)
    effective_start = start_time
    if trade_date == now_et.date() and now_et > start_time:
        effective_start = now_et

    if session.market_close <= effective_start:
        print("0")
        return

    duration = (session.market_close - effective_start).total_seconds()
    print(str(int(duration)))


if __name__ == "__main__":
    main()
