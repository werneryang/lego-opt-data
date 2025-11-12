from __future__ import annotations

import logging
import math
from typing import Any, Callable, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

DEFAULT_GENERIC_TICKS = "100,101,104,105,106,165,221,225,233,293,294,295"
DEFAULT_TIMEOUT = 12.0  # seconds
DEFAULT_POLL_INTERVAL = 0.25


def collect_option_snapshots(
    ib: Any,
    contracts: Sequence[Dict[str, Any]],
    *,
    generic_ticks: str = DEFAULT_GENERIC_TICKS,
    timeout: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    acquire_token: Optional[Callable[[], None]] = None,
    require_greeks: bool = True,
) -> List[Dict[str, Any]]:
    """Sequentially subscribe to each contract, wait for quotes/Greeks, then cancel."""

    from ib_insync import Option  # type: ignore

    rows: List[Dict[str, Any]] = []
    for info in contracts:
        expiry = info.get("expiry", "")
        expiry_clean = expiry.replace("-", "")
        option = Option(
            info["symbol"],
            expiry_clean,
            info["strike"],
            info["right"],
            exchange=info.get("exchange", "SMART"),
        )
        option.currency = info.get("currency", "USD")
        if info.get("tradingClass"):
            option.tradingClass = info["tradingClass"]
        if info.get("multiplier"):
            option.multiplier = str(info["multiplier"])
        option.includeExpired = True

        if acquire_token:
            acquire_token()
        ticker = ib.reqMktData(option, genericTickList=generic_ticks, snapshot=False)

        elapsed = 0.0
        while elapsed < timeout:
            price_ready = _has_price(ticker)
            greeks_ready = _has_greeks(ticker)
            if price_ready and (not require_greeks or greeks_ready):
                break
            ib.sleep(poll_interval)
            elapsed += poll_interval

        price_ready = _has_price(ticker)
        greeks_ready = _has_greeks(ticker)
        timed_out = not (price_ready and (not require_greeks or greeks_ready))

        rows.append(
            _build_row(
                info,
                ticker,
                price_ready=price_ready,
                greeks_ready=greeks_ready,
                timed_out=timed_out,
            )
        )

        try:
            ib.cancelMktData(option)
        except Exception:  # pragma: no cover - best effort
            pass

    return rows


def _has_price(ticker: Any) -> bool:
    for attr in ("last", "close", "bid", "ask"):
        value = getattr(ticker, attr, None)
        if value is None:
            continue
        try:
            if not math.isnan(float(value)):
                return True
        except (TypeError, ValueError):
            return True
    return False


def _has_greeks(ticker: Any) -> bool:
    model = getattr(ticker, "modelGreeks", None)
    if not model:
        return False
    for attr in ("impliedVol", "delta", "gamma", "theta", "vega"):
        value = getattr(model, attr, None)
        if value is None:
            return False
        try:
            if math.isnan(float(value)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _build_row(
    info: Dict[str, Any],
    ticker: Any,
    *,
    price_ready: bool,
    greeks_ready: bool,
    timed_out: bool,
) -> Dict[str, Any]:
    model = getattr(ticker, "modelGreeks", None)
    bid_g = getattr(ticker, "bidGreeks", None)
    ask_g = getattr(ticker, "askGreeks", None)
    last_g = getattr(ticker, "lastGreeks", None)

    bid = _to_float(getattr(ticker, "bid", None))
    ask = _to_float(getattr(ticker, "ask", None))
    mid = None
    if bid is not None and ask is not None:
        mid = (bid + ask) / 2.0

    timestamp = getattr(ticker, "time", None)

    row = {
        **info,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "last": _to_float(getattr(ticker, "last", None)),
        "open": _to_float(getattr(ticker, "open", None)),
        "high": _to_float(getattr(ticker, "high", None)),
        "low": _to_float(getattr(ticker, "low", None)),
        "close": _to_float(getattr(ticker, "close", None)),
        "bid_size": _to_float(getattr(ticker, "bidSize", None)),
        "ask_size": _to_float(getattr(ticker, "askSize", None)),
        "last_size": _to_float(getattr(ticker, "lastSize", None)),
        "volume": _to_float(getattr(ticker, "volume", None)),
        "vwap": _to_float(getattr(ticker, "vwap", None)),
        "rt_last": None,
        "rt_size": None,
        "rt_time": None,
        "rt_totalVolume": None,
        "rt_vwap": None,
        "rt_single": None,
        "iv": _safe_get(model, "impliedVol"),
        "delta": _safe_get(model, "delta"),
        "gamma": _safe_get(model, "gamma"),
        "theta": _safe_get(model, "theta"),
        "vega": _safe_get(model, "vega"),
        "market_data_type": getattr(ticker, "marketDataType", None),
        "asof": timestamp.isoformat() if timestamp else None,
        "open_interest": getattr(ticker, "openInterest", None),
        "price_ready": price_ready,
        "greeks_ready": greeks_ready,
        "snapshot_timed_out": timed_out,
    }

    row.update(_parse_rt_volume(getattr(ticker, "rtVolume", "")))
    row["bid_iv"] = _safe_get(bid_g, "impliedVol")
    row["ask_iv"] = _safe_get(ask_g, "impliedVol")
    row["last_iv"] = _safe_get(last_g, "impliedVol")
    return row


def _safe_get(obj: Any, attr: str) -> float | None:
    if not obj:
        return None
    value = getattr(obj, attr, None)
    return _to_float(value)


def _parse_rt_volume(rt: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "rt_last": None,
        "rt_size": None,
        "rt_time": None,
        "rt_totalVolume": None,
        "rt_vwap": None,
        "rt_single": None,
    }
    if not rt:
        return out
    parts = str(rt).split(";")
    if len(parts) >= 6:
        out["rt_last"] = _to_float(parts[0])
        out["rt_size"] = _to_int(parts[1])
        out["rt_time"] = _to_int(parts[2])
        out["rt_totalVolume"] = _to_int(parts[3])
        out["rt_vwap"] = _to_float(parts[4])
        flag = parts[5].strip().lower()
        out["rt_single"] = flag in {"true", "1", "t", "y", "yes"}
    return out


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
