from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import pandas as pd


@dataclass(frozen=True)
class OIProbeConfig:
    """Configuration for a lightweight OI probe."""

    symbol: str
    expiries: int = 1
    expiry_offset: int = 1  # skip nearest by default, use the next expiry
    strikes_per_side: int = 2
    timeout: float = 15.0
    poll_interval: float = 0.5


def _select_expiries(all_expirations: Sequence[str], cfg: OIProbeConfig) -> list[str]:
    if not all_expirations:
        return []
    expirations_sorted = sorted(all_expirations)
    start = min(max(cfg.expiry_offset, 0), len(expirations_sorted) - 1)
    end = min(start + cfg.expiries, len(expirations_sorted))
    return expirations_sorted[start:end]


def _select_strikes(strikes: Iterable[float], spot: float, per_side: int) -> list[float]:
    all_strikes = sorted(float(s) for s in strikes)
    if not all_strikes or per_side <= 0 or spot <= 0:
        return []
    nearest_idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - spot))
    start_idx = max(0, nearest_idx - per_side)
    end_idx = min(len(all_strikes) - 1, nearest_idx + per_side)
    return all_strikes[start_idx : end_idx + 1]


def probe_oi(ib: Any, cfg: OIProbeConfig) -> pd.DataFrame:
    """Probe real-time option OI around spot for one underlying.

    This is a small operational helper and is not used in the main pipeline.
    It relies on reqMktData + generic tick '101' and reads call/put open interest.
    """

    from ib_insync import Option, Stock  # type: ignore

    symbol = cfg.symbol.upper()
    underlying = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(underlying)

    ticker = ib.reqMktData(underlying, "", False, False)
    ib.sleep(2.0)
    spot = 0.0
    if ticker is not None:
        try:
            price_val = getattr(ticker, "marketPrice", None)
            spot = float(price_val()) if callable(price_val) else float(price_val or 0.0)
        except Exception:
            spot = 0.0
    if spot <= 0:
        return pd.DataFrame()

    chains = ib.reqSecDefOptParams(underlying.symbol, "", underlying.secType, underlying.conId)
    chain = next((c for c in chains if getattr(c, "exchange", "") == "SMART"), None)
    if chain is None:
        return pd.DataFrame()

    expiries = _select_expiries(list(chain.expirations), cfg)
    if not expiries:
        return pd.DataFrame()

    strikes = _select_strikes(chain.strikes, spot, cfg.strikes_per_side)
    if not strikes:
        return pd.DataFrame()

    contracts: list[Any] = []
    for exp in expiries:
        for s in strikes:
            contracts.append(Option(symbol, exp, s, "C", "SMART"))
            contracts.append(Option(symbol, exp, s, "P", "SMART"))
    if not contracts:
        return pd.DataFrame()

    qualified = ib.qualifyContracts(*contracts)
    if not qualified:
        return pd.DataFrame()

    for c in qualified:
        ib.reqMktData(c, "101", False, False)

    start = time.monotonic()
    while time.monotonic() - start < cfg.timeout:
        ready = True
        for c in qualified:
            t = ib.ticker(c)
            if not t:
                ready = False
                break
            call_oi = getattr(t, "callOpenInterest", None)
            put_oi = getattr(t, "putOpenInterest", None)
            if (c.right == "C" and not _valid_oi(call_oi)) or (
                c.right == "P" and not _valid_oi(put_oi)
            ):
                ready = False
                break
        if ready:
            break
        ib.sleep(cfg.poll_interval)

    rows: list[dict[str, Any]] = []
    for c in qualified:
        t = ib.ticker(c)
        if not t:
            continue
        if c.right == "C":
            oi_val = getattr(t, "callOpenInterest", None)
        else:
            oi_val = getattr(t, "putOpenInterest", None)
        if not _valid_oi(oi_val):
            continue

        bid = t.bid if getattr(t, "bid", None) and t.bid > 0 else None
        ask = t.ask if getattr(t, "ask", None) and t.ask > 0 else None
        mid = (bid + ask) / 2.0 if bid is not None and ask is not None else None
        try:
            oi_int = int(oi_val)
        except Exception:
            continue
        iv = getattr(t, "impliedVolatility", None)
        iv_pct = None
        try:
            if iv is not None and not math.isnan(float(iv)) and iv > 0:
                iv_pct = float(iv) * 100.0
        except Exception:
            iv_pct = None

        rows.append(
            {
                "symbol": getattr(c, "localSymbol", "") or f"{symbol}",
                "underlying": symbol,
                "expiry": c.lastTradeDateOrContractMonth,
                "strike": c.strike,
                "right": c.right,
                "bid": float(bid) if bid is not None else 0.0,
                "ask": float(ask) if ask is not None else 0.0,
                "mid": float(mid) if mid is not None else 0.0,
                "open_interest": oi_int,
                "volume": int(getattr(t, "volume", 0) or 0),
                "iv_pct": iv_pct,
            }
        )

    return pd.DataFrame(rows)


def _valid_oi(value: Any) -> bool:
    if value is None:
        return False
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False
    if num <= 0 or math.isnan(num):
        return False
    return True


__all__ = ["OIProbeConfig", "probe_oi"]
