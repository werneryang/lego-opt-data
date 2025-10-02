from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Iterable, Optional, TYPE_CHECKING
from collections import defaultdict
import json
import logging
from datetime import date

from ..config import AppConfig
from ..util.expiry import (
    is_standard_monthly_expiry,
    is_quarterly_expiry,
    filter_expiries,
    third_friday,
)

if TYPE_CHECKING:  # pragma: no cover
    from .session import IBSession

logger = logging.getLogger(__name__)


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


def limit_strikes_per_expiry(
    contracts: List[Dict[str, Any]],
    underlying_close: float,
    max_per_expiry: Optional[int],
) -> List[Dict[str, Any]]:
    if not max_per_expiry or max_per_expiry <= 0:
        return contracts

    grouped: Dict[tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for contract in contracts:
        key = (contract.get("expiry", ""), contract.get("exchange", ""))
        grouped[key].append(contract)

    limited: List[Dict[str, Any]] = []
    for key, items in grouped.items():
        ordered = sorted(items, key=lambda c: abs(float(c.get("strike", 0.0)) - underlying_close))
        limited.extend(ordered[:max_per_expiry])
    return limited


def discover_contracts(
    *_: Any, **__: Any
) -> List[Dict[str, Any]]:  # pragma: no cover - placeholder
    """Deprecated placeholder kept for backward compatibility."""
    return []


def _parse_expiration(value: str) -> Optional[date]:
    if len(value) == 8:  # YYYYMMDD
        return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
    if len(value) == 6:  # YYYYMM
        base = date(int(value[0:4]), int(value[4:6]), 1)
        return third_friday(base.year, base.month)
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _normalize_expiry(expiry: str) -> str:
    if len(expiry) == 8 and expiry.isdigit():
        return f"{expiry[0:4]}-{expiry[4:6]}-{expiry[6:8]}"
    return expiry


def discover_contracts_for_symbol(
    session: "IBSession",
    symbol: str,
    trade_date: date,
    underlying_close: float,
    cfg: AppConfig,
    *,
    underlying_conid: Optional[int] = None,
    force_refresh: bool = False,
    acquire_token: Optional[Callable[[], None]] = None,
    max_strikes_per_expiry: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Discover option contracts for *symbol* using IB and cache results."""

    from ib_insync import Option  # type: ignore

    cache_root = Path(cfg.paths.contracts_cache)
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_key = trade_date.isoformat()

    if not force_refresh:
        cached = load_cache(cache_root, symbol, cache_key)
        if cached:
            return cached

    ib = session.ensure_connected()
    if acquire_token:
        acquire_token()
    params = ib.reqSecDefOptParams(symbol, "", "STK", underlying_conid or 0)

    candidates: List[Dict[str, Any]] = []
    for param in params:
        strikes = sorted(float(s) for s in param.strikes if s is not None)
        if not strikes:
            continue
        raw_expirations = [_parse_expiration(exp) for exp in param.expirations]
        expirations = [d for d in raw_expirations if d]
        filtered_expiries = filter_expiries(expirations, cfg.filters.expiry_types)
        if not filtered_expiries:
            continue
        exchange = param.exchange or "SMART"
        trading_class = param.tradingClass or symbol
        multiplier = float(param.multiplier or 100)
        for expiry_date in filtered_expiries:
            iso_expiry = expiry_date.isoformat()
            for strike in strikes:
                candidates.append(
                    {
                        "symbol": symbol,
                        "expiry": iso_expiry,
                        "strike": strike,
                        "exchange": exchange,
                        "tradingClass": trading_class,
                        "multiplier": multiplier,
                    }
                )

    scoped_candidates = filter_by_scope(
        candidates,
        underlying_close=underlying_close,
        moneyness_pct=cfg.filters.moneyness_pct,
        allowed_expiry_types=cfg.filters.expiry_types,
    )

    scoped_candidates = limit_strikes_per_expiry(
        scoped_candidates,
        underlying_close=underlying_close,
        max_per_expiry=max_strikes_per_expiry,
    )

    results: Dict[tuple[int, str], Dict[str, Any]] = {}
    for candidate in scoped_candidates:
        expiry_yyyymmdd = candidate["expiry"].replace("-", "")
        for right in ("C", "P"):
            option = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiry_yyyymmdd,
                strike=candidate["strike"],
                right=right,
                exchange=candidate["exchange"],
                currency="USD",
                tradingClass=candidate["tradingClass"],
            )
            try:
                if acquire_token:
                    acquire_token()
                details = ib.reqContractDetails(option)
            except Exception as exc:  # pragma: no cover - network failure
                logger.warning(
                    "reqContractDetails failed",
                    extra={"symbol": symbol, "right": right, "expiry": expiry_yyyymmdd},
                    exc_info=exc,
                )
                continue
            for detail in details:
                contract = detail.contract
                key = (contract.conId, contract.exchange or candidate["exchange"])
                results[key] = {
                    "conid": contract.conId,
                    "symbol": contract.symbol or symbol,
                    "expiry": _normalize_expiry(contract.lastTradeDateOrContractMonth),
                    "right": contract.right or right,
                    "strike": float(contract.strike or candidate["strike"]),
                    "multiplier": float(contract.multiplier or candidate["multiplier"]),
                    "exchange": contract.exchange or candidate["exchange"],
                    "tradingClass": contract.tradingClass or candidate["tradingClass"],
                    "currency": contract.currency or "USD",
                }

    ordered = sorted(
        results.values(), key=lambda x: (x["expiry"], x["strike"], x["right"], x["exchange"])
    )
    save_cache(cache_root, symbol, cache_key, ordered)
    logger.info(
        "Discovered %s contracts for %s",
        len(ordered),
        symbol,
        extra={"symbol": symbol, "contracts": len(ordered)},
    )
    return ordered
