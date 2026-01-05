from __future__ import annotations

import math
import time
from typing import Any

from ib_insync import Ticker  # type: ignore


def fetch_iv_snapshot(
    ib: Any,
    contract: Any,
    *,
    generic_ticks: str = "106",
    timeout: float = 12.0,
    poll_interval: float = 0.25,
) -> float | None:
    """Fetch 30-day IV snapshot via reqMktData + generic tick 106."""

    ticker: Ticker = ib.reqMktData(
        contract,
        genericTickList=generic_ticks,
        snapshot=False,
        regulatorySnapshot=False,
        mktDataOptions=[],
    )
    deadline = time.monotonic() + timeout
    value = None
    while time.monotonic() < deadline:
        value = getattr(ticker, "impliedVolatility", None)
        if value is not None and not (isinstance(value, float) and math.isnan(value)):
            break
        ib.sleep(poll_interval)
    try:
        ib.cancelMktData(contract)
    except Exception:
        pass
    return value


__all__ = ["fetch_iv_snapshot"]
