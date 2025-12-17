#!/usr/bin/env python3
"""
Universe quarterly option historical bars probe (staged).

Goal
----
Use a *representative* option contract per underlying (nearest quarterly expiry, ATM-ish strike)
to test/collect historical bars across bar sizes 1 minute .. 8 hours. This is intended as a
scalable "weekend probe/pull" harness: pick stage=hours vs stage=minutes, and slice the universe
into batches.

Notes
-----
- IBKR historical bars are requested per-contract; this script only orchestrates batching.
- Discovery uses reqSecDefOptParams(exchange="SMART") and qualifyContracts (no reqContractDetails).
- For options, prefer TRADES when you care about volume.

Output
------
- Writes a run summary JSONL under state/run_logs/historical_probe_universe/
- Optionally writes Parquet bars under data_test/raw/ib/historical_bars_quarterly/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo

import pandas as pd
from ib_insync import IB, Option, OptionChain, RequestError, Stock  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opt_data.ib.historical_probe_utils import (  # noqa: E402
    candidate_strikes,
    parse_yyyymmdd,
    pick_nearest_quarterly_expiry,
    sanitize_token,
    stable_batch_slice,
)
from opt_data.universe import load_universe  # noqa: E402
from opt_data.util.ratelimit import TokenBucket  # noqa: E402


NY_TZ = ZoneInfo("America/New_York")
logger = logging.getLogger("historical_probe_quarterly_universe_stage")


BAR_SIZES_MINUTES = ["1 min", "5 mins", "15 mins", "30 mins"]
BAR_SIZES_HOURS = ["1 hour", "2 hours", "4 hours", "8 hours"]
BAR_SIZES_ALL = [*BAR_SIZES_MINUTES, *BAR_SIZES_HOURS]


def _now_end_datetime_et() -> str:
    return datetime.now(tz=NY_TZ).strftime("%Y%m%d %H:%M:%S") + " US/Eastern"


def _choose_smart_chain(chains: Sequence[OptionChain], *, symbol: str) -> OptionChain:
    if not chains:
        raise RuntimeError("reqSecDefOptParams returned no chains")
    symbol_u = symbol.upper()
    smart = [c for c in chains if (c.exchange or "").upper() == "SMART"]
    if smart:
        exact_tc = [c for c in smart if (c.tradingClass or "").upper() == symbol_u]
        if exact_tc:
            return max(exact_tc, key=lambda c: len(c.strikes or []))
        return max(smart, key=lambda c: len(c.strikes or []))
    return max(chains, key=lambda c: len(c.strikes or []))


def _fetch_underlying_last_close(ib: IB, stock: Stock, *, timeout: float) -> float | None:
    try:
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
        bars_list = list(bars) if bars else []
        if bars_list:
            return float(bars_list[-1].close)
    except Exception as exc:
        logger.warning("Underlying daily historical fetch failed: %s", exc)
    return None


def _normalize_bar_date(value: Any) -> date | datetime | None:  # noqa: ANN401 - IB surface
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        parsed_date = parse_yyyymmdd(raw)
        if parsed_date is not None:
            return parsed_date
        for fmt in ("%Y%m%d %H:%M:%S", "%Y%m%d  %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def _duration_candidates(
    bar_size: str,
    *,
    duration_1m: str,
    duration_minutes: str,
    duration_hours: str,
) -> list[str]:
    if bar_size == "1 min":
        base = [duration_1m, "1 W"]
    elif bar_size in BAR_SIZES_MINUTES:
        base = [duration_minutes, "6 M", "3 M", "1 M", "1 W"]
    else:
        base = [duration_hours, "1 Y", "6 M", "3 M", "1 M", "1 W"]
    out: list[str] = []
    seen: set[str] = set()
    for d in base:
        d_norm = d.strip()
        if not d_norm or d_norm in seen:
            continue
        seen.add(d_norm)
        out.append(d_norm)
    return out


def _bars_to_frame(
    bars: Sequence[Any],  # noqa: ANN401 - IB surface
    *,
    symbol: str,
    option_conid: int,
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
                "option_conid": option_conid,
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
    option_conid: int | None
    bar_size: str
    what_to_show: str
    duration_requested: str
    duration_used: str | None
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
            "option_conid": self.option_conid,
            "bar_size": self.bar_size,
            "what_to_show": self.what_to_show,
            "duration_requested": self.duration_requested,
            "duration_used": self.duration_used,
            "bars": self.bars,
            "first": self.first,
            "last": self.last,
            "elapsed_sec": self.elapsed_sec,
            "skipped": self.skipped,
            "output_path": self.output_path,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


def _iter_unique_symbols(entries: Iterable[Any]) -> list[str]:  # noqa: ANN401 - supports UniverseEntry
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
        description="Probe/pull quarterly option historical bars for a universe in staged batches."
    )
    parser.add_argument(
        "--universe",
        type=Path,
        default=Path("config/universe.csv"),
        help="Universe CSV (symbol,conid) with optional # comments",
    )
    parser.add_argument(
        "--symbols",
        default="",
        help="Optional comma-separated symbols override (ignores --universe)",
    )
    parser.add_argument(
        "--stage",
        default="all",
        choices=["all", "minutes", "hours"],
        help="Which bar-size stage to run",
    )
    parser.add_argument(
        "--bar-size",
        action="append",
        default=[],
        help="Override barSizeSetting (repeatable). If provided, ignores --stage.",
    )
    parser.add_argument("--batch-index", type=int, default=0, help="0-based batch index")
    parser.add_argument("--batch-count", type=int, default=1, help="Total number of batches")
    parser.add_argument("--right", default="C", choices=["C", "P"])
    parser.add_argument(
        "--prefer-strike-step",
        type=float,
        default=5.0,
        help="Prefer strikes that are multiples of this step (0 disables)",
    )
    parser.add_argument("--max-strike-candidates", type=int, default=12)
    parser.add_argument(
        "--what",
        "--what-to-show",
        dest="what",
        action="append",
        default=None,
        help="whatToShow (repeatable). Default: TRADES",
    )
    parser.add_argument(
        "--use-rth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use regular trading hours (RTH) only",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    parser.add_argument("--client-id", type=int, default=210)
    parser.add_argument("--connect-timeout-sec", type=float, default=8.0)
    parser.add_argument("--connect-retries", type=int, default=2)
    parser.add_argument("--connect-retry-sleep-sec", type=float, default=1.0)
    parser.add_argument("--market-data-type", type=int, default=0)
    parser.add_argument("--historical-timeout-sec", type=float, default=20.0)
    parser.add_argument(
        "--max-duration-attempts",
        type=int,
        default=2,
        help="Max number of duration fallback attempts per (barSize, whatToShow). Set 1 to minimize requests.",
    )
    parser.add_argument(
        "--skip-underlying-close",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Skip the underlying daily close request (reduces 1 historical request per symbol); strike selection falls back to median strikes.",
    )
    parser.add_argument(
        "--discovery-per-minute",
        type=int,
        default=0,
        help="Optional token-bucket refill rate for discovery calls (0 disables)",
    )
    parser.add_argument(
        "--discovery-burst",
        type=int,
        default=0,
        help="Optional token-bucket burst capacity for discovery calls (0 disables)",
    )
    parser.add_argument(
        "--historical-per-minute",
        type=int,
        default=10,
        help="Token-bucket refill rate for historical requests",
    )
    parser.add_argument(
        "--historical-burst",
        type=int,
        default=5,
        help="Token-bucket burst capacity for historical requests",
    )
    parser.add_argument(
        "--duration-1m",
        default="1 M",
        help="Preferred duration for barSize='1 min' (safe default: 1 M)",
    )
    parser.add_argument(
        "--duration-minutes",
        default="6 M",
        help="Preferred duration for minute bars >=5 mins (fallback ladder applies)",
    )
    parser.add_argument(
        "--duration-hours",
        default="6 M",
        help="Preferred duration for hour bars (fallback ladder applies)",
    )
    parser.add_argument(
        "--write-bars",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write Parquet bars under --output-root",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip fetch if output parquet already exists",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data_test/raw/ib/historical_bars_quarterly"),
        help="Root directory for Parquet outputs (if --write-bars)",
    )
    parser.add_argument(
        "--summary-jsonl",
        type=Path,
        default=None,
        help="Optional JSONL path (default under state/run_logs/historical_probe_universe)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print symbol batch plan")
    parser.add_argument(
        "--reuse-probe",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reuse per-symbol probe contract from output-root (probe.json) when available",
    )
    parser.add_argument(
        "--log-ib-events",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write IB error/disconnect events into the summary JSONL (useful for diagnosing disconnects)",
    )
    args = parser.parse_args()
    if not args.what:
        args.what = ["TRADES"]

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.symbols.strip():
        symbols_all = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols_all = _iter_unique_symbols(load_universe(args.universe))

    symbols = stable_batch_slice(
        symbols_all,
        batch_index=int(args.batch_index),
        batch_count=int(args.batch_count),
    )

    if args.stage == "minutes":
        bar_sizes = BAR_SIZES_MINUTES
    elif args.stage == "hours":
        bar_sizes = BAR_SIZES_HOURS
    else:
        bar_sizes = BAR_SIZES_ALL

    if args.bar_size:
        requested = [str(b).strip() for b in args.bar_size if str(b).strip()]
        invalid = [b for b in requested if b not in BAR_SIZES_ALL]
        if invalid:
            raise SystemExit(f"--bar-size invalid values: {invalid!r}; allowed={BAR_SIZES_ALL!r}")
        bar_sizes = requested

    max_duration_attempts = int(args.max_duration_attempts)
    if max_duration_attempts <= 0:
        raise SystemExit("--max-duration-attempts must be positive")

    what_list: list[str] = []
    seen_what: set[str] = set()
    for w in args.what:
        w_norm = str(w).strip().upper()
        if not w_norm or w_norm in seen_what:
            continue
        seen_what.add(w_norm)
        what_list.append(w_norm)

    logger.info(
        "Plan: universe=%s symbols_total=%d stage=%s barsizes=%d batch=%d/%d symbols_batch=%d",
        args.universe,
        len(symbols_all),
        args.stage,
        len(bar_sizes),
        int(args.batch_index) + 1,
        int(args.batch_count),
        len(symbols),
    )
    if args.dry_run:
        logger.info("Symbols: %s", ", ".join(symbols))
        return

    asof_et = datetime.now(tz=NY_TZ).date()
    end_dt = _now_end_datetime_et()

    run_dir = Path("state/run_logs/historical_probe_universe")
    run_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(tz=ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    summary_path = (
        args.summary_jsonl
        if args.summary_jsonl is not None
        else run_dir / f"summary_quarterly_{args.stage}_b{args.batch_index}of{args.batch_count}_{run_id}.jsonl"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    limiter = TokenBucket.create(
        capacity=int(args.historical_burst),
        refill_per_minute=int(args.historical_per_minute),
    )

    def acquire_historical_token() -> None:
        while not limiter.try_acquire():
            time.sleep(0.5)

    discovery_limiter: TokenBucket | None = None
    if int(args.discovery_per_minute) > 0 and int(args.discovery_burst) > 0:
        discovery_limiter = TokenBucket.create(
            capacity=int(args.discovery_burst),
            refill_per_minute=int(args.discovery_per_minute),
        )

    def acquire_discovery_token() -> None:
        if discovery_limiter is None:
            return
        while not discovery_limiter.try_acquire():
            time.sleep(0.5)

    ib = IB()
    last_connect_error: Exception | None = None
    logger.info(
        "Connecting: host=%s port=%s clientId=%s timeout=%.1fs",
        args.host,
        args.port,
        args.client_id,
        float(args.connect_timeout_sec),
    )
    for attempt in range(int(args.connect_retries) + 1):
        try:
            ib.connect(
                args.host,
                args.port,
                clientId=args.client_id,
                timeout=float(args.connect_timeout_sec),
                readonly=False,
            )
            last_connect_error = None
            break
        except TimeoutError as exc:
            last_connect_error = exc
            if attempt < int(args.connect_retries):
                logger.warning(
                    "ib.connect timeout; retrying in %.1fs (attempt %d/%d)",
                    float(args.connect_retry_sleep_sec),
                    attempt + 1,
                    int(args.connect_retries),
                )
                time.sleep(float(args.connect_retry_sleep_sec))
                continue
            break
        except Exception as exc:
            last_connect_error = exc
            break

    if last_connect_error is not None:
        raise SystemExit(
            "Failed to connect to IB Gateway/TWS API. "
            f"(host={args.host} port={args.port} clientId={args.client_id} "
            f"timeout={args.connect_timeout_sec}s error={last_connect_error!r})"
        )

    if int(args.market_data_type) in {1, 2, 3, 4}:
        ib.reqMarketDataType(int(args.market_data_type))
        logger.info("marketDataType=%s", int(args.market_data_type))

    with summary_path.open("a", encoding="utf-8") as summary_fh:
        def _write_event(payload: dict[str, Any]) -> None:
            if summary_fh.closed:
                return
            try:
                summary_fh.write(json.dumps({"event": payload}) + "\n")
                summary_fh.flush()
            except ValueError:
                # Defensive: IB event callbacks can fire during shutdown.
                return

        def _on_error(req_id: int, error_code: int, error_string: str, contract: Any) -> None:  # noqa: ANN401
            _write_event(
                {
                    "type": "error",
                    "ts_utc": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
                    "req_id": req_id,
                    "error_code": error_code,
                    "error_string": error_string,
                    "contract": getattr(contract, "localSymbol", None)
                    or getattr(contract, "symbol", None)
                    or None,
                }
            )

        def _on_disconnected() -> None:
            _write_event(
                {
                    "type": "disconnected",
                    "ts_utc": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
                }
            )

        if bool(args.log_ib_events):
            ib.errorEvent += _on_error
            ib.disconnectedEvent += _on_disconnected

        def _write_symbol_failure(
            *,
            symbol: str,
            error_code: int | None,
            error_message: str,
        ) -> None:
            for bar_size in bar_sizes:
                for what in what_list:
                    duration_list = _duration_candidates(
                        bar_size,
                        duration_1m=str(args.duration_1m),
                        duration_minutes=str(args.duration_minutes),
                        duration_hours=str(args.duration_hours),
                    )[:max_duration_attempts]
                    summary = FetchSummary(
                        symbol=symbol,
                        option_conid=None,
                        bar_size=bar_size,
                        what_to_show=str(what).upper(),
                        duration_requested=duration_list[0] if duration_list else "",
                        duration_used=None,
                        bars=0,
                        first=None,
                        last=None,
                        elapsed_sec=0.0,
                        skipped=False,
                        output_path=None,
                        error_code=error_code,
                        error_message=error_message,
                    )
                    summary_fh.write(json.dumps(summary.to_json()) + "\n")
            summary_fh.flush()

        try:
            meta = {
                "meta": {
                    "run_id": run_id,
                    "asof_et": asof_et.isoformat(),
                    "endDateTime": end_dt,
                    "host": args.host,
                    "port": args.port,
                    "client_id": args.client_id,
                    "market_data_type": int(args.market_data_type),
                    "universe": str(args.universe),
                    "symbols_total": len(symbols_all),
                    "stage": args.stage,
                    "bar_sizes": bar_sizes,
                    "what_to_show": what_list,
                    "use_rth": bool(args.use_rth),
                    "prefer_strike_step": float(args.prefer_strike_step),
                    "discovery_per_minute": int(args.discovery_per_minute),
                    "discovery_burst": int(args.discovery_burst),
                    "historical_per_minute": int(args.historical_per_minute),
                    "historical_burst": int(args.historical_burst),
                    "duration_1m": args.duration_1m,
                    "duration_minutes": args.duration_minutes,
                    "duration_hours": args.duration_hours,
                    "batch_index": int(args.batch_index),
                    "batch_count": int(args.batch_count),
                    "symbols_batch": symbols,
                    "max_duration_attempts": max_duration_attempts,
                    "skip_underlying_close": bool(args.skip_underlying_close),
                }
            }
            summary_fh.write(json.dumps(meta) + "\n")
            summary_fh.flush()

            for idx, symbol in enumerate(symbols, start=1):
                logger.info("[%d/%d] Symbol=%s", idx, len(symbols), symbol)

                symbol_dir = args.output_root / symbol
                symbol_dir.mkdir(parents=True, exist_ok=True)
                probe_path = symbol_dir / "probe.json"

                option: Option | None = None
                expiry: str | None = None
                strike_used: float | None = None
                option_conid: int | None = None

                if bool(args.reuse_probe) and probe_path.exists():
                    try:
                        probe = json.loads(probe_path.read_text(encoding="utf-8"))
                        expiry = str(probe.get("selected_quarterly_expiry") or "").strip()
                        strike_used = float(probe.get("selected_strike") or 0.0)
                        right = str(probe.get("right") or "").strip().upper()
                        if right and right != str(args.right).strip().upper():
                            raise RuntimeError(
                                f"probe.json right mismatch: {right} != {str(args.right).strip().upper()}"
                            )
                        right = right or str(args.right).strip().upper()
                        option_conid = int(probe.get("option_conid") or 0) or None
                        trading_class = probe.get("option_trading_class") or probe.get(
                            "chain_trading_class"
                        )
                        multiplier = probe.get("option_multiplier") or probe.get("chain_multiplier")
                        if expiry and strike_used and option_conid:
                            option = Option(
                                symbol=symbol,
                                lastTradeDateOrContractMonth=expiry,
                                strike=float(strike_used),
                                right=right,
                                exchange="SMART",
                                currency="USD",
                                tradingClass=str(trading_class or ""),
                                multiplier=str(multiplier or ""),
                            )
                            option.conId = int(option_conid)
                            option.includeExpired = True
                            try:
                                acquire_discovery_token()
                                qualified = ib.qualifyContracts(option)
                                if not qualified or int(getattr(option, "conId", 0) or 0) <= 0:
                                    raise RuntimeError("qualifyContracts returned no qualified option")
                            except Exception:
                                option = None
                    except Exception as exc:
                        logger.warning("Failed to reuse probe.json; will re-select: %s", exc)
                        option = None

                if option is None:
                    stock = Stock(symbol, "SMART", "USD")
                    try:
                        acquire_discovery_token()
                        qualified = ib.qualifyContracts(stock)
                        if not qualified or int(getattr(stock, "conId", 0) or 0) <= 0:
                            raise RuntimeError("qualifyContracts returned no qualified underlying")
                    except Exception as exc:
                        code = getattr(exc, "code", None)
                        msg = getattr(exc, "message", None) or str(exc)
                        if code is None and "no qualified underlying" in msg:
                            code = 200
                        logger.error("Underlying qualify failed: %s", msg)
                        _write_symbol_failure(
                            symbol=symbol,
                            error_code=int(code) if code is not None else None,
                            error_message=f"underlying_qualify_failed: {msg}",
                        )
                        continue

                    try:
                        acquire_discovery_token()
                        chains = ib.reqSecDefOptParams(symbol, "", stock.secType, stock.conId)
                        chain = _choose_smart_chain(chains, symbol=symbol)
                    except Exception as exc:
                        code = getattr(exc, "code", None)
                        msg = getattr(exc, "message", None) or str(exc)
                        logger.error("reqSecDefOptParams failed: %s", msg)
                        _write_symbol_failure(
                            symbol=symbol,
                            error_code=int(code) if code is not None else None,
                            error_message=f"reqSecDefOptParams_failed: {msg}",
                        )
                        continue

                    try:
                        expiry = pick_nearest_quarterly_expiry(chain.expirations, asof=asof_et)
                    except Exception as exc:
                        msg = str(exc)
                        logger.error("Pick quarterly expiry failed: %s", msg)
                        _write_symbol_failure(
                            symbol=symbol,
                            error_code=None,
                            error_message=f"pick_quarterly_expiry_failed: {msg}",
                        )
                        continue

                    ref_close: float | None = None
                    if not bool(args.skip_underlying_close):
                        acquire_historical_token()
                        ref_close = _fetch_underlying_last_close(
                            ib, stock, timeout=float(args.historical_timeout_sec)
                        )
                    if ref_close is None:
                        if bool(args.skip_underlying_close):
                            logger.debug(
                                "Underlying close unavailable (skipped); strike selection uses median strike"
                            )
                        else:
                            logger.warning(
                                "Underlying close unavailable; strike selection uses median strike"
                            )

                    strikes = candidate_strikes(
                        chain.strikes,
                        reference_price=ref_close,
                        prefer_step=float(args.prefer_strike_step),
                    )
                    if not strikes:
                        logger.error("No strikes returned by reqSecDefOptParams")
                        _write_symbol_failure(
                            symbol=symbol,
                            error_code=None,
                            error_message="no_strikes_from_reqSecDefOptParams",
                        )
                        continue

                    last_qualify_error: str | None = None

                    for strike in strikes[: int(args.max_strike_candidates)]:
                        candidate = Option(
                            symbol=symbol,
                            lastTradeDateOrContractMonth=expiry,
                            strike=float(strike),
                            right=str(args.right).upper(),
                            exchange="SMART",
                            currency="USD",
                            multiplier=str(chain.multiplier or ""),
                            tradingClass=str(chain.tradingClass or ""),
                        )
                        candidate.includeExpired = True
                        try:
                            acquire_discovery_token()
                            qualified = ib.qualifyContracts(candidate)
                            if not qualified or int(getattr(candidate, "conId", 0) or 0) <= 0:
                                last_qualify_error = "qualifyContracts returned no qualified option"
                                continue
                            option = candidate
                            strike_used = float(strike)
                            break
                        except RequestError as exc:
                            last_qualify_error = f"{exc.code}: {exc.message}"
                            continue
                        except Exception as exc:
                            last_qualify_error = str(exc)
                            continue

                    if option is None or strike_used is None:
                        logger.error(
                            "No probe option qualified (tried %d strikes); last_error=%s",
                            int(args.max_strike_candidates),
                            last_qualify_error,
                        )
                        _write_symbol_failure(
                            symbol=symbol,
                            error_code=200
                            if last_qualify_error
                            and (
                                last_qualify_error.startswith("200:")
                                or "no qualified option" in last_qualify_error
                                or "qualifyContracts returned no qualified option" in last_qualify_error
                            )
                            else None,
                            error_message=f"no_probe_option_qualified: {last_qualify_error or 'unknown'}",
                        )
                        continue

                    option_conid = int(getattr(option, "conId", 0) or 0) or None
                    if option_conid is None:
                        logger.error("Qualified option missing conId")
                        _write_symbol_failure(
                            symbol=symbol,
                            error_code=None,
                            error_message="qualified_option_missing_conId",
                        )
                        continue

                    probe_path.write_text(
                        json.dumps(
                            {
                                "symbol": symbol,
                                "asof_et": asof_et.isoformat(),
                                "endDateTime": end_dt,
                                "underlying_conid": int(getattr(stock, "conId", 0) or 0),
                                "reference_close": ref_close,
                                "selected_quarterly_expiry": expiry,
                                "selected_strike": strike_used,
                                "right": str(args.right).upper(),
                                "option_conid": int(option_conid),
                                "option_trading_class": getattr(option, "tradingClass", None),
                                "option_multiplier": getattr(option, "multiplier", None),
                                "chain_exchange": getattr(chain, "exchange", None),
                                "chain_trading_class": getattr(chain, "tradingClass", None),
                                "chain_multiplier": getattr(chain, "multiplier", None),
                            },
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

                assert expiry is not None and strike_used is not None and option_conid is not None

                logger.info(
                    "Probe contract: %s %s %s %.2f conId=%s",
                    symbol,
                    expiry,
                    getattr(option, "right", str(args.right)).upper(),
                    float(strike_used),
                    int(option_conid),
                )

                contract_dir = symbol_dir / str(option_conid)
                contract_dir.mkdir(parents=True, exist_ok=True)

                for bar_size in bar_sizes:
                    for what in what_list:
                        duration_list = _duration_candidates(
                            bar_size,
                            duration_1m=str(args.duration_1m),
                            duration_minutes=str(args.duration_minutes),
                            duration_hours=str(args.duration_hours),
                        )[:max_duration_attempts]

                        out_path: Path | None = None
                        if bool(args.write_bars):
                            bar_tok = sanitize_token(bar_size)
                            what_tok = sanitize_token(str(what).upper())
                            out_path = contract_dir / what_tok / f"{bar_tok}.parquet"
                            out_path.parent.mkdir(parents=True, exist_ok=True)
                            if bool(args.resume) and out_path.exists():
                                summary = FetchSummary(
                                    symbol=symbol,
                                    option_conid=option_conid,
                                    bar_size=bar_size,
                                    what_to_show=str(what).upper(),
                                    duration_requested=duration_list[0] if duration_list else "",
                                    duration_used=None,
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
                                summary_fh.flush()
                                logger.info(
                                    "SKIP   | %-8s | %-8s | %s",
                                    bar_size,
                                    str(what).upper(),
                                    out_path,
                                )
                                continue

                        bars: list[Any] = []
                        used_duration: str | None = None
                        err: RequestError | None = None
                        elapsed = 0.0

                        for duration in duration_list:
                            acquire_historical_token()
                            started = time.monotonic()
                            try:
                                bars_raw = ib.reqHistoricalData(
                                    option,
                                    endDateTime=end_dt,
                                    durationStr=duration,
                                    barSizeSetting=bar_size,
                                    whatToShow=str(what).upper(),
                                    useRTH=bool(args.use_rth),
                                    formatDate=2,
                                    keepUpToDate=False,
                                    timeout=float(args.historical_timeout_sec),
                                )
                                bars = list(bars_raw) if bars_raw else []
                                elapsed = time.monotonic() - started
                                err = None
                            except RequestError as exc:
                                elapsed = time.monotonic() - started
                                err = exc
                                bars = []
                            except TimeoutError:
                                elapsed = time.monotonic() - started
                                err = RequestError(-1, 1100, "timeout")
                                bars = []
                            except Exception as exc:
                                elapsed = time.monotonic() - started
                                err = RequestError(-1, -1, str(exc))
                                bars = []

                            if bars:
                                used_duration = duration
                                break

                        first_raw = bars[0].date if bars and hasattr(bars[0], "date") else None
                        last_raw = bars[-1].date if bars and hasattr(bars[-1], "date") else None
                        first = _normalize_bar_date(first_raw)
                        last = _normalize_bar_date(last_raw)
                        first_s = first.isoformat() if first else None
                        last_s = last.isoformat() if last else None

                        error_code = None
                        error_message = None
                        if err is not None:
                            error_code = int(getattr(err, "code", None) or 0) or None
                            error_message = str(getattr(err, "message", None) or str(err)) or None

                        saved_path: str | None = None
                        if bool(args.write_bars) and out_path is not None and bars:
                            df = _bars_to_frame(
                                bars,
                                symbol=symbol,
                                option_conid=option_conid,
                                expiry=expiry,
                                strike=float(strike_used),
                                right=getattr(option, "right", str(args.right)).upper(),
                                bar_size=bar_size,
                                what_to_show=str(what).upper(),
                            )
                            df.to_parquet(out_path, index=False)
                            saved_path = str(out_path)

                        summary = FetchSummary(
                            symbol=symbol,
                            option_conid=option_conid,
                            bar_size=bar_size,
                            what_to_show=str(what).upper(),
                            duration_requested=duration_list[0] if duration_list else "",
                            duration_used=used_duration,
                            bars=len(bars),
                            first=first_s,
                            last=last_s,
                            elapsed_sec=float(elapsed),
                            skipped=False,
                            output_path=saved_path,
                            error_code=error_code,
                            error_message=error_message,
                        )
                        summary_fh.write(json.dumps(summary.to_json()) + "\n")
                        summary_fh.flush()

                        status = "OK" if bars else ("ERR" if err is not None else "EMPTY")
                        logger.info(
                            "%-5s | %-8s | %-6s | dur=%-4s | bars=%5d | t=%.2fs | first=%s | last=%s",
                            status,
                            bar_size,
                            str(what).upper(),
                            used_duration or "-",
                            len(bars),
                            float(elapsed),
                            first_s,
                            last_s,
                        )
        finally:
            if bool(args.log_ib_events):
                ib.errorEvent -= _on_error
                ib.disconnectedEvent -= _on_disconnected
            logger.info("Disconnecting")
            ib.disconnect()

    logger.info("Summary written: %s", summary_path)


if __name__ == "__main__":
    main()
