from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
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


# Placeholder: to be implemented with ib_insync calls
def discover_contracts(*_: Any, **__: Any) -> List[Dict[str, Any]]:  # pragma: no cover - placeholder
    return []

