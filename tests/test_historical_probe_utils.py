from __future__ import annotations

from datetime import date

import pytest

from opt_data.ib.historical_probe_utils import (
    candidate_strikes,
    is_third_friday_family,
    pick_nearest_quarterly_expiry,
    sanitize_token,
    stable_batch_slice,
    third_friday,
)


def test_third_friday_known_month() -> None:
    assert third_friday(2025, 3) == date(2025, 3, 21)


@pytest.mark.parametrize(
    ("d", "expected"),
    [
        (date(2025, 3, 20), True),
        (date(2025, 3, 21), True),
        (date(2025, 3, 22), True),
        (date(2025, 3, 19), False),
        (date(2025, 3, 23), False),
    ],
)
def test_is_third_friday_family(d: date, expected: bool) -> None:
    assert is_third_friday_family(d) is expected


def test_pick_nearest_quarterly_expiry_prefers_quarterly() -> None:
    expirations = ["20250221", "20250321", "20250418", "20250620"]
    assert pick_nearest_quarterly_expiry(expirations, asof=date(2025, 2, 10)) == "20250321"


def test_pick_nearest_quarterly_expiry_falls_back_when_no_quarterly() -> None:
    expirations = ["20250221", "20250418"]
    assert pick_nearest_quarterly_expiry(expirations, asof=date(2025, 2, 10)) == "20250221"


def test_pick_nearest_quarterly_expiry_parses_yyyymm() -> None:
    expirations = ["202503", "202504"]
    assert pick_nearest_quarterly_expiry(expirations, asof=date(2025, 2, 10)) == "20250321"


def test_candidate_strikes_prefers_step_multiple() -> None:
    strikes = [97.0, 98.0, 99.0, 100.0, 101.0]
    ordered = candidate_strikes(strikes, reference_price=99.3, prefer_step=5.0)
    assert ordered[0] == 100.0


def test_stable_batch_slice_even_split() -> None:
    items = [f"S{i}" for i in range(10)]
    assert stable_batch_slice(items, batch_index=0, batch_count=2) == items[:5]
    assert stable_batch_slice(items, batch_index=1, batch_count=2) == items[5:]


def test_stable_batch_slice_remainder() -> None:
    items = [f"S{i}" for i in range(10)]
    assert stable_batch_slice(items, batch_index=0, batch_count=3) == items[:4]
    assert stable_batch_slice(items, batch_index=1, batch_count=3) == items[4:7]
    assert stable_batch_slice(items, batch_index=2, batch_count=3) == items[7:]


def test_sanitize_token() -> None:
    assert sanitize_token("8 hours") == "8_hours"
    assert sanitize_token("BID/ASK") == "BIDASK"
    assert sanitize_token("") == "na"

