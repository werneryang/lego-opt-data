from __future__ import annotations

import sys
import time
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

import typer

from .config import load_config
from .pipeline.backfill import BackfillPlanner, BackfillRunner
from .util.calendar import to_et_date, is_trading_day
from .ib import (
    IBSession,
    sec_def_params,
    enumerate_options,
    resolve_conids,
    make_throttle,
    fetch_daily,
    bars_to_dicts,
    OptionSpec,
)


app = typer.Typer(add_completion=False, help="opt-data CLI entrypoint")


@app.command()
def backfill(
    start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    symbols: Optional[str] = typer.Option(None, help="Comma separated symbols, optional"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    end: Optional[str] = typer.Option(
        None, help="End date YYYY-MM-DD or 'today'. Defaults to start date."
    ),
    days: Optional[int] = typer.Option(
        None, help="Number of calendar days to backfill starting from start"
    ),
    execute: bool = typer.Option(False, "--execute/--plan-only", help="Run backfill immediately"),
    limit: Optional[int] = typer.Option(
        None, help="Limit number of symbols to process per day during execution"
    ),
    force_refresh: bool = typer.Option(False, help="Ignore cached contracts when executing"),
    timeout: int = typer.Option(
        60,
        help="Timeout in seconds without progress before aborting execution (<=0 disables)",
    ),
) -> None:
    cfg = load_config(Path(config) if config else None)

    def parse_date(value: str) -> date:
        if value == "today":
            return to_et_date(datetime.utcnow())
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise typer.BadParameter("Expected YYYY-MM-DD or 'today'") from exc

    start_date = parse_date(start)

    if end and days:
        typer.echo("Cannot specify both --end and --days", err=True)
        raise typer.Exit(code=2)

    if days is not None and days <= 0:
        typer.echo("--days must be positive", err=True)
        raise typer.Exit(code=2)

    if end:
        end_date = parse_date(end)
    elif days:
        end_date = start_date + timedelta(days=days - 1)
    else:
        end_date = start_date

    if end_date < start_date:
        typer.echo("--end must be on or after --start", err=True)
        raise typer.Exit(code=2)

    selected = [s.strip().upper() for s in symbols.split(",")] if symbols else None

    planner = BackfillPlanner(cfg)

    current = start_date
    total_tasks = 0
    planned_days = 0
    while current <= end_date:
        if is_trading_day(current):
            queue = planner.plan(current, selected)
            queue_path = planner.queue_path(current)
            typer.echo(
                f"[backfill] planned {len(queue)} tasks for {current.isoformat()} -> {queue_path}"
            )
            total_tasks += len(queue)
            planned_days += 1
        current += timedelta(days=1)

    typer.echo(
        f"[backfill] planning complete: {planned_days} trading days, total tasks={total_tasks}"
    )
    typer.echo(
        "[backfill] acquisition "
        f"mode={cfg.acquisition.mode} duration={cfg.acquisition.duration} "
        f"bar_size={cfg.acquisition.bar_size} what={cfg.acquisition.what_to_show} "
        f"use_rth={cfg.acquisition.use_rth} max_strikes={cfg.acquisition.max_strikes_per_expiry}"
    )

    if execute:
        log_dir = cfg.paths.run_logs
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        log_file = log_dir / (
            f"backfill_{start_date.isoformat()}_{end_date.isoformat()}_{timestamp}.log"
        )
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(
                "# Backfill execution\n"
                f"mode={cfg.acquisition.mode} duration={cfg.acquisition.duration} "
                f"bar_size={cfg.acquisition.bar_size} what={cfg.acquisition.what_to_show} "
                f"use_rth={cfg.acquisition.use_rth} max_strikes={cfg.acquisition.max_strikes_per_expiry}\n"
                f"symbols={selected or 'ALL'} start={start_date} end={end_date} limit={limit or 'ALL'}\n"
            )

        timeout = max(timeout, 0)
        if timeout == 0:
            typer.echo("[backfill] timeout disabled")

        last_event = time.monotonic()

        def stop_requested() -> bool:
            if timeout <= 0:
                return False
            return time.monotonic() - last_event > timeout

        runner = BackfillRunner(cfg)

        def report(day: date, symbol: str, status: str, extra: Dict[str, Any]) -> None:
            nonlocal last_event
            last_event = time.monotonic()
            parts = [f"[backfill:{status}]", day.isoformat()]
            if symbol:
                parts.append(symbol)
            if extra:
                details = ", ".join(f"{k}={v}" for k, v in extra.items())
                parts.append(details)
            typer.echo(" ".join(parts))
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(" ".join(parts) + "\n")

        with log_file.open("a", encoding="utf-8") as fh:
            fh.write("[backfill] execution started\n")

        try:
            processed = runner.run_range(
                start_date,
                end_date,
                selected,
                force_refresh=force_refresh,
                limit_per_day=limit,
                progress=report,
                stop_requested=stop_requested,
            )
            summary = f"[backfill] executed tasks={processed} output_root={cfg.paths.raw}"
            typer.echo(summary)
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(summary + "\n")
        except Exception as exc:
            error_line = f"[backfill:error] exception={exc}"
            typer.echo(error_line, err=True)
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(error_line + "\n")
            raise


@app.command()
def ib_smoke(
    symbols: str = typer.Option("AAPL,MSFT", help="Comma separated list of underlying symbols"),
    duration: str = typer.Option("30 D", help="Historical duration string, e.g. '30 D'"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    contracts: int = typer.Option(
        4, "--contracts", "-n", help="Maximum option contracts per symbol to fetch"
    ),
    include_expired: bool = typer.Option(True, help="Include expired contracts when resolving"),
    throttle_sec: float = typer.Option(0.35, help="Minimum seconds between historical requests"),
    what: List[str] = typer.Option(
        ["TRADES", "OPTION_OPEN_INTEREST"],
        "--what",
        "-w",
        help="Historical data types to request (repeatable)",
    ),
    output: Optional[str] = typer.Option(
        None, help="Optional path for JSONL summary (defaults under state/ib_smoke)"
    ),
) -> None:
    """Manual IB smoke test for a handful of option contracts."""

    if contracts <= 0:
        typer.echo("--contracts must be positive", err=True)
        raise typer.Exit(code=2)

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        typer.echo("No symbols provided", err=True)
        raise typer.Exit(code=2)

    cfg = load_config(Path(config) if config else None)
    expiry_types = {etype.lower() for etype in cfg.filters.expiry_types}
    only_monthly = "monthly" in expiry_types
    include_quarterly = "quarterly" in expiry_types
    output_dir = cfg.paths.state / "ib_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    log_path = Path(output).expanduser() if output else output_dir / f"summary_{timestamp}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    throttle = make_throttle(throttle_sec)

    session = IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        market_data_type=cfg.ib.market_data_type,
    )

    summaries: List[Dict[str, Any]] = []

    def select_contracts(items: List[OptionSpec], price: float) -> List[OptionSpec]:
        scored = sorted(
            items,
            key=lambda opt: (
                abs(opt.strike - price),
                opt.expiry,
                opt.right,
                opt.exchange,
            ),
        )
        selected: List[OptionSpec] = []
        seen: set[tuple[str, float, str]] = set()
        for opt in scored:
            key = (opt.expiry, opt.strike, opt.right)
            if key in seen:
                continue
            seen.add(key)
            selected.append(opt)
            if len(selected) >= contracts:
                break
        return selected

    def historical_close(ib_obj: Any, symbol: str) -> tuple[float, int]:
        from ib_insync import Stock  # type: ignore

        stock = Stock(symbol, "SMART", "USD")
        ib_obj.qualifyContracts(stock)
        throttle()
        bars = ib_obj.reqHistoricalData(
            stock,
            endDateTime="",
            durationStr="3 D",
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,
            formatDate=2,
            keepUpToDate=False,
        )
        if not bars:
            raise RuntimeError(f"No historical data returned for underlying {symbol}")
        return float(bars[-1].close), int(getattr(stock, "conId", 0) or 0)

    with session as sess:
        ib = sess.ensure_connected()
        for symbol in symbol_list:
            typer.echo(f"[ib_smoke] symbol={symbol} duration={duration}")
            try:
                spot, underlying_conid = historical_close(ib, symbol)
            except Exception as exc:  # pragma: no cover - network failure
                msg = f"[ib_smoke] {symbol} failed to fetch underlying close: {exc}"
                typer.echo(msg, err=True)
                summaries.append(
                    {
                        "symbol": symbol,
                        "error": str(exc),
                        "stage": "underlying_close",
                    }
                )
                continue

            try:
                params = sec_def_params(ib, symbol, underlying_conid=underlying_conid)
            except Exception as exc:  # pragma: no cover - network failure
                typer.echo(f"[ib_smoke] {symbol} sec_def_params failed: {exc}", err=True)
                summaries.append(
                    {
                        "symbol": symbol,
                        "error": str(exc),
                        "stage": "sec_def_params",
                    }
                )
                continue

            specs = enumerate_options(
                params,
                symbol=symbol,
                underlying_price=spot,
                moneyness_pct=cfg.filters.moneyness_pct,
                only_standard_monthly=only_monthly,
                include_quarterly=include_quarterly,
            )
            if not specs:
                typer.echo(f"[ib_smoke] {symbol} no option specs after filtering", err=True)
                summaries.append(
                    {
                        "symbol": symbol,
                        "error": "No option specs after filtering",
                        "stage": "enumerate_options",
                    }
                )
                continue

            smart_specs = [opt for opt in specs if opt.exchange.upper() == "SMART"]
            candidate_pool = smart_specs or specs
            selected_specs = select_contracts(candidate_pool, spot)
            if not selected_specs:
                typer.echo(f"[ib_smoke] {symbol} no contracts selected", err=True)
                summaries.append(
                    {
                        "symbol": symbol,
                        "error": "No contracts selected",
                        "stage": "select_contracts",
                    }
                )
                continue

            normalized_specs = [
                OptionSpec(
                    symbol=s.symbol,
                    expiry=s.expiry,
                    strike=s.strike,
                    right=s.right,
                    exchange=s.exchange if s.exchange.upper() == "SMART" else "SMART",
                    currency="USD",
                    trading_class=s.trading_class,
                    multiplier=s.multiplier,
                )
                for s in selected_specs
            ]

            try:
                resolved = resolve_conids(ib, normalized_specs, include_expired=include_expired)
            except Exception as exc:  # pragma: no cover - network failure
                typer.echo(f"[ib_smoke] {symbol} resolve_conids failed: {exc}", err=True)
                summaries.append(
                    {
                        "symbol": symbol,
                        "error": str(exc),
                        "stage": "resolve_conids",
                    }
                )
                continue

            if not resolved:
                typer.echo(f"[ib_smoke] {symbol} no contracts resolved", err=True)
                summaries.append(
                    {
                        "symbol": symbol,
                        "error": "No contracts resolved",
                        "stage": "resolve_conids",
                    }
                )
                continue

            for resolved_option in resolved:
                contract_dir = output_dir / symbol / str(resolved_option.conid)
                contract_dir.mkdir(parents=True, exist_ok=True)
                for what_to_show in what:
                    try:
                        bars = fetch_daily(
                            ib,
                            resolved_option.contract,
                            what_to_show=what_to_show,
                            duration=duration,
                            throttle=throttle,
                        )
                        bar_dicts = bars_to_dicts(bars)
                        path = contract_dir / f"{what_to_show.lower()}.json"
                        path.write_text(json.dumps(bar_dicts), encoding="utf-8")
                        if bar_dicts:
                            first_date = bar_dicts[0].get("date")
                            last_date = bar_dicts[-1].get("date")
                        else:
                            first_date = None
                            last_date = None
                        summaries.append(
                            {
                                "symbol": symbol,
                                "conid": resolved_option.conid,
                                "expiry": resolved_option.spec.expiry,
                                "right": resolved_option.spec.right,
                                "strike": resolved_option.spec.strike,
                                "what": what_to_show,
                                "bars": len(bar_dicts),
                                "first": first_date,
                                "last": last_date,
                            }
                        )
                        typer.echo(
                            f"[ib_smoke] {symbol} conid={resolved_option.conid} "
                            f"{what_to_show} bars={len(bar_dicts)} first={first_date} last={last_date}"
                        )
                    except Exception as exc:  # pragma: no cover - network failure
                        typer.echo(
                            f"[ib_smoke] {symbol} conid={resolved_option.conid} "
                            f"{what_to_show} failed: {exc}",
                            err=True,
                        )
                        summaries.append(
                            {
                                "symbol": symbol,
                                "conid": resolved_option.conid,
                                "expiry": resolved_option.spec.expiry,
                                "right": resolved_option.spec.right,
                                "strike": resolved_option.spec.strike,
                                "what": what_to_show,
                                "error": str(exc),
                            }
                        )

    with log_path.open("w", encoding="utf-8") as fh:
        for item in summaries:
            fh.write(json.dumps(item) + "\n")

    typer.echo(f"[ib_smoke] summary written to {log_path}")


@app.command()
def update(
    date_arg: str = typer.Option("today", "--date", help="Update date YYYY-MM-DD or 'today'"),
    symbols: Optional[str] = typer.Option(
        None, help="Comma separated list of symbols to update (defaults to universe)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    mode: str = typer.Option(
        "snapshot",
        "--mode",
        help="Acquisition mode (snapshot|historical); overrides config",
    ),
    limit: Optional[int] = typer.Option(
        None, help="Limit number of symbols to process for the target date"
    ),
    force_refresh: bool = typer.Option(False, help="Force refresh contract cache"),
) -> None:
    mode_normalized = mode.strip().lower()
    if mode_normalized not in {"snapshot", "historical"}:
        typer.echo("--mode must be 'snapshot' or 'historical'", err=True)
        raise typer.Exit(code=2)

    cfg = load_config(Path(config) if config else None)
    cfg.acquisition.mode = mode_normalized

    target_date = (
        to_et_date(datetime.utcnow()) if date_arg == "today" else date.fromisoformat(date_arg)
    )

    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None

    typer.echo(
        f"[update] date={target_date} mode={cfg.acquisition.mode} "
        f"limit={limit or 'ALL'} force_refresh={force_refresh}"
    )

    runner = BackfillRunner(cfg)
    processed_rows: Dict[str, Any] = {}

    def progress_cb(day: date, symbol: str, status: str, extra: Dict[str, Any]) -> None:
        stamp = day.isoformat()
        parts = [f"[update:{status}]", stamp]
        if symbol:
            parts.append(symbol)
        if extra:
            parts.append(", ".join(f"{k}={v}" for k, v in extra.items()))
        line = " ".join(parts)
        typer.echo(line)
        if status == "success" and symbol:
            processed_rows[symbol] = extra

    processed = runner.run(
        target_date,
        symbol_list,
        limit=limit,
        force_refresh=force_refresh,
        progress=progress_cb,
    )

    typer.echo(f"[update] processed={processed} symbols_processed={len(processed_rows)}")


@app.command()
def compact(
    older_than: int = typer.Option(14, help="Compact partitions older than N days"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    typer.echo(f"[compact] older_than={older_than} data_roots=[{cfg.paths.raw}, {cfg.paths.clean}]")


@app.command()
def inspect(
    what: str = typer.Argument("config", help="What to inspect: config|paths|connection"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    if what == "config":
        typer.echo(repr(cfg))
    elif what == "paths":
        typer.echo(f"raw={cfg.paths.raw}\nclean={cfg.paths.clean}\nstate={cfg.paths.state}")
    elif what == "connection":
        """Validate IB connection and market data type settings."""
        session = IBSession(
            host=cfg.ib.host,
            port=cfg.ib.port,
            client_id=cfg.ib.client_id,
            market_data_type=cfg.ib.market_data_type,
        )
        try:
            with session as sess:
                ib = sess.ensure_connected()
                # Try fetching server time if available; ib_insync.IB.serverTime is a method
                server_time = None
                st = getattr(ib, "serverTime", None)
                if callable(st):  # type: ignore[call-arg]
                    try:
                        server_time = st()
                    except Exception:  # pragma: no cover - best-effort info
                        server_time = None
                typer.echo(
                    "[inspect:connection] "
                    f"connected=True host={cfg.ib.host} port={cfg.ib.port} "
                    f"clientId={cfg.ib.client_id} market_data_type={cfg.ib.market_data_type} "
                    f"server_time={server_time}"
                )
        except Exception as exc:  # pragma: no cover - network/env dependent
            typer.echo(f"[inspect:connection] connected=False error={exc}", err=True)
            raise typer.Exit(code=1)
    else:
        typer.echo("Unknown inspect target", err=True)
        raise typer.Exit(code=2)


@app.command()
def logscan(
    date_str: str = typer.Option("today", "--date", help="Target ET date YYYY-MM-DD or 'today'"),
    keywords: str = typer.Option(
        "ERROR,CRITICAL,PACING,No market data permissions,slot_retry_exceeded,eod_rollup_stale,eod_rollup_fallback",
        help="Comma-separated keywords to scan for",
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    write_summary: bool = typer.Option(True, help="Write JSON summary under run_logs/errors"),
) -> None:
    """Aggregate errors and important markers from run logs for the given day."""
    cfg = load_config(Path(config) if config else None)

    def parse_et(value: str) -> date:
        if value == "today":
            return to_et_date(datetime.utcnow())
        try:
            return date.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - CLI validation
            raise typer.BadParameter("Expected YYYY-MM-DD or 'today'") from exc

    target_day = parse_et(date_str)
    ymd = target_day.strftime("%Y-%m-%d")
    ymd_compact = target_day.strftime("%Y%m%d")
    run_logs = cfg.paths.run_logs
    errors_dir = run_logs / "errors"
    errors_dir.mkdir(parents=True, exist_ok=True)

    # Prefer consolidated daily error log if present; otherwise scan all logs.
    consolidated = errors_dir / f"errors_{ymd_compact}.log"
    counters: Counter[str] = Counter()
    matched_files: list[str] = []

    def scan_file(path: Path, keys: list[str]) -> None:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # pragma: no cover - file permissions
            return
        low = text.lower()
        for k in keys:
            cnt = low.count(k.lower())
            if cnt:
                counters[k] += cnt

    key_list = [k.strip() for k in keywords.split(",") if k.strip()]

    if consolidated.exists():
        matched_files.append(str(consolidated))
        scan_file(consolidated, key_list)
    else:
        # Scan all log-like files under run_logs for lines containing the target day.
        for p in run_logs.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".log", ".jsonl", ".txt"}:
                continue
            # Heuristic: only consider files touched today to limit scope
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
            except Exception:
                mtime = None
            if mtime and to_et_date(mtime) != target_day:
                continue
            matched_files.append(str(p))
            scan_file(p, key_list)

    summary = {
        "date": ymd,
        "keywords": key_list,
        "files_scanned": matched_files,
        "counts": dict(counters),
    }

    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))

    if write_summary:
        out_path = errors_dir / f"summary_{ymd_compact}.json"
        try:
            out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - fs issues
            typer.echo(f"[logscan] failed to write summary: {exc}", err=True)


def main(argv: list[str] | None = None) -> int:
    try:
        app()
        return 0
    except SystemExit as e:
        return int(e.code)


if __name__ == "__main__":
    sys.exit(main())
