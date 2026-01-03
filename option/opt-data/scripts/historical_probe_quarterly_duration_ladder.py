#!/usr/bin/env python3
"""
Historical option bars probe (duration ladder) using the nearest quarterly expiry.

Goal
----
Empirically test how far back IBKR historical bars can be requested (durationStr ladder)
for option contracts across bar sizes from 1 minute to 8 hours.

Method
------
1) Discover option chain via reqSecDefOptParams(exchange="SMART") for the underlying.
2) Pick the nearest quarterly expiry (Mar/Jun/Sep/Dec, 3rd Friday family ±1 day).
3) Pick an ATM-ish strike using the underlying last close (fallback to median strike).
4) Qualify the option, then probe reqHistoricalData across:
   - barSizeSetting: 1 min .. 8 hours
   - whatToShow: includes TRADES (and MIDPOINT by default)
   - durationStr ladder: 1 W → 1 M → 6 M → 1 Y → 2 Y → 3 Y → 5 Y

Output
------
Writes JSONL to state/run_logs/historical_probe_duration_ladder/ and prints a summary table.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from ib_insync import IB, Option, OptionChain, RequestError, Stock  # type: ignore

NY_TZ = ZoneInfo("America/New_York")


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:  # noqa: ANN401 - JSON encoder API
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


BAR_SIZES_DEFAULT = [
    "1 min",
    "5 mins",
    "15 mins",
    "30 mins",
    "1 hour",
    "2 hours",
    "4 hours",
    "8 hours",
]

# Must include TRADES; keep MIDPOINT for comparison (useful when TRADES is sparse).
WHAT_TO_SHOW_DEFAULT = [
    "TRADES",
    "MIDPOINT",
]

DURATION_LADDER_DEFAULT = [
    "1 W",
    "1 M",
    "6 M",
    "1 Y",
    "2 Y",
    "3 Y",
    "5 Y",
]


logger = logging.getLogger("historical_probe_quarterly_duration_ladder")


def _third_friday(year: int, month: int) -> date:
    first_day = date(year, month, 1)
    # Monday=0 ... Sunday=6; Friday=4.
    days_until_friday = (4 - first_day.weekday()) % 7
    first_friday = first_day + timedelta(days=days_until_friday)
    return first_friday + timedelta(days=14)


def _is_third_friday_family(d: date) -> bool:
    third_friday = _third_friday(d.year, d.month)
    return abs((d - third_friday).days) <= 1


def _parse_yyyymmdd(value: str) -> date | None:
    raw = value.strip().replace("-", "")
    if len(raw) != 8 or not raw.isdigit():
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None


def _normalize_bar_date(value: Any) -> date | datetime | None:  # noqa: ANN401 - IB/ib_insync type surface
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        parsed_date = _parse_yyyymmdd(raw)
        if parsed_date is not None:
            return parsed_date
        for fmt in ("%Y%m%d %H:%M:%S", "%Y%m%d  %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def _pick_nearest_quarterly_expiry(expirations: Sequence[str], *, asof: date) -> str:
    quarter_months = {3, 6, 9, 12}
    candidates: list[tuple[date, str]] = []
    for exp in expirations:
        exp_date = _parse_yyyymmdd(exp)
        if exp_date is None:
            continue
        if exp_date < asof:
            continue
        if exp_date.month not in quarter_months:
            continue
        if not _is_third_friday_family(exp_date):
            continue
        candidates.append((exp_date, exp_date.strftime("%Y%m%d")))

    if not candidates:
        preview = ", ".join(sorted(expirations)[:10])
        raise RuntimeError(
            f"No quarterly expiries found (asof={asof.isoformat()}); expirations(head)=[{preview}]"
        )
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _choose_smart_chain(chains: Sequence[OptionChain], *, symbol: str) -> OptionChain:
    smart = [c for c in chains if str(getattr(c, "exchange", "")).upper() == "SMART"]
    if not smart:
        raise RuntimeError("reqSecDefOptParams returned no SMART chains")
    for chain in smart:
        if str(chain.tradingClass).upper() == symbol.upper():
            return chain
    return max(smart, key=lambda c: len(c.expirations))


def _fetch_underlying_last_close(ib: IB, stock: Stock) -> float | None:
    try:
        bars = ib.reqHistoricalData(
            stock,
            endDateTime="",
            durationStr="1 W",
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,
            formatDate=2,
            keepUpToDate=False,
        )
        bars_list = list(bars) if bars is not None else []
        if bars_list:
            return float(bars_list[-1].close)
    except RequestError as exc:
        logger.warning("Underlying daily historical fetch failed (%s): %s", exc.code, exc.message)
    except Exception as exc:
        logger.warning("Underlying daily historical fetch failed: %s", exc)
    return None


def _is_multiple_of(value: float, step: float, *, tol: float = 1e-6) -> bool:
    if step <= 0:
        return False
    quotient = value / step
    return abs(quotient - round(quotient)) < tol


def _candidate_strikes(
    strikes: Sequence[float],
    *,
    reference_price: float | None,
    prefer_step: float | None,
) -> list[float]:
    unique = sorted({float(s) for s in strikes if float(s) > 0})
    if not unique:
        return []

    ref = reference_price
    if ref is None:
        ref = unique[len(unique) // 2]

    if prefer_step is None or prefer_step <= 0:
        return sorted(unique, key=lambda s: (abs(s - ref), s))

    return sorted(
        unique,
        key=lambda s: (0 if _is_multiple_of(s, prefer_step) else 1, abs(s - ref), s),
    )


def _classify_request_error(exc: RequestError) -> str:
    msg = (exc.message or "").lower()
    if exc.code == 162:
        return "duration_limit"
    if exc.code == 1100:
        return "timeout"
    if "pacing violation" in msg:
        return "pacing"
    if "requesting too much data" in msg or "please retry with shorter duration" in msg:
        return "duration_limit"
    if "no data" in msg or "returned no data" in msg:
        return "no_data"
    return "other"


@dataclass(frozen=True)
class ProbeResult:
    bar_size: str
    what_to_show: str
    duration: str
    use_rth: bool
    bars: int
    first: date | datetime | None
    last: date | datetime | None
    error_code: int | None
    error_message: str | None
    error_class: str | None

    def to_json(self) -> dict[str, Any]:
        return {
            "bar_size": self.bar_size,
            "what_to_show": self.what_to_show,
            "duration": self.duration,
            "use_rth": self.use_rth,
            "bars": self.bars,
            "first": self.first,
            "last": self.last,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_class": self.error_class,
        }


def _make_throttle(min_interval_sec: float) -> callable:
    last_called = 0.0

    def wait() -> None:
        nonlocal last_called
        now = time.monotonic()
        delta = now - last_called
        if delta < min_interval_sec:
            time.sleep(min_interval_sec - delta)
        last_called = time.monotonic()

    return wait


def _fetch_bars(
    ib: IB,
    option: Option,
    *,
    what_to_show: str,
    duration: str,
    bar_size: str,
    end_date_time: str,
    use_rth: bool,
    throttle: callable,
    max_retries: int,
    pacing_sleep_sec: float,
    historical_timeout_sec: float,
) -> tuple[list[Any], RequestError | None]:
    for attempt in range(max_retries + 1):
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
                timeout=historical_timeout_sec,
            )
            return (list(bars) if bars is not None else []), None
        except RequestError as exc:
            if _classify_request_error(exc) == "pacing" and attempt < max_retries:
                sleep_for = pacing_sleep_sec * (2**attempt)
                logger.warning(
                    "Pacing violation; retrying after %.1fs (attempt %d/%d)",
                    sleep_for,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(sleep_for)
                continue
            return [], exc
        except TimeoutError:
            return [], RequestError(-1, 1100, "timeout")
        except Exception as exc:
            return [], RequestError(-1, -1, str(exc))
    return [], RequestError(-1, -1, "unreachable")


def _summarize(
    results: Sequence[ProbeResult],
    *,
    bar_sizes: Sequence[str],
    what_to_show_list: Sequence[str],
    duration_ladder: Sequence[str],
) -> None:
    duration_rank = {d: idx for idx, d in enumerate(duration_ladder)}

    logger.info("\n" + "=" * 120)
    logger.info("SUMMARY (per barSize/whatToShow)")
    logger.info("=" * 120)

    header = (
        f"{'BarSize':<10} | {'What':<9} | {'MaxOK':<5} | {'Earliest':<25} | {'Latest':<25} | "
        f"{'SpanDays':<7} | {'LimitAt':<7}"
    )
    logger.info(header)
    logger.info("-" * len(header))

    def _as_dt(v: date | datetime | None) -> datetime | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            if v.tzinfo is not None:
                return v.astimezone(NY_TZ).replace(tzinfo=None)
            return v
        return datetime(v.year, v.month, v.day)

    for bar_size in bar_sizes:
        for what in what_to_show_list:
            group = [r for r in results if r.bar_size == bar_size and r.what_to_show == what]
            ok = [r for r in group if r.bars > 0]

            limit_at = next((r.duration for r in group if r.error_class == "duration_limit"), None)

            if not ok:
                logger.info(
                    f"{bar_size:<10} | {what:<9} | {'-':<5} | {'(no bars)':<25} | {'-':<25} | {'-':<7} | {limit_at or '-':<7}"
                )
                continue

            max_ok = max(ok, key=lambda r: duration_rank.get(r.duration, -1))
            earliest = min(ok, key=lambda r: _as_dt(r.first) or datetime.max)
            latest = max(ok, key=lambda r: _as_dt(r.last) or datetime.min)

            first_dt = _as_dt(earliest.first)
            last_dt = _as_dt(latest.last)
            span_days = (last_dt - first_dt).days if first_dt and last_dt else None

            earliest_s = (earliest.first.isoformat() if earliest.first else "-")[:25]
            latest_s = (latest.last.isoformat() if latest.last else "-")[:25]
            logger.info(
                f"{bar_size:<10} | {what:<9} | {max_ok.duration:<5} | {earliest_s:<25} | {latest_s:<25} | {str(span_days) if span_days is not None else '-':<7} | {limit_at or '-':<7}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe option historical bars duration ladder for 1min..8h using nearest quarterly."
    )
    parser.add_argument("--symbol", default=os.getenv("SYMBOL", "AAPL"))
    parser.add_argument("--right", default=os.getenv("RIGHT", "C"), choices=["C", "P"])
    parser.add_argument(
        "--expiry",
        default=os.getenv("EXPIRY"),
        help="Optional expiry override (YYYYMMDD). If omitted, uses the nearest quarterly expiry.",
    )
    parser.add_argument(
        "--strike",
        type=float,
        default=(float(os.getenv("STRIKE")) if os.getenv("STRIKE") else None),
        help="Optional fixed strike for the probe contract (fallback to nearest available if not found/qualifiable unless --strict-strike)",
    )
    parser.add_argument(
        "--strict-strike",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fail if the requested --strike cannot be qualified for the selected expiry",
    )
    parser.add_argument("--host", default=os.getenv("IB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("IB_PORT", "4001")))
    parser.add_argument("--client-id", type=int, default=int(os.getenv("IB_CLIENT_ID", "210")))
    parser.add_argument(
        "--connect-timeout-sec",
        type=float,
        default=float(os.getenv("IB_CONNECT_TIMEOUT_SEC", "8")),
        help="Timeout for IB API handshake (ib.connect timeout)",
    )
    parser.add_argument(
        "--connect-retries",
        type=int,
        default=int(os.getenv("IB_CONNECT_RETRIES", "2")),
        help="Number of retries if ib.connect times out",
    )
    parser.add_argument(
        "--connect-retry-sleep-sec",
        type=float,
        default=float(os.getenv("IB_CONNECT_RETRY_SLEEP_SEC", "1.0")),
        help="Sleep between connect retries",
    )
    parser.add_argument(
        "--market-data-type", type=int, default=int(os.getenv("IB_MARKET_DATA_TYPE", "0"))
    )
    parser.add_argument(
        "--use-rth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use regular trading hours (RTH) only",
    )
    parser.add_argument(
        "--throttle-sec", type=float, default=float(os.getenv("THROTTLE_SEC", "0.35"))
    )
    parser.add_argument(
        "--prefer-strike-step",
        type=float,
        default=float(os.getenv("PREFER_STRIKE_STEP", "5")),
        help="Prefer strikes that are multiples of this step (0 disables)",
    )
    parser.add_argument("--max-strike-candidates", type=int, default=12)
    parser.add_argument(
        "--historical-timeout-sec",
        type=float,
        default=float(os.getenv("HISTORICAL_TIMEOUT_SEC", "20")),
        help="Per-request timeout for reqHistoricalData",
    )
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--pacing-sleep-sec", type=float, default=2.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    symbol = str(args.symbol).upper()
    right = str(args.right).upper()
    throttle = _make_throttle(args.throttle_sec)

    end_dt = datetime.now(tz=NY_TZ).strftime("%Y%m%d %H:%M:%S") + " US/Eastern"
    asof_et = datetime.now(tz=NY_TZ).date()

    out_dir = Path("state/run_logs/historical_probe_duration_ladder")
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(tz=NY_TZ).strftime("%Y%m%dT%H%M%S")
    out_path = out_dir / f"duration_ladder_{symbol}_{run_id}.jsonl"

    ib = IB()
    logger.info(
        "Connecting: host=%s port=%s clientId=%s timeout=%.1fs",
        args.host,
        args.port,
        args.client_id,
        float(args.connect_timeout_sec),
    )

    last_connect_error: Exception | None = None
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
            "Check that Gateway is logged in, API is enabled, the port matches, "
            "127.0.0.1 is trusted, and try a different clientId. "
            f"(host={args.host} port={args.port} clientId={args.client_id} "
            f"timeout={args.connect_timeout_sec}s error={last_connect_error!r})"
        )

    try:
        if args.market_data_type in {1, 2, 3, 4}:
            ib.reqMarketDataType(args.market_data_type)
            logger.info("marketDataType=%s", args.market_data_type)

        stock = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(stock)
        logger.info("Underlying qualified: %s conId=%s", stock.localSymbol or symbol, stock.conId)

        chains = ib.reqSecDefOptParams(symbol, "", stock.secType, stock.conId)
        chain = _choose_smart_chain(chains, symbol=symbol)
        expiry_override = str(args.expiry).strip() if args.expiry else None
        if expiry_override:
            expiry_override = expiry_override.replace("-", "")
            if _parse_yyyymmdd(expiry_override) is None:
                raise RuntimeError(f"Invalid --expiry (expect YYYYMMDD): {args.expiry!r}")
            if expiry_override not in {e.replace("-", "") for e in chain.expirations}:
                raise RuntimeError(f"--expiry {expiry_override} not found in secdef expirations")
            expiry = expiry_override
        else:
            expiry = _pick_nearest_quarterly_expiry(chain.expirations, asof=asof_et)
        logger.info(
            "Selected chain: exchange=%s tradingClass=%s multiplier=%s expiries=%d strikes=%d",
            chain.exchange,
            chain.tradingClass,
            chain.multiplier,
            len(chain.expirations),
            len(chain.strikes),
        )
        logger.info("Selected quarterly expiry: %s (asof=%s)", expiry, asof_et.isoformat())

        ref_price = _fetch_underlying_last_close(ib, stock)
        if ref_price is not None:
            logger.info("Underlying last close (1d): %.4f", ref_price)
        else:
            logger.warning("Underlying last close unavailable; falling back to median strike")

        strike_requested = float(args.strike) if args.strike is not None else None
        strikes = _candidate_strikes(
            chain.strikes,
            reference_price=(strike_requested if strike_requested is not None else ref_price),
            prefer_step=float(args.prefer_strike_step),
        )
        if not strikes:
            raise RuntimeError("No strikes returned by reqSecDefOptParams")

        option: Option | None = None
        strike_used: float | None = None
        last_qualify_error: str | None = None

        if strike_requested is not None:
            logger.info(
                "Requested strike override: %.2f (strict=%s)", strike_requested, args.strict_strike
            )

        strike_candidates: list[float] = []
        if strike_requested is not None:
            strike_candidates.append(float(strike_requested))
        if strike_requested is None or not bool(args.strict_strike):
            strike_candidates.extend(float(s) for s in strikes)

        deduped: list[float] = []
        seen: set[float] = set()
        for s in strike_candidates:
            key = round(float(s), 6)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(float(s))

        for strike in deduped[: args.max_strike_candidates]:
            candidate = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiry,
                strike=float(strike),
                right=right,
                exchange="SMART",
                currency="USD",
                multiplier=str(chain.multiplier or ""),
                tradingClass=str(chain.tradingClass or ""),
            )
            candidate.includeExpired = True
            try:
                ib.qualifyContracts(candidate)
                option = candidate
                strike_used = float(strike)
                break
            except RequestError as exc:
                last_qualify_error = f"{exc.code}: {exc.message}"
                continue
            except Exception as exc:
                last_qualify_error = str(exc)
                continue

        if option is None:
            raise RuntimeError(
                f"Failed to qualify any strike (tried {args.max_strike_candidates}); last_error={last_qualify_error}"
            )

        logger.info(
            "Probe contract: %s %s %s %.2f conId=%s tradingClass=%s",
            symbol,
            expiry,
            right,
            strike_used,
            option.conId,
            getattr(option, "tradingClass", None),
        )
        if (
            strike_requested is not None
            and strike_used is not None
            and abs(strike_used - strike_requested) > 1e-6
        ):
            logger.info("Strike fallback: requested=%.2f used=%.2f", strike_requested, strike_used)

        results: list[ProbeResult] = []

        for bar_size in BAR_SIZES_DEFAULT:
            for what in WHAT_TO_SHOW_DEFAULT:
                had_non_empty = False
                for duration in DURATION_LADDER_DEFAULT:
                    bars, err = _fetch_bars(
                        ib,
                        option,
                        what_to_show=what,
                        duration=duration,
                        bar_size=bar_size,
                        end_date_time=end_dt,
                        use_rth=bool(args.use_rth),
                        throttle=throttle,
                        max_retries=args.max_retries,
                        pacing_sleep_sec=args.pacing_sleep_sec,
                        historical_timeout_sec=float(args.historical_timeout_sec),
                    )

                    first_raw = bars[0].date if bars and hasattr(bars[0], "date") else None
                    last_raw = bars[-1].date if bars and hasattr(bars[-1], "date") else None
                    first = _normalize_bar_date(first_raw)
                    last = _normalize_bar_date(last_raw)

                    error_code = err.code if err is not None else None
                    error_message = err.message if err is not None else None
                    error_class = _classify_request_error(err) if err is not None else None

                    if bars:
                        had_non_empty = True

                    results.append(
                        ProbeResult(
                            bar_size=bar_size,
                            what_to_show=what,
                            duration=duration,
                            use_rth=bool(args.use_rth),
                            bars=len(bars),
                            first=first,
                            last=last,
                            error_code=error_code if error_code != -1 else None,
                            error_message=error_message,
                            error_class=error_class,
                        )
                    )

                    status = "OK" if bars else ("EMPTY" if err is None else f"ERR({error_code})")
                    logger.info(
                        "%-6s | %-9s | %-7s | %-5s | bars=%4d | first=%s | last=%s%s",
                        status,
                        bar_size,
                        duration,
                        what,
                        len(bars),
                        first,
                        last,
                        f" | {error_class}: {error_message}" if err is not None else "",
                    )

                    if err is not None and error_class == "duration_limit":
                        break
                    if had_non_empty and not bars and err is not None and err.code == 1100:
                        break
                    if (
                        had_non_empty
                        and not bars
                        and err is None
                        and duration != DURATION_LADDER_DEFAULT[0]
                    ):
                        break

    finally:
        logger.info("Disconnecting")
        ib.disconnect()

    with out_path.open("w", encoding="utf-8") as fh:
        meta = {
            "run_id": run_id,
            "asof_et": asof_et,
            "host": args.host,
            "port": args.port,
            "client_id": args.client_id,
            "connect_timeout_sec": float(args.connect_timeout_sec),
            "connect_retries": int(args.connect_retries),
            "market_data_type": args.market_data_type,
            "symbol": symbol,
            "right": right,
            "strike_requested": strike_requested,
            "use_rth": bool(args.use_rth),
            "prefer_strike_step": float(args.prefer_strike_step),
            "historical_timeout_sec": float(args.historical_timeout_sec),
            "endDateTime": end_dt,
            "bar_sizes": BAR_SIZES_DEFAULT,
            "what_to_show_options": WHAT_TO_SHOW_DEFAULT,
            "duration_ladder": DURATION_LADDER_DEFAULT,
            "underlying_conid": stock.conId,
            "reference_close": ref_price,
            "expiry_override": expiry_override,
            "selected_quarterly_expiry": expiry,
            "selected_strike": strike_used,
            "option_conid": option.conId,
            "option_trading_class": getattr(option, "tradingClass", None),
            "option_multiplier": getattr(option, "multiplier", None),
        }
        fh.write(json.dumps({"meta": meta}, cls=DateTimeEncoder) + "\n")
        for item in results:
            fh.write(json.dumps(item.to_json(), cls=DateTimeEncoder) + "\n")

    logger.info("Results written: %s", out_path)
    _summarize(
        results,
        bar_sizes=BAR_SIZES_DEFAULT,
        what_to_show_list=WHAT_TO_SHOW_DEFAULT,
        duration_ladder=DURATION_LADDER_DEFAULT,
    )


if __name__ == "__main__":
    main()
