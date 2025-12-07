from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Iterable, Optional, TYPE_CHECKING
from collections import defaultdict
import calendar
import json
import logging
from datetime import date, timedelta

from ..config import AppConfig
from ..util.expiry import (
    is_standard_monthly_expiry,
    is_quarterly_expiry,
    third_friday,
)
from ..util.retry import retry_with_backoff

if TYPE_CHECKING:  # pragma: no cover
    from .session import IBSession

logger = logging.getLogger(__name__)


@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def _fetch_sec_def_opt_params(ib: Any, symbol: str, underlying_conid: int) -> List[Any]:
    """Fetch security definition option parameters (strikes/expirations) with retry."""
    return ib.reqSecDefOptParams(symbol, "", "STK", underlying_conid or 0)


@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def _qualify_contracts_chunk(ib: Any, contracts: List[Any]) -> List[Any]:
    """Batch-qualify Option contracts (avoid per-contract reqContractDetails) with retry."""
    return ib.qualifyContracts(*contracts)


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
        allow_weekly = "weekly" in kinds
        allowed = False
        if ("monthly" in kinds and is_monthly) or ("quarterly" in kinds and is_quarter):
            allowed = True
        elif allow_weekly and not is_monthly and not is_quarter:
            allowed = True

        if allowed and low <= strike <= high:
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


def _is_multiple_of_five(value: float) -> bool:
    if value == 0:
        return False
    return abs((value / 5.0) - round(value / 5.0)) < 1e-6


def _select_strikes(
    strikes: Iterable[float],
    *,
    underlying_close: float,
    moneyness_pct: float,
    max_strikes_per_expiry: Optional[int],
) -> List[float]:
    """Prefer SecDef strikes that are 5-multiples and near spot; cap per-expiry."""
    strikes_all = sorted(float(s) for s in strikes if s is not None)
    if not strikes_all:
        return []

    low = underlying_close * (1.0 - moneyness_pct)
    high = underlying_close * (1.0 + moneyness_pct)

    in_range = [s for s in strikes_all if low <= s <= high]
    multiples = [s for s in in_range if _is_multiple_of_five(s)]

    candidates = multiples or in_range or strikes_all
    ordered = sorted(candidates, key=lambda s: abs(s - underlying_close))
    if max_strikes_per_expiry and max_strikes_per_expiry > 0:
        ordered = ordered[:max_strikes_per_expiry]
    return ordered


def _is_valid_far_expiry(d: date) -> bool:
    """Third Friday of Mar/Jun/Sep/Dec, accepting Thu/Fri/Sat encodings."""
    if d.month not in {1, 3, 6, 9, 12}:
        return False
    tf = third_friday(d.year, d.month)
    return d in {tf - timedelta(days=1), tf, tf + timedelta(days=1)}


