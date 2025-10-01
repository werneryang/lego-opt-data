from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Iterable
import json


@dataclass
class ContractInfo:
    conid: int
    symbol: str
    expiry: str
    right: str
    strike: float
    multiplier: float
    exchange: str
    tradingClass: str


def cache_path(root: Path, symbol: str, trade_date: str) -> Path:
    return (root / f"{symbol.upper()}_{trade_date}.json").resolve()


def load_cache(root: Path, symbol: str, trade_date: str) -> List[Dict[str, Any]]:
    p = cache_path(root, symbol, trade_date)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return []


def save_cache(root: Path, symbol: str, trade_date: str, items: List[Dict[str, Any]]) -> Path:
    p = cache_path(root, symbol, trade_date)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(items), encoding="utf-8")
    return p


def filter_by_scope(
    contracts: Iterable[Dict[str, Any]],
    underlying_close: float,
    moneyness_pct: float,
    allowed_expiry_types: Iterable[str],
) -> List[Dict[str, Any]]:
    from datetime import date
    from ..util.expiry import is_standard_monthly_expiry, is_quarterly_expiry

    low = underlying_close * (1.0 - moneyness_pct)
    high = underlying_close * (1.0 + moneyness_pct)
    kinds = {k.lower() for k in allowed_expiry_types}

    out: List[Dict[str, Any]] = []
    for c in contracts:
        strike = float(c.get("strike", 0.0))
        exp_str = str(c.get("expiry"))
        try:
            d = date.fromisoformat(exp_str)
        except ValueError:
            # try YYYYMMDD
            if len(exp_str) == 8:
                d = date(int(exp_str[0:4]), int(exp_str[4:6]), int(exp_str[6:8]))
            else:
                continue

        is_monthly = is_standard_monthly_expiry(d)
        is_quarter = is_quarterly_expiry(d)
        if ("monthly" in kinds and is_monthly) or ("quarterly" in kinds and is_quarter):
            if low <= strike <= high:
                out.append(c)
    return out


def discover_contracts(*_: Any, **__: Any) -> List[Dict[str, Any]]:  # pragma: no cover - placeholder
    """Placeholder for IB-based discovery, implemented later."""
    return []
