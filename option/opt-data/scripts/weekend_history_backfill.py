#!/usr/bin/env python3
"""
Weekend history backfill for option contracts.

Goal
----
Use contracts cache from the most recent trading day to batch-fetch historical bars
for all option contracts (hours stage) or active subset (minutes stage).

This is intended for weekend batch runs, outputting to data_test/ only.

Usage
-----
    # Hours stage: all contracts, 8 hours bars
    python scripts/weekend_history_backfill.py \
        --stage hours \
        --universe config/universe_history_202511.csv \
        --batch-count 8 --batch-index 0

    # Minutes stage: active subset, 30 mins bars
    python scripts/weekend_history_backfill.py \
        --stage minutes \
        --universe config/universe_history_202511.csv \
        --top-expiries 5 --strikes-per-side 3

Output
------
- Parquet bars: data_test/raw/ib/historical_bars_weekend/{SYMBOL}/{conId}/TRADES/{bar}.parquet
- Summary JSONL: state/run_logs/historical_backfill/summary_*.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

import pandas as pd
from ib_insync import IB, Option, RequestError, Stock  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opt_data.ib.historical_probe_utils import (  # noqa: E402
    sanitize_token,
    stable_batch_slice,
)
from opt_data.universe import load_universe  # noqa: E402
from opt_data.util.ratelimit import TokenBucket  # noqa: E402


NY_TZ = ZoneInfo("America/New_York")
logger = logging.getLogger("weekend_history_backfill")

# Bar sizes by stage
BAR_SIZES_HOURS = ["8 hours"]
BAR_SIZES_MINUTES = ["30 mins"]

# Duration by stage
DURATION_HOURS = "6 M"
DURATION_MINUTES = "1 M"


def _now_end_datetime_et() -> str:
    return datetime.now(tz=NY_TZ).strftime("%Y%m%d %H:%M:%S") + " US/Eastern"


def _normalize_bar_date(value: Any) -> date | datetime | None:  # noqa: ANN401
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if len(raw) >= 8:
            try:
                return datetime.strptime(raw[:8], "%Y%m%d").date()
            except ValueError:
                pass
        for fmt in ("%Y%m%d %H:%M:%S", "%Y%m%d  %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def _bars_to_frame(
    bars: Sequence[Any],  # noqa: ANN401
    *,
    symbol: str,
    conid: int,
    expiry: str,
    strike: float,
    right: str,
    bar_size: str,
    what_to_show: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for b in bars:
        rows.append(
            {
                "ts": getattr(b, "date", None),
                "open": getattr(b, "open", None),
                "high": getattr(b, "high", None),
                "low": getattr(b, "low", None),
                "close": getattr(b, "close", None),
                "volume": getattr(b, "volume", None),
                "barCount": getattr(b, "barCount", None),
                "average": getattr(b, "average", None),
                "symbol": symbol,
                "conid": conid,
                "expiry": expiry,
                "strike": strike,
                "right": right,
                "bar_size": bar_size,
                "what_to_show": what_to_show,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df


@dataclass(frozen=True)
class FetchSummary:
    symbol: str
    conid: int | None
    expiry: str | None
    strike: float | None
    right: str | None
    bar_size: str
    what_to_show: str
    duration: str
    bars: int
    first: str | None
    last: str | None
    elapsed_sec: float
    skipped: bool
    output_path: str | None
    error_code: int | None
    error_message: str | None

    def to_json(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "conid": self.conid,
            "expiry": self.expiry,
            "strike": self.strike,
            "right": self.right,
            "bar_size": self.bar_size,
            "what_to_show": self.what_to_show,
            "duration": self.duration,
            "bars": self.bars,
            "first": self.first,
            "last": self.last,
            "elapsed_sec": self.elapsed_sec,
            "skipped": self.skipped,
            "output_path": self.output_path,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


def load_latest_contracts_cache(symbol: str, cache_dir: Path) -> tuple[list[dict], str]:
    """Load contracts from the most recent cache file for a symbol.

    Returns:
        Tuple of (contracts list, cache date string)
    """
    pattern = f"{symbol}_*.json"
    files = sorted(cache_dir.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"No contracts cache found for {symbol} in {cache_dir}")

    # Extract date from filename: {SYMBOL}_{YYYY-MM-DD}.json
    cache_file = files[0]
    cache_date = cache_file.stem.split("_", 1)[-1] if "_" in cache_file.stem else "unknown"

    contracts = json.loads(cache_file.read_text(encoding="utf-8"))
    if not isinstance(contracts, list):
        raise ValueError(f"Contracts cache {cache_file} is not a list")

    return contracts, cache_date


def get_underlying_close(
    ib: IB,
    symbol: str,
    *,
    timeout: float = 20.0,
) -> float | None:
    """Fetch the most recent daily close price for an underlying."""
    stock = Stock(symbol, "SMART", "USD")
    try:
        qualified = ib.qualifyContracts(stock)
        if not qualified:
            logger.warning("Failed to qualify underlying %s", symbol)
            return None

        bars = ib.reqHistoricalData(
            stock,
            endDateTime="",
            durationStr="3 D",
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,
            formatDate=2,
            keepUpToDate=False,
            timeout=timeout,
        )
        if bars:
            return float(bars[-1].close)
    except Exception as exc:
        logger.warning("Failed to fetch underlying close for %s: %s", symbol, exc)
    return None


def filter_active_subset(
    contracts: list[dict],
    close_price: float,
    *,
    top_expiries: int = 5,
    strikes_per_side: int = 3,
) -> list[dict]:
    """Filter contracts to active subset based on near-ATM selection.

    Args:
        contracts: Full list of contracts from cache
        close_price: Underlying close price for ATM calculation
        top_expiries: Number of nearest expiries to include
        strikes_per_side: Number of strikes per side (C/P) per expiry

    Returns:
        Filtered list of contracts
    """
    # Group by expiry
    by_expiry: dict[str, list[dict]] = defaultdict(list)
    for c in contracts:
        exp = c.get("expiry", "")
        if exp:
            by_expiry[exp].append(c)

    # Take nearest E expiries
    sorted_expiries = sorted(by_expiry.keys())[:top_expiries]

    result: list[dict] = []
    seen_conids: set[int] = set()

    for exp in sorted_expiries:
        for right in ["C", "P"]:
            subset = [c for c in by_expiry[exp] if c.get("right") == right]
            # Sort by distance from ATM
            subset.sort(key=lambda c: abs(float(c.get("strike", 0)) - close_price))
            # Take top K
            for c in subset[:strikes_per_side]:
                conid = c.get("conid")
                if conid and conid not in seen_conids:
                    seen_conids.add(conid)
                    result.append(c)

    return result


def _iter_unique_symbols(entries: Any) -> list[str]:  # noqa: ANN401
    seen: set[str] = set()
    out: list[str] = []
    for e in entries:
        symbol = getattr(e, "symbol", None) or ""
        symbol_u = str(symbol).strip().upper()
        if not symbol_u or symbol_u in seen:
            continue
        seen.add(symbol_u)
        out.append(symbol_u)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Weekend history backfill for option contracts using contracts cache."
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=["hours", "minutes"],
        help="Which stage to run: hours (full contracts) or minutes (active subset)",
    )
    parser.add_argument(
        "--universe",
        type=Path,
        default=Path("config/universe.csv"),
        help="Universe CSV file",
    )
    parser.add_argument(
        "--symbols",
        default="",
        help="Comma-separated symbols (overrides --universe)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("state/contracts_cache"),
        help="Contracts cache directory",
    )
    parser.add_argument("--batch-index", type=int, default=0, help="0-based batch index")
    parser.add_argument("--batch-count", type=int, default=1, help="Total batches")
    parser.add_argument(
        "--top-expiries",
        type=int,
        default=5,
        help="[minutes stage] Number of nearest expiries to include",
    )
    parser.add_argument(
        "--strikes-per-side",
        type=int,
        default=3,
        help="[minutes stage] Strikes per side (C/P) per expiry",
    )
    parser.add_argument(
        "--what",
        default="TRADES",
        help="whatToShow for historical data",
    )
    parser.add_argument(
        "--use-rth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use regular trading hours only",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7496)
    parser.add_argument("--client-id", type=int, default=220)
    parser.add_argument("--connect-timeout-sec", type=float, default=8.0)
    parser.add_argument("--historical-timeout-sec", type=float, default=20.0)
    parser.add_argument(
        "--historical-per-minute",
        type=int,
        default=10,
        help="Token bucket refill rate for historical requests",
    )
    parser.add_argument(
        "--historical-burst",
        type=int,
        default=5,
        help="Token bucket burst capacity",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip contracts with existing output",
    )
    parser.add_argument(
        "--incremental",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "If output exists, fetch and append new bars (ts > max existing) and deduplicate "
            "by ts/conid/bar_size/what_to_show instead of skipping. "
            "Set --no-incremental to keep the old skip/overwrite behavior."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data_test/raw/ib/historical_bars_weekend"),
        help="Root directory for Parquet output",
    )
    parser.add_argument(
        "--summary-jsonl",
        type=Path,
        default=None,
        help="Summary JSONL path (default: auto-generated)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan only")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Determine symbols
    if args.symbols.strip():
        symbols_all = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols_all = _iter_unique_symbols(load_universe(args.universe))

    # Batch slice
    symbols = stable_batch_slice(
        symbols_all,
        batch_index=int(args.batch_index),
        batch_count=int(args.batch_count),
    )

    # Stage config
    if args.stage == "hours":
        bar_sizes = BAR_SIZES_HOURS
        duration = DURATION_HOURS
    else:
        bar_sizes = BAR_SIZES_MINUTES
        duration = DURATION_MINUTES

    logger.info(
        "Plan: stage=%s universe=%s symbols_total=%d batch=%d/%d symbols_batch=%d",
        args.stage,
        args.universe,
        len(symbols_all),
        int(args.batch_index) + 1,
        int(args.batch_count),
        len(symbols),
    )

    if args.dry_run:
        logger.info("Symbols in batch: %s", ", ".join(symbols))
        for sym in symbols[:3]:
            try:
                contracts, cache_date = load_latest_contracts_cache(sym, args.cache_dir)
                logger.info("  %s: %d contracts (cache: %s)", sym, len(contracts), cache_date)
            except FileNotFoundError as e:
                logger.warning("  %s: %s", sym, e)
        return

    # Setup run logs
    run_dir = Path("state/run_logs/historical_backfill")
    run_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(tz=ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    summary_path = (
        args.summary_jsonl
        if args.summary_jsonl
        else run_dir
        / f"summary_{args.stage}_b{args.batch_index}of{args.batch_count}_{run_id}.jsonl"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    # Rate limiter
    limiter = TokenBucket.create(
        capacity=int(args.historical_burst),
        refill_per_minute=int(args.historical_per_minute),
    )

    def acquire_token() -> None:
        while not limiter.try_acquire():
            time.sleep(0.5)

    # Connect to IB
    ib = IB()
    logger.info(
        "Connecting to IB: host=%s port=%s clientId=%s", args.host, args.port, args.client_id
    )
    try:
        ib.connect(
            args.host,
            args.port,
            clientId=args.client_id,
            timeout=float(args.connect_timeout_sec),
            readonly=False,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to connect to IB: {exc}")

    end_dt = _now_end_datetime_et()

    with summary_path.open("a", encoding="utf-8") as summary_fh:
        # Write metadata
        meta = {
            "meta": {
                "run_id": run_id,
                "stage": args.stage,
                "endDateTime": end_dt,
                "bar_sizes": bar_sizes,
                "duration": duration,
                "what_to_show": args.what,
                "use_rth": bool(args.use_rth),
                "cache_dir": str(args.cache_dir),
                "symbols_batch": symbols,
                "batch_index": int(args.batch_index),
                "batch_count": int(args.batch_count),
                "top_expiries": int(args.top_expiries),
                "strikes_per_side": int(args.strikes_per_side),
            }
        }
        summary_fh.write(json.dumps(meta) + "\n")
        summary_fh.flush()

        try:
            for idx, symbol in enumerate(symbols, start=1):
                logger.info("[%d/%d] Processing %s", idx, len(symbols), symbol)

                # Load contracts cache
                try:
                    contracts, cache_date = load_latest_contracts_cache(symbol, args.cache_dir)
                    logger.info("  Loaded %d contracts from cache %s", len(contracts), cache_date)
                except FileNotFoundError as e:
                    logger.error("  %s", e)
                    # Write failure for all bar sizes
                    for bar_size in bar_sizes:
                        summary = FetchSummary(
                            symbol=symbol,
                            conid=None,
                            expiry=None,
                            strike=None,
                            right=None,
                            bar_size=bar_size,
                            what_to_show=args.what,
                            duration=duration,
                            bars=0,
                            first=None,
                            last=None,
                            elapsed_sec=0.0,
                            skipped=False,
                            output_path=None,
                            error_code=None,
                            error_message=f"cache_not_found: {e}",
                        )
                        summary_fh.write(json.dumps(summary.to_json()) + "\n")
                    summary_fh.flush()
                    continue

                # For minutes stage, filter to active subset
                if args.stage == "minutes":
                    acquire_token()
                    close_price = get_underlying_close(
                        ib, symbol, timeout=args.historical_timeout_sec
                    )
                    if close_price is None:
                        logger.warning("  Could not get close price; using median strike")
                        strikes = sorted(
                            {float(c.get("strike", 0)) for c in contracts if c.get("strike")}
                        )
                        close_price = strikes[len(strikes) // 2] if strikes else 100.0

                    contracts = filter_active_subset(
                        contracts,
                        close_price,
                        top_expiries=int(args.top_expiries),
                        strikes_per_side=int(args.strikes_per_side),
                    )
                    logger.info(
                        "  Filtered to %d contracts (close=%.2f)",
                        len(contracts),
                        close_price,
                    )

                # Output directory
                symbol_dir = args.output_root / symbol
                symbol_dir.mkdir(parents=True, exist_ok=True)

                # Track statistics
                expired_count = 0
                processed_count = 0

                # Process each contract
                for c_idx, contract_dict in enumerate(contracts):
                    conid = int(contract_dict.get("conid", 0))
                    expiry = contract_dict.get("expiry", "")
                    strike = float(contract_dict.get("strike", 0))
                    right = contract_dict.get("right", "")
                    trading_class = contract_dict.get("tradingClass", "")
                    multiplier = contract_dict.get("multiplier", 100)

                    if not conid:
                        continue

                    # Skip expired contracts
                    try:
                        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                        today = datetime.now(tz=NY_TZ).date()
                        if expiry_date < today:
                            expired_count += 1
                            if c_idx < 5:
                                logger.debug(
                                    "  Skipping expired contract: conid=%s expiry=%s",
                                    conid,
                                    expiry,
                                )
                            continue
                    except (ValueError, AttributeError):
                        # If expiry parsing fails, skip the contract
                        logger.warning("  Invalid expiry format for conid=%s: %s", conid, expiry)
                        continue

                    # Build Option contract
                    option = Option(
                        symbol=symbol,
                        lastTradeDateOrContractMonth=expiry.replace("-", ""),
                        strike=strike,
                        right=right,
                        exchange="SMART",
                        currency="USD",
                        tradingClass=trading_class,
                        multiplier=str(multiplier),
                    )
                    option.conId = conid
                    option.includeExpired = True

                    contract_dir = symbol_dir / str(conid)
                    contract_dir.mkdir(parents=True, exist_ok=True)

                    for bar_size in bar_sizes:
                        bar_tok = sanitize_token(bar_size)
                        what_tok = sanitize_token(args.what.upper())
                        out_path = contract_dir / what_tok / f"{bar_tok}.parquet"
                        out_path.parent.mkdir(parents=True, exist_ok=True)

                        existing_df: pd.DataFrame | None = None
                        existing_max_ts: pd.Timestamp | None = None
                        existing_rows = 0
                        incremental_ready = True

                        # Incremental read (preferred default)
                        if bool(args.incremental) and out_path.exists():
                            try:
                                existing_df = pd.read_parquet(out_path)
                                existing_rows = len(existing_df)
                                if not existing_df.empty and "ts" in existing_df:
                                    existing_max_ts = existing_df["ts"].max()
                                logger.debug(
                                    "  incremental load: %s rows=%d max_ts=%s",
                                    out_path,
                                    existing_rows,
                                    existing_max_ts,
                                )
                                if not existing_df.empty and "ts" not in existing_df.columns:
                                    logger.warning(
                                        "  existing parquet missing ts column, disabling incremental merge: %s",
                                        out_path,
                                    )
                                    incremental_ready = False
                                    existing_df = None
                                    existing_max_ts = None
                            except Exception as exc:
                                logger.warning(
                                    "  failed to read existing parquet for incremental merge (%s): %s",
                                    out_path,
                                    exc,
                                )
                                existing_df = None
                                existing_max_ts = None
                                incremental_ready = False

                        # Legacy resume skip (only when incremental is disabled)
                        if (not bool(args.incremental)) and bool(args.resume) and out_path.exists():
                            summary = FetchSummary(
                                symbol=symbol,
                                conid=conid,
                                expiry=expiry,
                                strike=strike,
                                right=right,
                                bar_size=bar_size,
                                what_to_show=args.what,
                                duration=duration,
                                bars=0,
                                first=None,
                                last=None,
                                elapsed_sec=0.0,
                                skipped=True,
                                output_path=str(out_path),
                                error_code=None,
                                error_message=None,
                            )
                            summary_fh.write(json.dumps(summary.to_json()) + "\n")
                            continue

                        # Fetch historical data
                        acquire_token()
                        started = time.monotonic()
                        bars: list[Any] = []
                        err: Exception | None = None

                        try:
                            bars_raw = ib.reqHistoricalData(
                                option,
                                endDateTime=end_dt,
                                durationStr=duration,
                                barSizeSetting=bar_size,
                                whatToShow=args.what.upper(),
                                useRTH=bool(args.use_rth),
                                formatDate=2,
                                keepUpToDate=False,
                                timeout=float(args.historical_timeout_sec),
                            )
                            bars = list(bars_raw) if bars_raw else []
                        except RequestError as exc:
                            err = exc
                        except TimeoutError:
                            err = TimeoutError("Historical request timeout")
                        except Exception as exc:
                            err = exc

                        elapsed = time.monotonic() - started

                        # Parse first/last
                        first_raw = bars[0].date if bars else None
                        last_raw = bars[-1].date if bars else None
                        first = _normalize_bar_date(first_raw)
                        last = _normalize_bar_date(last_raw)
                        first_s = first.isoformat() if first else None
                        last_s = last.isoformat() if last else None

                        error_code = None
                        error_message = None
                        if err is not None:
                            error_code = getattr(err, "code", None)
                            error_message = str(err)

                        # Save bars (incremental append + dedup by ts/conid/bar_size/what_to_show)
                        saved_path: str | None = None
                        bars_written = 0
                        merged_first: str | None = None
                        merged_last: str | None = None

                        df_new = _bars_to_frame(
                            bars,
                            symbol=symbol,
                            conid=conid,
                            expiry=expiry,
                            strike=strike,
                            right=right,
                            bar_size=bar_size,
                            what_to_show=args.what,
                        )

                        if bool(args.incremental) and incremental_ready:
                            if existing_max_ts is not None and not df_new.empty:
                                df_new = df_new[df_new["ts"] > existing_max_ts]

                            frames: list[pd.DataFrame] = []
                            if existing_df is not None:
                                frames.append(existing_df)
                            if not df_new.empty:
                                frames.append(df_new)

                            if frames:
                                merged = pd.concat(frames, ignore_index=True)
                                merged = (
                                    merged.drop_duplicates(
                                        subset=["ts", "conid", "bar_size", "what_to_show"],
                                        keep="last",
                                    )
                                    .sort_values("ts")
                                )
                                merged_first = (
                                    merged["ts"].min().isoformat() if not merged.empty else None
                                )
                                merged_last = (
                                    merged["ts"].max().isoformat() if not merged.empty else None
                                )
                                bars_written = max(len(merged) - existing_rows, 0)
                                merged.to_parquet(out_path, index=False)
                                saved_path = str(out_path)
                        else:
                            if not df_new.empty:
                                df_new.to_parquet(out_path, index=False)
                                bars_written = len(df_new)
                                merged_first = df_new["ts"].min().isoformat()
                                merged_last = df_new["ts"].max().isoformat()
                                saved_path = str(out_path)

                        summary = FetchSummary(
                            symbol=symbol,
                            conid=conid,
                            expiry=expiry,
                            strike=strike,
                            right=right,
                            bar_size=bar_size,
                            what_to_show=args.what,
                            duration=duration,
                            bars=bars_written if bool(args.incremental) else len(bars),
                            first=merged_first or first_s,
                            last=merged_last or last_s,
                            elapsed_sec=float(elapsed),
                            skipped=False,
                            output_path=saved_path,
                            error_code=error_code,
                            error_message=error_message,
                        )
                        summary_fh.write(json.dumps(summary.to_json()) + "\n")

                        effective_bars = bars_written if bool(args.incremental) else len(bars)
                        status = "OK" if effective_bars else ("ERR" if err else "EMPTY")
                        if c_idx < 5 or (c_idx + 1) % 50 == 0:
                            logger.info(
                                "  [%d/%d] %-5s conid=%s %s bars=%d t=%.1fs",
                                c_idx + 1,
                                len(contracts),
                                status,
                                conid,
                                bar_size,
                                effective_bars,
                                elapsed,
                            )


                    summary_fh.flush()

                # Log summary for this symbol
                logger.info(
                    "  %s complete: %d contracts processed, %d expired (skipped)",
                    symbol,
                    len(contracts) - expired_count,
                    expired_count,
                )

        finally:
            logger.info("Disconnecting from IB")
            ib.disconnect()

    logger.info("Summary written: %s", summary_path)


if __name__ == "__main__":
    main()
