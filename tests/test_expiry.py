from datetime import date

from opt_data.util.expiry import (
    third_friday,
    is_standard_monthly_expiry,
    is_quarterly_expiry,
    filter_expiries,
)


def test_third_friday_known_dates() -> None:
    assert third_friday(2024, 10) == date(2024, 10, 18)
    assert third_friday(2025, 3) == date(2025, 3, 21)


def test_monthly_and_quarterly_classification() -> None:
    d1 = date(2024, 10, 18)
    d2 = date(2025, 3, 21)
    assert is_standard_monthly_expiry(d1)
    assert is_standard_monthly_expiry(d2)
    assert not is_quarterly_expiry(d1)
    assert is_quarterly_expiry(d2)


def test_filter_expiries() -> None:
    xs = [date(2024, 10, 18), date(2025, 3, 21), date(2025, 6, 20)]
    out_m = filter_expiries(xs, ["monthly"])  # all listed are monthly expiries
    assert out_m == xs
    out_q = filter_expiries(xs, ["quarterly"])  # only Mar and Jun
    assert out_q == [date(2025, 3, 21), date(2025, 6, 20)]