def _select_expirations_spy_style(expirations: List[date], today: date) -> List[date]:
    """Mirror data_test/SPY_auto_collect.py expiry selection."""
    near = []
    far = []
    for d in sorted(expirations):
        days = (d - today).days
        if 0 <= days <= 30 and d.weekday() == 4:
            near.append(d)
        elif days > 30 and _is_valid_far_expiry(d):
            far.append(d)

    ordered = near + far
    seen: set[date] = set()
    dedup: List[date] = []
    for d in ordered:
        if d not in seen:
            dedup.append(d)
            seen.add(d)
        if len(dedup) >= 30:
            break
    return dedup


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
    filter_contracts: bool = True,
) -> List[Dict[str, Any]]:
    """Discover option contracts for *symbol* and cache results (SMART-only, 2025 flow).

    Implementation follows IB API v10.26+ guidance:
    - Use reqSecDefOptParams() to get expirations/strikes
    - Restrict discovery to SMART routing
    - Build Option contracts and batch-qualify via qualifyContracts
    - Do NOT call reqContractDetails per candidate
    """

    from ib_insync import Option  # type: ignore

    # Cache guardrails: discovery should only run when cache is allowed; avoids pulling
    # unexpected strikes intraday. Cache key = (symbol, trade_date).
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

    # 1) Fetch SecDef params and pick the richest SMART chain (qualifyContracts only, no reqContractDetails)
    try:
        params = _fetch_sec_def_opt_params(ib, symbol, underlying_conid or 0)
        logger.info(f"SecDef params fetched for {symbol}: {len(params)} chains")
    except Exception as exc:
        logger.error(
            "Failed to fetch SecDefOptParams after retries",
            extra={"symbol": symbol, "error": str(exc)},
        )
        raise

    allowed_exchange = (cfg.snapshot.exchange or "SMART").upper()
    best_overall = max(params, key=lambda p: len(p.strikes or []), default=None)
    best_tc = max(
        (p for p in params if (p.tradingClass or "").upper() == symbol.upper()),
        key=lambda p: len(p.strikes or []),
        default=None,
    )
    secdef = best_tc or None
    for p in params:
        exch = (p.exchange or "").upper()
        if exch == allowed_exchange:
            secdef = p
            break
    if secdef is None or (best_tc and len(best_tc.strikes or []) > len(secdef.strikes or [])):
        secdef = best_tc
    if secdef is None or (best_overall and len(best_overall.strikes or []) > len(secdef.strikes or [])):
        secdef = best_overall
    # No debug prints; selection is deterministic based on richest chain.
    if secdef is None:
        logger.warning(f"No suitable SecDef chain found for {symbol}")
        return []

    logger.info(f"Selected SecDef chain: exchange={secdef.exchange} tradingClass={secdef.tradingClass} strikes={len(secdef.strikes or [])} expirations={len(secdef.expirations or [])}")

    # 2) Build candidate grid (expiry x strike), apply scope filters (moneyness/expiry window)
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
    if filter_contracts:
        filtered_expiries = _select_expirations_spy_style(expirations, trade_date)
    else:
        filtered_expiries = sorted(expirations)
    
    logger.info(f"Expirations after filtering: {len(filtered_expiries)} (from {len(expirations)})")

    if not filtered_expiries or not strikes_all:
        logger.warning("No expirations or strikes left after filtering")
        return []
    strike_candidates = _select_strikes(
        strikes_all,
        underlying_close=underlying_close,
        moneyness_pct=cfg.filters.moneyness_pct,
        max_strikes_per_expiry=max_strikes_per_expiry,
    )
    
    logger.info(f"Strike candidates: {len(strike_candidates)} (from {len(strikes_all)})")

    if not strike_candidates:
        logger.warning("No strike candidates found")
        return []

    candidates: List[Dict[str, Any]] = []
    exchange = allowed_exchange
    trading_class = secdef.tradingClass or symbol
    multiplier = float(secdef.multiplier or 100)
    for expiry_date in filtered_expiries:
        iso_expiry = expiry_date.isoformat()
        for strike in strike_candidates:
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

    if filter_contracts:
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
    else:
        scoped_candidates = candidates

    if not scoped_candidates:
        logger.warning("No scoped candidates found")
        return []
    
    # 3) Build Option list (C/P) and batch-qualify; no per-contract details calls
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
    
    # Adaptive batch size based on total contract count
    # Smaller batches for small sets, larger for medium, capped for very large
    total_contracts = len(options)
    if total_contracts <= 25:
        CHUNK = total_contracts  # Process all at once for small sets
    elif total_contracts <= 100:
        CHUNK = 50  # Standard batch size
    elif total_contracts <= 500:
        CHUNK = 75  # Larger batches for medium sets
    else:
        CHUNK = 100  # Cap at 100 for very large sets to avoid timeouts
    
    logger.debug(
        f"Qualifying {total_contracts} contracts with batch size {CHUNK}",
        extra={"symbol": symbol, "total": total_contracts, "batch_size": CHUNK}
    )
    
    for i in range(0, len(options), CHUNK):
        chunk = options[i : i + CHUNK]
        try:
            # Optionally acquire token per chunk if provided; otherwise proceed immediately
            if acquire_token:
                acquire_token()
            qualified.extend(_qualify_contracts_chunk(ib, chunk))
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning(
                "qualifyContracts chunk failed after retries", extra={"size": len(chunk)}, exc_info=exc
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
