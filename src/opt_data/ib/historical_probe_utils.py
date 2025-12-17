from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Sequence


def third_friday(year: int, month: int) -> date:
    first_day = date(year, month, 1)
    # Monday=0 ... Sunday=6; Friday=4.
    days_until_friday = (4 - first_day.weekday()) % 7
    first_friday = first_day + timedelta(days=days_until_friday)
    return first_friday + timedelta(days=14)


def is_third_friday_family(d: date) -> bool:
    tf = third_friday(d.year, d.month)
    return abs((d - tf).days) <= 1


def parse_yyyymmdd(value: str) -> date | None:
    raw = value.strip().replace("-", "")
    if len(raw) != 8 or not raw.isdigit():
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None


def _parse_expiration(value: str) -> date | None:
    raw = value.strip().replace("-", "")
    if len(raw) == 8:
        return parse_yyyymmdd(raw)
    if len(raw) == 6 and raw.isdigit():
        base = date(int(raw[0:4]), int(raw[4:6]), 1)
        return third_friday(base.year, base.month)
    return None


def pick_nearest_quarterly_expiry(expirations: Sequence[str], *, asof: date) -> str:
    """Pick the nearest quarterly expiry (Mar/Jun/Sep/Dec third Friday family)."""
    parsed: list[tuple[date, str]] = []
    for raw in expirations:
        d = _parse_expiration(raw)
        if d is None:
            continue
        parsed.append((d, raw))
    if not parsed:
        raise ValueError("No parsable expirations")

    quarterlies = [
        (d, raw)
        for d, raw in parsed
        if d >= asof and d.month in {3, 6, 9, 12} and is_third_friday_family(d)
    ]
    if quarterlies:
        best = min(quarterlies, key=lambda x: x[0])[0]
        return best.strftime("%Y%m%d")

    future = [(d, raw) for d, raw in parsed if d >= asof]
    if future:
        best = min(future, key=lambda x: x[0])[0]
        return best.strftime("%Y%m%d")

    best = max(parsed, key=lambda x: x[0])[0]
    return best.strftime("%Y%m%d")


def is_multiple_of(value: float, step: float, *, tol: float = 1e-6) -> bool:
    if step <= 0:
        return False
    quotient = value / step
    return abs(quotient - round(quotient)) < tol


def candidate_strikes(
    strikes: Sequence[float],
    *,
    reference_price: float | None,
    prefer_step: float | None,
) -> list[float]:
    unique = sorted({float(s) for s in strikes if float(s) > 0})
    if not unique:
        return []

    ref = reference_price if reference_price is not None else unique[len(unique) // 2]

    if prefer_step is None or prefer_step <= 0:
        return sorted(unique, key=lambda s: (abs(s - ref), s))

    return sorted(
        unique,
        key=lambda s: (0 if is_multiple_of(s, prefer_step) else 1, abs(s - ref), s),
    )


def stable_batch_slice(items: Sequence[str], *, batch_index: int, batch_count: int) -> list[str]:
    """Deterministically split items into N nearly-equal batches and return one slice."""
    if batch_count <= 0:
        raise ValueError("batch_count must be positive")
    if batch_index < 0 or batch_index >= batch_count:
        raise ValueError("batch_index must be within [0, batch_count)")
    if not items:
        return []

    n = len(items)
    base = n // batch_count
    rem = n % batch_count
    start = batch_index * base + min(batch_index, rem)
    size = base + (1 if batch_index < rem else 0)
    end = min(start + size, n)
    return list(items[start:end])


_SAFE_TOKEN_RE = re.compile(r"[^a-zA-Z0-9._=-]+")


def sanitize_token(value: str) -> str:
    """Sanitize a string token for filenames."""
    token = value.strip().replace(" ", "_")
    token = _SAFE_TOKEN_RE.sub("", token)
    return token or "na"

