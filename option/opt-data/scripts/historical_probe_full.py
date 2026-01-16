#!/usr/bin/env python3
"""
Comprehensive historical option bar probe - tests ALL possible configurations.

Tests various combinations of:
- Bar sizes: 1 min, 5 mins, 15 mins, 30 mins, 1 hour, 1 day
- Data types: TRADES, MIDPOINT, BID_ASK, OPTION_IMPLIED_VOLATILITY, HISTORICAL_VOLATILITY
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

from ib_insync import IB, Option  # type: ignore


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


# ---- Fixed parameters -------------------------------------------------------
HOST = "127.0.0.1"
PORT = 7496
CLIENT_ID = 210  # Different client ID
SYMBOLS = ["AAPL"]
TRADE_DATE = "2025-12-18"
CONTRACTS_CACHE_ROOT = Path("state/contracts_cache")

# All configurations to test
BAR_SIZES = ["8 hours", "1 hour"]
WHAT_TO_SHOW_OPTIONS = ["MIDPOINT"]

DURATION_MAP = {
    "8 hours": "1 Y",
    "1 hour": "1 Y",
}

USE_RTH_OPTIONS = [True]
LIMIT_PER_SYMBOL = 1
THROTTLE_SEC = 0.35
OUTPUT_PATH = Path("state/run_logs/historical_probe_long.jsonl")

# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("historical_probe_full")


def make_throttle(min_interval_sec: float) -> callable:
    last_called = 0.0

    def wait() -> None:
        nonlocal last_called
        now = time.monotonic()
        delta = now - last_called
        if delta < min_interval_sec:
            time.sleep(min_interval_sec - delta)
        last_called = time.monotonic()

    return wait


def load_cache(cache_root: Path, symbol: str, trade_date: date) -> List[Dict[str, Any]]:
    path = (cache_root / f"{symbol.upper()}_{trade_date.isoformat()}.json").resolve()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read cache %s: %s", path, exc)
        return []


def choose_contracts(contracts: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    ordered = sorted(
        contracts,
        key=lambda c: (str(c.get("expiry", "")), float(c.get("strike", 0.0)), c.get("right", "")),
    )
    return ordered[:limit]


def build_option(contract: Dict[str, Any]) -> Option:
    expiry_raw = str(contract.get("expiry", "")).replace("-", "")
    opt = Option(
        contract.get("symbol", ""),
        expiry_raw,
        float(contract.get("strike", 0.0)),
        contract.get("right", "C"),
        contract.get("exchange") or "SMART",
        contract.get("currency") or "USD",
        contract.get("tradingClass"),
    )
    opt.includeExpired = True
    conid = contract.get("conid")
    if conid:
        opt.conId = int(conid)
    return opt


def fetch_bars(
    ib: IB,
    option: Option,
    *,
    what_to_show: str,
    duration: str,
    bar_size: str,
    end_date_time: str,
    use_rth: bool,
    throttle: callable,
) -> tuple[List[Any], str | None]:
    """Fetch historical bars and return (bars, error_message)."""
    throttle()
    try:
        bars = ib.reqHistoricalData(
            option,
            endDateTime=end_date_time,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=2,
            keepUpToDate=False,
        )
        if bars is None:
            return [], None
        try:
            result = list(bars)
            return result, None
        except TypeError:
            return [bars] if bars else [], None
    except Exception as exc:
        return [], str(exc)


def main() -> None:
    throttle = make_throttle(THROTTLE_SEC)
    results: List[Dict[str, Any]] = []
    trade_date = date.fromisoformat(TRADE_DATE)

    cache_root = CONTRACTS_CACHE_ROOT
    cache_root.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("COMPREHENSIVE IBKR HISTORICAL DATA PROBE")
    logger.info("=" * 80)
    logger.info(
        "Testing %d bar sizes x %d data types x %d RTH settings",
        len(BAR_SIZES),
        len(WHAT_TO_SHOW_OPTIONS),
        len(USE_RTH_OPTIONS),
    )

    ib = IB()
    try:
        logger.info("Connecting to IB at %s:%s clientId=%s", HOST, PORT, CLIENT_ID)
        ib.connect(HOST, PORT, clientId=CLIENT_ID, readonly=False)
    except Exception as exc:
        raise SystemExit(f"Failed to connect to IB: {exc}") from exc

    try:
        for symbol in SYMBOLS:
            cache = load_cache(cache_root, symbol, trade_date)
            if not cache:
                logger.error("Cache empty for %s %s", symbol, trade_date)
                continue

            selected = choose_contracts(cache, LIMIT_PER_SYMBOL)
            if not selected:
                logger.error("No contracts selected for %s", symbol)
                continue

            # Use first contract for testing
            contract = selected[0]
            option = build_option(contract)
            try:
                ib.qualifyContracts(option)
            except Exception as exc:
                logger.error("Failed to qualify contract: %s", exc)
                continue

            end_dt = f"{trade_date.strftime('%Y%m%d')} 23:59:59 US/Eastern"

            logger.info("-" * 80)
            logger.info(
                "Testing with contract: %s %s strike=%s %s",
                symbol,
                contract.get("expiry"),
                contract.get("strike"),
                contract.get("right"),
            )
            logger.info("-" * 80)

            for use_rth in USE_RTH_OPTIONS:
                rth_label = "RTH" if use_rth else "ETH"
                for bar_size in BAR_SIZES:
                    duration = DURATION_MAP.get(bar_size, "1 D")

                    for what in WHAT_TO_SHOW_OPTIONS:
                        bars, error = fetch_bars(
                            ib,
                            option,
                            what_to_show=what,
                            duration=duration,
                            bar_size=bar_size,
                            end_date_time=end_dt,
                            use_rth=use_rth,
                            throttle=throttle,
                        )

                        if bars:
                            logger.info("Sample bars:")
                            for b in bars[:5]:
                                logger.info(f"  {b.date} O={b.open} C={b.close}")
                            logger.info("  ...")
                            for b in bars[-5:]:
                                logger.info(f"  {b.date} O={b.open} C={b.close}")

                        bar_count = len(bars)
                        status = "✅" if bar_count > 0 else ("❌ ERROR" if error else "⚠️ EMPTY")

                        result = {
                            "symbol": symbol,
                            "conid": contract.get("conid"),
                            "bar_size": bar_size,
                            "what_to_show": what,
                            "use_rth": use_rth,
                            "duration": duration,
                            "bars": bar_count,
                            "status": "success"
                            if bar_count > 0
                            else ("error" if error else "empty"),
                            "error": error,
                            "first": bars[0].date if bars and hasattr(bars[0], "date") else None,
                            "last": bars[-1].date if bars and hasattr(bars[-1], "date") else None,
                        }
                        results.append(result)

                        error_msg = (
                            f" ({error[:50]}...)"
                            if error and len(error) > 50
                            else (f" ({error})" if error else "")
                        )
                        logger.info(
                            "%s | %-4s | %-8s | %-28s | bars=%3d%s",
                            status,
                            rth_label,
                            bar_size,
                            what,
                            bar_count,
                            error_msg,
                        )

    finally:
        logger.info("Disconnecting")
        ib.disconnect()

    # Write results
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        for item in results:
            fh.write(json.dumps(item, cls=DateTimeEncoder) + "\n")
    logger.info("Results written to %s", OUTPUT_PATH)

    # Summary table
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY TABLE")
    logger.info("=" * 80)

    # Build summary matrix
    summary = {}
    for r in results:
        key = (r["use_rth"], r["bar_size"], r["what_to_show"])
        summary[key] = r["bars"] > 0

    # Print header
    header = f"{'RTH':<4} | {'Bar Size':<12} | " + " | ".join(
        f"{w[:12]:<12}" for w in WHAT_TO_SHOW_OPTIONS
    )
    logger.info(header)
    logger.info("-" * len(header))

    # Print rows
    for use_rth in USE_RTH_OPTIONS:
        rth_label = "YES" if use_rth else "NO"
        for bar_size in BAR_SIZES:
            row = f"{rth_label:<4} | {bar_size:<12} | "
            cells = []
            for what in WHAT_TO_SHOW_OPTIONS:
                key = (use_rth, bar_size, what)
                status = "✅ YES" if summary.get(key, False) else "❌ NO"
                cells.append(f"{status:<12}")
            row += " | ".join(cells)
            logger.info(row)

    # Statistics
    success_count = sum(1 for r in results if r["bars"] > 0)
    total_count = len(results)
    logger.info("\n" + "=" * 80)
    logger.info(
        "TOTAL: %d/%d configurations returned data (%.1f%%)",
        success_count,
        total_count,
        100 * success_count / total_count if total_count else 0,
    )
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
