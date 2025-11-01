from __future__ import annotations

import sys
import time
import json
from collections import Counter
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional, Dict, Any, List

import typer

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - optional dependency guard
    BackgroundScheduler = None  # type: ignore[assignment]

from .config import load_config
from .pipeline.backfill import BackfillPlanner, BackfillRunner
from .pipeline.snapshot import SnapshotRunner
from .pipeline.rollup import RollupRunner
from .pipeline.enrichment import EnrichmentRunner
from .pipeline.scheduler import ScheduleRunner
from .pipeline.qa import QAMetricsCalculator
from .util.calendar import to_et_date, is_trading_day
from .util.logscanner import scan_logs
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
def snapshot(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    slot: str = typer.Option(
        "now",
        "--slot",
        help="Slot label HH:MM (ET) or 'now'/'next' to pick the upcoming slot",
    ),
    symbols: Optional[str] = typer.Option(
        None, "--symbols", help="Comma separated symbols (defaults to full universe)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    force_refresh: bool = typer.Option(False, help="Force refresh contract discovery cache"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.utcnow()) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None

    runner = SnapshotRunner(cfg, snapshot_grace_seconds=cfg.cli.snapshot_grace_seconds)
    try:
        slot_obj = runner.resolve_slot(trade_date, slot)
    except ValueError as exc:
        typer.echo(f"[snapshot] {exc}", err=True)
        raise typer.Exit(code=2)

    typer.echo(
        f"[snapshot] date={trade_date} slot={slot_obj.label} symbols={symbol_list or 'ALL'} "
        f"force_refresh={force_refresh}"
    )

    def progress_cb(symbol: str, status: str, extra: Dict[str, Any]) -> None:
        parts = [f"[snapshot:{status}]", f"slot={slot_obj.label}"]
        if symbol:
            parts.append(symbol)
        if extra:
            parts.append(", ".join(f"{k}={v}" for k, v in extra.items()))
        typer.echo(" ".join(parts))

    try:
        result = runner.run(
            trade_date,
            slot_obj,
            symbol_list,
            force_refresh=force_refresh,
            progress=progress_cb,
        )
    except Exception as exc:  # pragma: no cover - network/runtime specific
        typer.echo(f"[snapshot:error] {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(
        "[snapshot] "
        f"ingest_id={result.ingest_id} rows={result.rows_written} "
        f"raw_files={len(result.raw_paths)} clean_files={len(result.clean_paths)} "
        f"errors={len(result.errors)}"
    )
    if result.errors:
        for err in result.errors[:5]:
            typer.echo(
                "[snapshot:error] "
                f"symbol={err.get('symbol')} stage={err.get('stage')} error={err.get('error')}"
            )
        if len(result.errors) > 5:
            typer.echo(f"[snapshot] ... {len(result.errors) - 5} more errors logged")


@app.command()
def rollup(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    symbols: Optional[str] = typer.Option(
        None, "--symbols", help="Comma separated symbols (defaults to full universe)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    close_slot: Optional[int] = typer.Option(
        None, help="Slot index treated as market close (default from config)"
    ),
    fallback_slot: Optional[int] = typer.Option(
        None, help="Fallback slot index before using last_good (default from config)"
    ),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.utcnow()) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None

    effective_close = close_slot if close_slot is not None else cfg.cli.rollup_close_slot
    effective_fallback = (
        fallback_slot if fallback_slot is not None else cfg.cli.rollup_fallback_slot
    )

    typer.echo(
        f"[rollup] date={trade_date} close_slot={effective_close} "
        f"fallback_slot={effective_fallback} symbols={symbol_list or 'ALL'}"
    )

    runner = RollupRunner(cfg, close_slot=effective_close, fallback_slot=effective_fallback)

    def progress_cb(symbol: str, status: str, extra: Dict[str, Any]) -> None:
        parts = [f"[rollup:{status}]", symbol]
        if extra:
            parts.append(", ".join(f"{k}={v}" for k, v in extra.items()))
        typer.echo(" ".join(parts))

    try:
        result = runner.run(trade_date, symbol_list, progress=progress_cb)
    except Exception as exc:  # pragma: no cover - runtime specific
        typer.echo(f"[rollup:error] {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(
        "[rollup] "
        f"ingest_id={result.ingest_id} rows={result.rows_written} "
        f"symbols={result.symbols_processed} strategies={result.strategy_counts} "
        f"daily_clean_files={len(result.daily_clean_paths)} "
        f"daily_adjusted_files={len(result.daily_adjusted_paths)}"
    )
    if result.errors:
        for err in result.errors[:5]:
            typer.echo(
                "[rollup:error] "
                f"symbol={err.get('symbol')} stage={err.get('stage')} error={err.get('error')}"
            )
        if len(result.errors) > 5:
            typer.echo(f"[rollup] ... {len(result.errors) - 5} more errors logged")


@app.command()
def enrichment(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    symbols: Optional[str] = typer.Option(
        None, "--symbols", help="Comma separated symbols (defaults to full universe)"
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields", help="Comma separated fields to enrich (default from config)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    oi_duration: Optional[str] = typer.Option(
        None, help="Duration window for open interest requests (overrides config)"
    ),
    oi_use_rth: Optional[bool] = typer.Option(
        None, help="Whether to request open interest with useRTH (overrides config)"
    ),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.utcnow()) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None

    field_list = None
    if fields:
        tokens = [token.strip() for token in fields.split(",") if token.strip()]
        if not tokens:
            typer.echo("[enrichment] --fields provided but empty", err=True)
            raise typer.Exit(code=2)
        field_list = tokens

    effective_fields = field_list or cfg.enrichment.fields
    effective_duration = oi_duration or cfg.enrichment.oi_duration
    effective_use_rth = oi_use_rth if oi_use_rth is not None else cfg.enrichment.oi_use_rth

    typer.echo(
        f"[enrichment] date={trade_date} fields={effective_fields} "
        f"oi_duration='{effective_duration}' use_rth={effective_use_rth} "
        f"symbols={symbol_list or 'ALL'}"
    )

    runner = EnrichmentRunner(
        cfg,
        oi_duration=effective_duration,
        oi_use_rth=effective_use_rth,
    )

    def progress_cb(symbol: str, status: str, extra: Dict[str, Any]) -> None:
        parts = [f"[enrichment:{status}]"]
        if symbol:
            parts.append(symbol)
        if extra:
            parts.append(", ".join(f"{k}={v}" for k, v in extra.items()))
        typer.echo(" ".join(parts))

    try:
        result = runner.run(
            trade_date,
            symbol_list,
            fields=effective_fields,
            progress=progress_cb,
        )
    except ValueError as exc:
        typer.echo(f"[enrichment] {exc}", err=True)
        raise typer.Exit(code=2)
    except Exception as exc:  # pragma: no cover - runtime specific
        typer.echo(f"[enrichment:error] {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(
        "[enrichment] "
        f"ingest_id={result.ingest_id} rows_considered={result.rows_considered} "
        f"rows_updated={result.rows_updated} symbols={result.symbols_processed} "
        f"daily_clean_files={len(result.daily_clean_paths)} "
        f"daily_adjusted_files={len(result.daily_adjusted_paths)} "
        f"enrichment_files={len(result.enrichment_paths)}"
    )
    if result.errors:
        for err in result.errors[:5]:
            typer.echo(
                "[enrichment:error] "
                f"symbol={err.get('symbol')} stage={err.get('stage')} error={err.get('error')}"
            )
        if len(result.errors) > 5:
            typer.echo(f"[enrichment] ... {len(result.errors) - 5} more errors logged")


@app.command()
def schedule(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    symbols: Optional[str] = typer.Option(
        None, "--symbols", help="Comma separated symbols (defaults to full universe)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    enrichment_fields: Optional[str] = typer.Option(
        None, "--enrichment-fields", help="Comma separated enrichment fields"
    ),
    simulate: bool = typer.Option(True, "--simulate/--live", help="Run jobs immediately for the day"),
    snapshots: bool = typer.Option(True, "--snapshots/--skip-snapshots", help="Include snapshot jobs"),
    rollup: bool = typer.Option(True, "--rollup/--skip-rollup", help="Include rollup job"),
    enrichment: bool = typer.Option(
        True, "--enrichment/--skip-enrichment", help="Include enrichment job"
    ),
    misfire_grace_seconds: int = typer.Option(300, help="Grace window for missed jobs (seconds)"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.utcnow()) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
    fields = [f.strip().lower() for f in enrichment_fields.split(",") if f.strip()] if enrichment_fields else None

    runner = ScheduleRunner(cfg)
    jobs = runner.plan_day(
        trade_date,
        symbols=symbol_list,
        enrichment_fields=fields,
        include_snapshots=snapshots,
        include_rollup=rollup,
        include_enrichment=enrichment,
    )

    if not jobs:
        typer.echo(f"[schedule] no jobs planned for {trade_date} (non-trading day or all tasks skipped)")
        return

    typer.echo(
        f"[schedule] trade_date={trade_date} simulate={simulate} "
        f"snapshots={snapshots} rollup={rollup} enrichment={enrichment} jobs={len(jobs)}"
    )

    if simulate:
        summary = runner.run_simulation(
            trade_date,
            symbols=symbol_list,
            enrichment_fields=fields,
            include_snapshots=snapshots,
            include_rollup=rollup,
            include_enrichment=enrichment,
        )
        typer.echo(
            "[schedule] simulation completed "
            f"snapshots={summary.snapshots} rollups={summary.rollups} "
            f"enrichments={summary.enrichments} errors={len(summary.errors or [])}"
        )
        if summary.errors:
            for err in summary.errors[:5]:
                typer.echo(
                    "[schedule:error] "
                    f"kind={err.get('kind')} run_time={err.get('run_time')} error={err.get('error')}"
                )
            if len(summary.errors) > 5:
                typer.echo(f"[schedule] ... {len(summary.errors) - 5} more errors recorded")
        return

    if BackgroundScheduler is None:
        typer.echo("[schedule] APScheduler is not installed; install apscheduler>=3.10 to use --live", err=True)
        raise typer.Exit(code=1)

    scheduler = BackgroundScheduler(timezone=ZoneInfo(cfg.timezone.name))
    job_ids = runner.schedule(
        scheduler,
        trade_date,
        symbols=symbol_list,
        enrichment_fields=fields,
        include_snapshots=snapshots,
        include_rollup=rollup,
        include_enrichment=enrichment,
        misfire_grace_seconds=misfire_grace_seconds,
    )

    typer.echo(f"[schedule] scheduled jobs={len(job_ids)} ids={job_ids}")
    scheduler.start()
    typer.echo("[schedule] scheduler started; press Ctrl+C to stop")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        typer.echo("[schedule] stopping scheduler")
    finally:
        scheduler.shutdown()


@app.command()
def qa(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    write: bool = typer.Option(True, "--write/--no-write", help="Persist metrics JSON"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.utcnow()) if date_str == "today" else date.fromisoformat(date_str)
    )

    calculator = QAMetricsCalculator(cfg)
    result = calculator.evaluate(trade_date)

    typer.echo(
        "[qa] "
        f"trade_date={trade_date} status={result.status} breaches={result.breaches or 'NONE'}"
    )
    for metric in result.metrics:
        typer.echo(
            f"[qa:metric] {metric.name} value={metric.value:.4f} "
            f"threshold{metric.comparator}{metric.threshold:.4f} passed={metric.passed}"
        )

    if write:
        path = calculator.persist(result)
        typer.echo(f"[qa] metrics_written={path}")

    if result.status != "PASS":
        raise typer.Exit(code=1)


@app.command()
def selfcheck(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    log_keywords: str = typer.Option(
        "ERROR,CRITICAL,PACING,slot_retry_exceeded,eod_rollup_stale,eod_rollup_fallback",
        help="Comma-separated keywords for log scanning",
    ),
    log_max_total: int = typer.Option(
        0, help="Max allowed matches across keywords before failing (<=0 means any hit fails)"
    ),
    write: bool = typer.Option(True, "--write/--no-write", help="Persist selfcheck JSON report"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.utcnow()) if date_str == "today" else date.fromisoformat(date_str)
    )

    qa_calc = QAMetricsCalculator(cfg)
    qa_result = qa_calc.evaluate(trade_date)

    key_list = [k.strip() for k in log_keywords.split(",") if k.strip()]
    counters, matched_files = scan_logs(cfg, trade_date, key_list)
    total_matches = sum(counters.values())

    status = "PASS"
    reasons: list[str] = []

    if qa_result.status != "PASS":
        status = "FAIL"
        reasons.extend(f"qa:{name}" for name in qa_result.breaches)

    if log_max_total >= 0 and total_matches > log_max_total:
        status = "FAIL"
        reasons.append(f"logs:total>{log_max_total}")

    typer.echo(
        f"[selfcheck] date={trade_date} status={status} total_log_matches={total_matches} "
        f"qa_status={qa_result.status} reasons={reasons or 'NONE'}"
    )

    for metric in qa_result.metrics:
        typer.echo(
            f"[selfcheck:qa] {metric.name} value={metric.value:.4f} "
            f"threshold{metric.comparator}{metric.threshold:.4f} passed={metric.passed}"
        )

    if counters:
        for k, v in sorted(counters.items(), key=lambda kv: kv[0]):
            typer.echo(f"[selfcheck:logs] keyword={k} count={v}")

    report = {
        "trade_date": trade_date.isoformat(),
        "status": status,
        "reasons": reasons,
        "qa": qa_result.as_dict(),
        "logs": {
            "keywords": key_list,
            "total_matches": total_matches,
            "counts": counters,
            "files_scanned": matched_files,
        },
    }

    if write:
        report_dir = Path(cfg.paths.state) / "run_logs" / "selfcheck"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"selfcheck_{trade_date.strftime('%Y%m%d')}.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        typer.echo(f"[selfcheck] report_written={report_path}")

    if status != "PASS":
        raise typer.Exit(code=1)


@app.command()
def logscan(
    date_str: str = typer.Option("today", "--date", help="Target ET date YYYY-MM-DD or 'today'"),
    keywords: str = typer.Option(
        "ERROR,CRITICAL,PACING,No market data permissions,slot_retry_exceeded,eod_rollup_stale,eod_rollup_fallback",
        help="Comma-separated keywords to scan for",
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    write_summary: bool = typer.Option(True, help="Write JSON summary under run_logs/errors"),
    max_total: int = typer.Option(0, help="Max allowed total matches before exiting with failure"),
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

    key_list = [k.strip() for k in keywords.split(",") if k.strip()]
    counters, matched_files = scan_logs(cfg, target_day, key_list)

    summary = {
        "date": ymd,
        "keywords": key_list,
        "files_scanned": matched_files,
        "counts": counters,
    }

    total_matches = sum(counters.values())
    summary["total_matches"] = total_matches
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))

    if write_summary:
        out_path = errors_dir / f"summary_{ymd_compact}.json"
        try:
            out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - fs issues
            typer.echo(f"[logscan] failed to write summary: {exc}", err=True)

    if max_total >= 0 and total_matches > max_total:
        typer.echo(
            f"[logscan] total_matches {total_matches} exceeds max_total {max_total}", err=True
        )
        raise typer.Exit(code=1)


def main(argv: list[str] | None = None) -> int:
    try:
        app()
        return 0
    except SystemExit as e:
        return int(e.code)


if __name__ == "__main__":
    sys.exit(main())
