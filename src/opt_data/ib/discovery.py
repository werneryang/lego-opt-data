from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Iterable, Optional, TYPE_CHECKING
from collections import defaultdict
import calendar
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
    *,
    trade_date: date,
    expiry_months_ahead: int | None = None,
) -> List[Dict[str, Any]]:
    low = underlying_close * (1.0 - moneyness_pct)
    high = underlying_close * (1.0 + moneyness_pct)
    kinds = {k.lower() for k in allowed_expiry_types}
    expiry_cutoff: date | None = None
    if expiry_months_ahead and expiry_months_ahead > 0:
        # add months without external deps
        month = trade_date.month - 1 + expiry_months_ahead
        year = trade_date.year + month // 12
        month = month % 12 + 1
        day = min(trade_date.day, calendar.monthrange(year, month)[1])
        expiry_cutoff = date(year, month, day)

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

        if d < trade_date:
            continue
        if expiry_cutoff and d > expiry_cutoff:
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
    allow_rebuild: bool = False,
    acquire_token: Optional[Callable[[], None]] = None,
    max_strikes_per_expiry: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Discover option contracts for *symbol* and cache results (SMART-only, 2025 flow).

    Implementation follows IB API v10.26+ guidance:
    - Use reqSecDefOptParams() to get expirations/strikes
    - Restrict discovery to SMART routing
    - Build Option contracts and batch-qualify via qualifyContracts
    - Do NOT call reqContractDetails per candidate
    """

    from ib_insync import Option  # type: ignore

    cache_root = Path(cfg.paths.contracts_cache)
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_key = trade_date.isoformat()

    if force_refresh:
        logger.error(
            "force_refresh disabled; cache must be used",
            extra={"symbol": symbol, "trade_date": trade_date.isoformat()},
        )
        raise RuntimeError("force_refresh disabled; use existing contracts cache")

    cached: List[Dict[str, Any]] = []
    try:
        cached = load_cache(cache_root, symbol, cache_key)
    except Exception as exc:
        logger.warning(
            "Failed to read contracts cache; will rebuild if allowed",
            extra={
                "symbol": symbol,
                "trade_date": trade_date.isoformat(),
                "path": str(cache_root),
                "error": str(exc),
            },
        )
        cached = []
    if cached:
        return cached

    if not allow_rebuild:
        # 缓存缺失直接中断，避免使用 SecDef 动态生成未知行权价
        logger.error(
            "contracts cache missing for trade_date; discovery is disabled",
            extra={"symbol": symbol, "trade_date": trade_date.isoformat(), "path": str(cache_root)},
        )
        raise RuntimeError(f"contracts cache missing: {symbol} {cache_key}")

    ib = session.ensure_connected()

    # 1) Fetch sec def params and keep SMART only
    params = ib.reqSecDefOptParams(symbol, "", "STK", underlying_conid or 0)
    allowed_exchange = (cfg.snapshot.exchange or "SMART").upper()
    secdef = None
    for p in params:
        exch = (p.exchange or "").upper()
        if exch == allowed_exchange:
            secdef = p
            break
    if secdef is None:
        # Fallback: if SMART not returned, pick the first param as last resort
        secdef = params[0] if params else None
    if secdef is None:
        return []

    # 2) Build candidate grid (expiry x strike), apply scope filters
    strikes_all = sorted(float(s) for s in secdef.strikes if s is not None)
    if not strikes_all:
        return []
    cached_strikes: List[float] = []
    cached_path = cache_path(cache_root, symbol, cache_key)
    if cached_path.exists():
        try:
            cached_items = json.loads(cached_path.read_text(encoding="utf-8"))
            cached_strikes = sorted(
                {
                    float(item.get("strike", 0.0))
                    for item in cached_items
                    if item.get("strike") is not None
                }
            )
        except Exception as exc:  # pragma: no cover - logging only
            logger.debug(
                "Failed to read cached strikes for comparison",
                extra={"path": str(cached_path), "error": str(exc)},
            )
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "SecDef strikes fetched",
            extra={
                "symbol": symbol,
                "trade_date": trade_date.isoformat(),
                "exchange": allowed_exchange,
                "strikes_count": len(strikes_all),
                "strikes_min": min(strikes_all),
                "strikes_max": max(strikes_all),
                "strikes_sample": strikes_all[:10],
                "cache_path": str(cached_path),
                "cache_count": len(cached_strikes),
                "cache_sample": cached_strikes[:10],
                "new_vs_cache_sample": [s for s in strikes_all if s not in cached_strikes][:10]
                if cached_strikes
                else [],
                "missing_in_secdef_sample": [s for s in cached_strikes if s not in strikes_all][:10]
                if cached_strikes
                else [],
            },
        )
    if cached_strikes:
        secdef_set = set(strikes_all)
        cache_set = set(cached_strikes)
        if secdef_set != cache_set:
            diff_new = [s for s in strikes_all if s not in cache_set][:10]
            diff_missing = [s for s in cached_strikes if s not in secdef_set][:10]
            logger.error(
                "SecDef strikes mismatch cache; aborting to avoid requesting unknown strikes",
                extra={
                    "symbol": symbol,
                    "trade_date": trade_date.isoformat(),
                    "exchange": allowed_exchange,
                    "cache_path": str(cached_path),
                    "new_not_in_cache": diff_new,
                    "cache_not_in_secdef": diff_missing,
                },
            )
            raise RuntimeError("SecDef strikes differ from cached; rerun without mismatch")

    raw_expirations = [_parse_expiration(exp) for exp in secdef.expirations]
    expirations = [d for d in raw_expirations if d]
    filtered_expiries = sorted(filter_expiries(expirations, cfg.filters.expiry_types))
    if not filtered_expiries or not strikes_all:
        return []
    # Keep only the earliest expiries to avoid requesting far-out contracts that may not be tradable.
    MAX_EXPIRIES = 1
    filtered_expiries = filtered_expiries[:MAX_EXPIRIES]

    candidates: List[Dict[str, Any]] = []
    exchange = allowed_exchange
    trading_class = secdef.tradingClass or symbol
    multiplier = float(secdef.multiplier or 100)
    for expiry_date in filtered_expiries:
        iso_expiry = expiry_date.isoformat()
        for strike in strikes_all:
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
        trade_date=trade_date,
        expiry_months_ahead=cfg.filters.expiry_months_ahead,
    )

    scoped_candidates = limit_strikes_per_expiry(
        scoped_candidates,
        underlying_close=underlying_close,
        max_per_expiry=max_strikes_per_expiry,
    )

    if not scoped_candidates:
        return []

    # 3) Build Option list for both rights and batch-qualify
    options: List[Any] = []
    for cand in scoped_candidates:
        expiry_yyyymmdd = cand["expiry"].replace("-", "")
        for right in ("C", "P"):
            opt = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiry_yyyymmdd,
                strike=cand["strike"],
                right=right,
                exchange=exchange,
                currency="USD",
                tradingClass=trading_class,
            )
            opt.includeExpired = True
            options.append(opt)

    # Batch qualify; no per-candidate reqContractDetails
    qualified: List[Any] = []
    CHUNK = 50
    for i in range(0, len(options), CHUNK):
        chunk = options[i : i + CHUNK]
        try:
            # Optionally acquire token per chunk if provided; otherwise proceed immediately
            if acquire_token:
                acquire_token()
            qualified.extend(ib.qualifyContracts(*chunk))
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning(
                "qualifyContracts chunk failed", extra={"size": len(chunk)}, exc_info=exc
            )
            continue

    # 4) Normalize outputs
    results: Dict[tuple[int, str], Dict[str, Any]] = {}
    for contract in qualified:
        try:
            conid = int(getattr(contract, "conId", 0) or 0)
        except Exception:
            conid = 0
        if not conid:
            continue
        expiry_norm = _normalize_expiry(getattr(contract, "lastTradeDateOrContractMonth", ""))
        right = getattr(contract, "right", "") or ""
        strike_val = getattr(contract, "strike", None)
        try:
            strike_f = float(strike_val) if strike_val is not None else None
        except Exception:
            strike_f = None
        exch = getattr(contract, "exchange", None) or exchange
        results[(conid, exch)] = {
            "conid": conid,
            "symbol": getattr(contract, "symbol", symbol) or symbol,
            "expiry": expiry_norm,
            "right": right,
            "strike": strike_f if strike_f is not None else 0.0,
            "multiplier": float(getattr(contract, "multiplier", "100") or 100),
            "exchange": exch,
            "tradingClass": getattr(contract, "tradingClass", trading_class) or trading_class,
            "currency": getattr(contract, "currency", "USD") or "USD",
        }

    ordered = sorted(
        results.values(), key=lambda x: (x["expiry"], x["strike"], x["right"], x["exchange"])
    )
    cache_written = save_cache(cache_root, symbol, cache_key, ordered)
    if not cache_written.exists() or cache_written.stat().st_size == 0:
        logger.error(
            "Failed to write contracts cache",
            extra={"symbol": symbol, "path": str(cache_written)},
        )
        raise RuntimeError(f"contracts cache not written: {cache_written}")
    logger.info(
        "Discovered %s contracts for %s",
        len(ordered),
        symbol,
        extra={"symbol": symbol, "contracts": len(ordered)},
    )
    return ordered
