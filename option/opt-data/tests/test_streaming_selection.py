from datetime import date

from opt_data.streaming.selection import (
    diff_strikes,
    select_expiries,
    select_strikes_around_spot,
    should_rebalance,
    strike_step,
)


def test_select_expiries_weekly_and_next_monthly() -> None:
    trade_date = date(2024, 1, 10)  # Wed
    expiries = [
        date(2024, 1, 12),  # this Friday
        date(2024, 2, 16),  # next month monthly
        date(2024, 3, 15),
    ]
    selected = select_expiries(expiries, trade_date)
    assert selected == [date(2024, 1, 12), date(2024, 2, 16)]


def test_select_strikes_around_spot() -> None:
    strikes = [100, 101, 102, 103, 104, 105, 106, 107]
    selected = select_strikes_around_spot(strikes, spot=104.2, per_side=2)
    assert selected == [102.0, 103.0, 105.0, 106.0]


def test_strike_step_and_rebalance() -> None:
    strikes = [100, 101, 102, 103, 104]
    step = strike_step(strikes, spot=101.4)
    assert step == 1.0
    assert should_rebalance(100.0, 102.9, step, 3) is False
    assert should_rebalance(100.0, 103.0, step, 3) is True


def test_diff_strikes() -> None:
    removed, added = diff_strikes([100, 101, 102], [101, 102, 103])
    assert removed == [100.0]
    assert added == [103.0]
