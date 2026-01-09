from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, List, Sequence

from ..util.expiry import is_standard_monthly_expiry, third_friday


@dataclass(frozen=True)
class StrikeWindow:
    spot: float
    strike_step: float
    strikes: List[float]


def parse_expiration(value: date | str) -> date | None:
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    if len(text) == 8 and text.isdigit():
        return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
    if len(text) == 6 and text.isdigit():
        return third_friday(int(text[0:4]), int(text[4:6]))
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def select_expiries(expirations: Iterable[date | str], trade_date: date) -> List[date]:
    exp_dates = sorted({d for d in (parse_expiration(e) for e in expirations) if d})
    if not exp_dates:
        return []

    weekly = _this_friday(trade_date)
    weekly_expiry = weekly if weekly in exp_dates else _next_friday(exp_dates, trade_date)

    target_year, target_month = _next_month(trade_date.year, trade_date.month)
    monthly_candidates = sorted(d for d in exp_dates if is_standard_monthly_expiry(d))
    monthly_expiry = next(
        (d for d in monthly_candidates if d.year == target_year and d.month == target_month),
        None,
    )
    if monthly_expiry is None:
        monthly_expiry = next(
            (d for d in monthly_candidates if (d.year, d.month) > (target_year, target_month)),
            None,
        )

    selected: List[date] = []
    if weekly_expiry:
        selected.append(weekly_expiry)
    if monthly_expiry and monthly_expiry not in selected:
        selected.append(monthly_expiry)
    return selected


def select_strikes_around_spot(
    strikes: Iterable[float],
    spot: float,
    per_side: int,
    *,
    include_atm: bool = False,
) -> List[float]:
    if per_side <= 0 or spot <= 0:
        return []
    unique = sorted({float(s) for s in strikes if s is not None})
    if not unique:
        return []
    atm_idx = min(range(len(unique)), key=lambda i: abs(unique[i] - spot))
    below = unique[:atm_idx]
    above = unique[atm_idx + 1 :]

    selected = below[-per_side:] + above[:per_side]
    if include_atm and unique[atm_idx] not in selected:
        selected = selected[:per_side] + [unique[atm_idx]] + selected[per_side:]
    return sorted(selected)


def strike_step(strikes: Sequence[float], spot: float) -> float:
    unique = sorted({float(s) for s in strikes if s is not None})
    if len(unique) < 2:
        return 0.0
    atm_idx = min(range(len(unique)), key=lambda i: abs(unique[i] - spot))
    neighbors = []
    if atm_idx > 0:
        neighbors.append(abs(unique[atm_idx] - unique[atm_idx - 1]))
    if atm_idx < len(unique) - 1:
        neighbors.append(abs(unique[atm_idx + 1] - unique[atm_idx]))
    return min(neighbors) if neighbors else 0.0


def should_rebalance(
    previous_spot: float,
    spot: float,
    step: float,
    threshold_steps: int,
) -> bool:
    if step <= 0 or threshold_steps <= 0:
        return False
    return abs(spot - previous_spot) >= step * threshold_steps


def diff_strikes(
    previous: Sequence[float],
    current: Sequence[float],
) -> tuple[List[float], List[float]]:
    prev_set = {float(s) for s in previous}
    cur_set = {float(s) for s in current}
    removed = sorted(prev_set - cur_set)
    added = sorted(cur_set - prev_set)
    return removed, added


def _this_friday(trade_date: date) -> date:
    days_ahead = (4 - trade_date.weekday()) % 7
    return trade_date + timedelta(days=days_ahead)


def _next_friday(expirations: Sequence[date], trade_date: date) -> date | None:
    for d in expirations:
        if d >= trade_date and d.weekday() == 4:
            return d
    return None


def _next_month(year: int, month: int) -> tuple[int, int]:
    month += 1
    if month > 12:
        return year + 1, 1
    return year, month
