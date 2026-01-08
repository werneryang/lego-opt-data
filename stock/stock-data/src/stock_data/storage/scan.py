from __future__ import annotations

from datetime import date
from pathlib import Path


def _parse_date_dir(name: str) -> date | None:
    if not name.startswith("date="):
        return None
    value = name.replace("date=", "", 1)
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def existing_partition_dates(root: Path, symbol: str, exchange: str) -> set[date]:
    if not root.exists():
        return set()
    pattern = (
        f"date=*/symbol={symbol.upper()}/exchange={exchange.upper()}/part-*.parquet"
    )
    dates: set[date] = set()
    for path in root.glob(pattern):
        date_dir = path.parents[2].name
        parsed = _parse_date_dir(date_dir)
        if parsed is not None:
            dates.add(parsed)
    return dates


def latest_partition_date(root: Path, symbol: str, exchange: str) -> date | None:
    dates = existing_partition_dates(root, symbol, exchange)
    return max(dates) if dates else None

