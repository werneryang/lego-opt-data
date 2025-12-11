from __future__ import annotations

import json
import math
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

import typer

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - optional dependency guard
    BackgroundScheduler = None  # type: ignore[assignment]

from .config import load_config
from .pipeline.backfill import BackfillPlanner, BackfillRunner
from .pipeline.backfill import fetch_underlying_close
from .pipeline.snapshot import SnapshotRunner
from .pipeline.rollup import RollupRunner
from .pipeline.enrichment import EnrichmentRunner
from .pipeline.history import HistoryRunner
from .pipeline.scheduler import ScheduleRunner
from .pipeline.qa import QAMetricsCalculator
from .util.calendar import to_et_date, is_trading_day
from .util.logscanner import scan_logs
from .universe import load_universe
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
from .ib.discovery import cache_path, discover_contracts_for_symbol
from .ib.oi_probe import OIProbeConfig, probe_oi


app = typer.Typer(add_completion=False, help="opt-data CLI entrypoint")


def _precheck_contract_caches(
    cfg,
    trade_date: date,
    symbols_for_run: list[str],
    entries_by_symbol: dict[str, Any],
    *,
    universe_path: Path | None = None,
    build_missing_cache: bool,
    prefix: str,
) -> None:
    """Ensure contract caches exist for the requested symbols; optionally rebuild them."""

    missing: list[str] = []
    invalid: list[str] = []
    cache_root = Path(cfg.paths.contracts_cache)
    resolved_conids: dict[str, int] = {}
    # Use provided universe_path, or fall back to default config path
    effective_universe_path = universe_path or Path(cfg.universe.file)

    def _update_universe_file(path: Path, updates: dict[str, int]) -> None:
        if not updates or not path.exists():
            return
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            new_lines: list[str] = []
            seen: set[str] = set()
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    new_lines.append(line)
                    continue
                parts = line.split(",")
                if not parts:
                    new_lines.append(line)
                    continue
                sym = parts[0].strip().upper()
                if sym in updates:
                    new_lines.append(f"{sym},{updates[sym]}")
                    seen.add(sym)
                else:
                    new_lines.append(line)
            for sym, conid in updates.items():
                if sym not in seen:
                    new_lines.append(f"{sym},{conid}")
            new_lines.append("") if new_lines and new_lines[-1] != "" else None
            path.write_text("\n".join(new_lines), encoding="utf-8")
            typer.echo(
                f"[{prefix}] persisted conid updates for {', '.join(sorted(updates))} -> {path}"
            )
        except Exception as exc:  # pragma: no cover - filesystem issues
            typer.echo(f"[{prefix}] failed to persist conids to {path}: {exc}", err=True)

    def resolve_underlying_conid(ib, sym: str, conid: int | None) -> int:
        # Try to qualify the underlying to get a usable conid; prefer provided conid, fall back to
        # stock on SMART, and for common indices try CBOE index routing.
        from ib_insync import Stock, Index  # type: ignore

        candidates = []
        if conid:
            candidates.append(Stock(sym, "SMART", "USD", conId=conid))
        candidates.append(Stock(sym, "SMART", "USD"))
        if sym.upper() in {"SPX", "NDX", "VIX"}:
            candidates.append(Index(sym, "CBOE"))

        errors: list[str] = []
        for contract in candidates:
            try:
                qualified = ib.qualifyContracts(contract)
                if qualified:
                    return int(qualified[0].conId)
            except Exception as exc:  # pragma: no cover - network/IB dependent
                errors.append(str(exc))
                continue
            raise RuntimeError(f"unable to qualify underlying {sym}: {'; '.join(errors)}")

    # Phase 1: ensure we have conids for all symbols (persist even if later steps fail)
    symbols_needing_conid = [
        sym for sym in symbols_for_run if not entries_by_symbol.get(sym) or not entries_by_symbol[sym].conid
    ]
    if symbols_needing_conid:
        session = IBSession(
            host=cfg.ib.host,
            port=cfg.ib.port,
            client_id=cfg.ib.client_id,
            client_id_pool=cfg.ib.client_id_pool,
            market_data_type=cfg.ib.market_data_type,
        )
        with session as sess:
            ib = sess.ensure_connected()
            for sym in symbols_needing_conid:
                entry = entries_by_symbol.get(sym)
                existing_conid = entry.conid if entry else None
                try:
                    resolved_conid = resolve_underlying_conid(ib, sym, existing_conid)
                    if not existing_conid:
                        typer.echo(
                            f"[{prefix}] resolved underlying {sym} conid={resolved_conid} (secType auto)"
                        )
                    resolved_conids[sym] = resolved_conid
                    if entry is not None:
                        entry.conid = resolved_conid
                    else:
                        entries_by_symbol[sym] = UniverseEntry(symbol=sym, conid=resolved_conid)
                except Exception as exc:  # pragma: no cover - runtime dependent
                    typer.echo(f"[{prefix}] failed to resolve conid for {sym}: {exc}", err=True)
                    invalid.append(sym)
        if resolved_conids:
            _update_universe_file(effective_universe_path, resolved_conids)

    def check_cache(sym: str) -> tuple[str | None, str | None]:
        cache_file = cache_path(cache_root, sym, trade_date.isoformat())
        if not cache_file.exists() or cache_file.stat().st_size == 0:
            return sym, f"{sym} ({cache_file})"
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None, f"{sym} ({cache_file})"
        if not data:
            return None, f"{sym} ({cache_file})"
        return None, None

    def rebuild_caches(symbols_to_build: list[str]) -> list[str]:
        failures: list[str] = []
        session = IBSession(
            host=cfg.ib.host,
            port=cfg.ib.port,
            client_id=cfg.ib.client_id,
            client_id_pool=cfg.ib.client_id_pool,
            market_data_type=cfg.ib.market_data_type,
        )
        with session as sess:
            ib = sess.ensure_connected()
            for sym in symbols_to_build:
                entry = entries_by_symbol.get(sym)
                conid = entry.conid if entry else None
                try:
                    resolved_conid = resolve_underlying_conid(ib, sym, conid)
                    if not conid:
                        typer.echo(
                            f"[{prefix}] resolved underlying {sym} conid={resolved_conid} (secType auto)"
                        )
                        resolved_conids[sym] = resolved_conid
                        if entry is not None:
                            entry.conid = resolved_conid
                    try:
                        ref_price = fetch_underlying_close(ib, sym, trade_date, resolved_conid)
                    except Exception:
                        # Fallback to live snapshot price if HMDS is empty
                        from ib_insync import Stock  # type: ignore

                        contract = Stock(sym, "SMART", "USD", conId=resolved_conid)
                        ticker = ib.reqMktData(contract, "", True, False)
                        ib.sleep(1.0)
                        ref_price = ticker.marketPrice()
                        if ref_price is None or ref_price <= 0:
                            raise RuntimeError(
                                f"failed to fetch reference price for {sym} via market data fallback"
                            )
                    discover_contracts_for_symbol(
                        sess,
                        sym,
                        trade_date,
                        ref_price,
                        cfg,
                        underlying_conid=resolved_conid,
                        force_refresh=False,
                        allow_rebuild=True,
                        acquire_token=None,
                        max_strikes_per_expiry=cfg.acquisition.max_strikes_per_expiry,
                    )
                    typer.echo(f"[{prefix}] rebuilt contract cache for {sym}")
                except Exception as exc:  # pragma: no cover - runtime/IB dependent
                    failures.append(f"{sym} ({exc})")
        return failures

    for sym in symbols_for_run:
        miss, bad = check_cache(sym)
        if miss:
            missing.append(miss)
        if bad:
            invalid.append(bad)

    if (missing or invalid) and build_missing_cache:
        rebuild_targets = sorted(set(missing + [item.split()[0] for item in invalid]))
        failures = rebuild_caches(rebuild_targets)
        missing = []
        invalid = failures
        for sym in symbols_for_run:
            miss, bad = check_cache(sym)
            if miss:
                missing.append(miss)
            if bad:
                invalid.append(bad)

    if missing or invalid:
        parts = []
        if missing:
            paths = [
                cache_path(cache_root, sym, trade_date.isoformat()) for sym in sorted(set(missing))
            ]
            parts.append("missing=" + "; ".join(str(p) for p in paths))
        if invalid:
            parts.append(f"empty/invalid={'; '.join(sorted(set(invalid)))}")
        typer.echo(
            f"[{prefix}] contract cache precheck failed for {trade_date}: " + "; ".join(parts),
            err=True,
        )
        raise typer.Exit(code=1)


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
            return to_et_date(datetime.now(ZoneInfo("UTC")))
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
        client_id_pool=cfg.ib.client_id_pool,
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
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_arg == "today" else date.fromisoformat(date_arg)
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
def history(
    symbols: Optional[str] = typer.Option(
        None, help="Comma separated list of symbols (defaults to universe)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    days: int = typer.Option(30, help="Number of days of history to fetch"),
    output: Optional[str] = typer.Option(None, help="Output directory (default: data/clean/ib/history)"),
    what: str = typer.Option("MIDPOINT", help="Data type (MIDPOINT, TRADES, etc.)"),
    use_rth: bool = typer.Option(True, help="Use Regular Trading Hours"),
    force_refresh: bool = typer.Option(False, help="Force refresh contract cache"),
    incremental: bool = typer.Option(False, help="Only fetch missing days based on existing data"),
    bar_size: str = typer.Option("8 hours", help="Bar size (e.g. '8 hours', '1 day', '1 hour')"),
) -> None:
    """Fetch daily historical data for options (using 8-hour bar aggregation by default)."""
    cfg = load_config(Path(config) if config else None)
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    
    runner = HistoryRunner(cfg)
    
    typer.echo(f"[history] fetching {days} days of {what} data for {symbol_list or 'universe'}")
    if incremental:
        typer.echo("[history] incremental mode enabled")
    
    def progress_cb(current: int, total: int, status: str, details: Dict[str, Any]) -> None:
        # Simple CLI progress
        pct = (current / total) * 100 if total > 0 else 0
        typer.echo(f"[history] {pct:.1f}% - {status}")

    results = runner.run(
        symbols=symbol_list,
        days=days,
        output_dir=Path(output) if output else None,
        what_to_show=what,
        use_rth=use_rth,
        force_refresh=force_refresh,
        incremental=incremental,
        bar_size=bar_size,
        progress_callback=progress_cb,
    )
    
    typer.echo(f"[history] complete. processed={results['processed']} errors={results['errors']}")
    for sym, stats in results["symbols"].items():
        typer.echo(f"  {sym}: contracts={stats['contracts']} bars={stats['bars']} errors={stats['errors']}")


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
            client_id_pool=cfg.ib.client_id_pool,
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
    universe: Optional[str] = typer.Option(
        None, "--universe", help="Override universe file path (defaults to intraday_file or file)"
    ),
    force_refresh: bool = typer.Option(False, help="Force refresh contract discovery cache"),
    exchange: Optional[str] = typer.Option(
        None, "--exchange", help="Override default option exchange (e.g., SMART)"
    ),
    fallback_exchanges: Optional[str] = typer.Option(
        None,
        "--fallback-exchanges",
        help="Comma separated fallback exchanges (e.g., 'CBOE,CBOEOPT')",
    ),
    strikes: Optional[int] = typer.Option(
        None, "--strikes", help="Nearest strikes per side (overrides config)"
    ),
    ticks: Optional[str] = typer.Option(
        None, "--ticks", help="Override generic tick list for option snapshots"
    ),
    timeout: Optional[float] = typer.Option(
        None, "--timeout", help="Per-option subscription timeout seconds"
    ),
    poll_interval: Optional[float] = typer.Option(
        None, "--poll-interval", help="Per-option subscription poll interval seconds"
    ),
    snapshot_mode: Optional[str] = typer.Option(
        None,
        "--snapshot-mode",
        help="Override snapshot fetch mode (streaming/snapshot/reqtickers)",
    ),
) -> None:
    cfg = load_config(Path(config) if config else None)
    snapshot_cfg = getattr(cfg, "snapshot", None)
    if snapshot_cfg is not None:
        if exchange:
            snapshot_cfg.exchange = exchange.strip().upper()
        if fallback_exchanges:
            snapshot_cfg.fallback_exchanges = [
                token.strip().upper() for token in fallback_exchanges.split(",") if token.strip()
            ]
        if strikes and strikes > 0:
            snapshot_cfg.strikes_per_side = strikes
        if ticks:
            snapshot_cfg.generic_ticks = ticks
        if timeout and timeout > 0:
            snapshot_cfg.subscription_timeout = float(timeout)
        if poll_interval and poll_interval > 0:
            snapshot_cfg.subscription_poll_interval = float(poll_interval)
        if snapshot_mode:
            mode_normalized = snapshot_mode.strip().lower()
            if mode_normalized not in {"streaming", "snapshot", "reqtickers"}:
                typer.echo(f"Invalid --snapshot-mode: {snapshot_mode}. Valid: streaming, snapshot, reqtickers", err=True)
                raise typer.Exit(code=2)
            snapshot_cfg.fetch_mode = mode_normalized
    elif ticks:
        cfg.cli.default_generic_ticks = ticks

    # Determine effective universe path: CLI override > intraday_file > file
    if universe:
        effective_universe = Path(universe).expanduser().resolve()
    elif cfg.universe.intraday_file and cfg.universe.intraday_file.exists():
        effective_universe = cfg.universe.intraday_file
    else:
        effective_universe = cfg.universe.file

    trade_date = (
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None

    runner = SnapshotRunner(cfg, snapshot_grace_seconds=cfg.cli.snapshot_grace_seconds)
    try:
        slot_obj = runner.resolve_slot(trade_date, slot)
    except ValueError as exc:
        typer.echo(f"[snapshot] {exc}", err=True)
        raise typer.Exit(code=2)

    cfg_path = Path(config).resolve() if config else Path(cfg.paths.state).parent.resolve()
    typer.echo(
        "[snapshot:params] "
        f"config={cfg_path} universe={effective_universe} view=intraday slot={slot_obj.label} "
        f"symbols={symbol_list or 'ALL'} fetch_mode={snapshot_cfg.fetch_mode if snapshot_cfg else 'N/A'} "
        f"strikes_per_side={snapshot_cfg.strikes_per_side if snapshot_cfg else 'N/A'} "
        f"generic_ticks={snapshot_cfg.generic_ticks if snapshot_cfg else cfg.cli.default_generic_ticks} "
        f"market_data_type={cfg.ib.market_data_type} "
        f"paths.raw={cfg.paths.raw} paths.clean={cfg.paths.clean} "
        f"paths.state={cfg.paths.state} paths.run_logs={cfg.paths.run_logs}"
    )

    typer.echo(
        f"[snapshot] date={trade_date} slot={slot_obj.label} symbols={symbol_list or 'ALL'} "
        f"universe={effective_universe.name} force_refresh={force_refresh}"
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
            universe_path=effective_universe,
            ingest_run_type="intraday",
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
def close_snapshot(
    date_str: str = typer.Option("today", "--date", help="Trade date in ET or 'today'"),
    symbols: Optional[str] = typer.Option(
        None, "--symbols", help="Comma separated symbols (defaults to full universe)"
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    universe: Optional[str] = typer.Option(
        None, "--universe", help="Override universe file path (defaults to close_file or file)"
    ),
    build_missing_cache: bool = typer.Option(
        True,
        "--build-missing-cache/--fail-on-missing-cache",
        help="Automatically rebuild missing/invalid contract caches before running",
    ),
) -> None:
    """Capture only the end-of-day (close) snapshot for the given date."""

    cfg = load_config(Path(config) if config else None)
    snapshot_cfg = getattr(cfg, "snapshot", None)
    trade_date = (
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None

    # Determine effective universe path: CLI override > close_file > file
    if universe:
        effective_universe = Path(universe).expanduser().resolve()
    elif cfg.universe.close_file and cfg.universe.close_file.exists():
        effective_universe = cfg.universe.close_file
    else:
        effective_universe = cfg.universe.file

    universe_entries = load_universe(effective_universe)
    entries_by_symbol = {e.symbol: e for e in universe_entries}
    symbols_for_run: list[str]
    if symbol_list:
        symbols_for_run = symbol_list
    else:
        if not universe_entries:
            typer.echo(
                "[close-snapshot] no symbols available from universe for snapshot precheck", err=True
            )
            raise typer.Exit(code=1)
        symbols_for_run = [u.symbol for u in universe_entries]

    _precheck_contract_caches(
        cfg,
        trade_date,
        symbols_for_run,
        entries_by_symbol,
        universe_path=effective_universe,
        build_missing_cache=build_missing_cache,
        prefix="close-snapshot",
    )

    session_factory = lambda: IBSession(  # force delayed/replay data for EOD capture
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        client_id_pool=cfg.ib.client_id_pool,
        market_data_type=2,
    )

    runner = SnapshotRunner(
        cfg,
        snapshot_grace_seconds=cfg.cli.snapshot_grace_seconds,
        session_factory=session_factory,
    )
    slots = runner.available_slots(trade_date)
    if not slots:
        typer.echo(f"[close-snapshot] no slots available for {trade_date}", err=True)
        raise typer.Exit(code=1)
    close_slot = slots[-1]

    cfg_path = Path(config).resolve() if config else Path(cfg.paths.state).parent.resolve()
    typer.echo(
        "[close-snapshot:params] "
        f"config={cfg_path} universe={effective_universe} view=close slot={close_slot.label} "
        f"symbols={symbol_list or 'ALL'} fetch_mode={snapshot_cfg.fetch_mode if snapshot_cfg else 'N/A'} "
        f"strikes_per_side={snapshot_cfg.strikes_per_side if snapshot_cfg else 'N/A'} "
        f"generic_ticks={snapshot_cfg.generic_ticks if snapshot_cfg else cfg.cli.default_generic_ticks} "
        "market_data_type=2 "
        f"paths.raw={cfg.paths.raw} paths.clean={cfg.paths.clean} "
        f"paths.state={cfg.paths.state} paths.run_logs={cfg.paths.run_logs}"
    )

    typer.echo(
        f"[close-snapshot] date={trade_date} slot={close_slot.label} "
        f"universe={effective_universe.name} symbols={symbol_list or 'ALL'}"
    )

    def progress_cb(symbol: str, status: str, extra: Dict[str, Any]) -> None:
        parts = [f"[close-snapshot:{status}]", f"slot={close_slot.label}"]
        if symbol:
            parts.append(symbol)
        if extra:
            parts.append(", ".join(f"{k}={v}" for k, v in extra.items()))
        typer.echo(" ".join(parts))

    try:
        result = runner.run(
            trade_date,
            close_slot,
            symbol_list,
            universe_path=effective_universe,
            ingest_run_type="close_snapshot",
            view="close",
            progress=progress_cb,
        )
    except ValueError as exc:
        typer.echo(f"[close-snapshot] {exc}", err=True)
        raise typer.Exit(code=2)
    except Exception as exc:  # pragma: no cover - runtime specific
        typer.echo(f"[close-snapshot:error] {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(
        "[close-snapshot] "
        f"ingest_id={result.ingest_id} rows={result.rows_written} "
        f"raw_files={len(result.raw_paths)} clean_files={len(result.clean_paths)} "
        f"errors={len(result.errors)}"
    )
    if result.errors:
        for err in result.errors[:5]:
            typer.echo(
                "[close-snapshot:error] "
                f"symbol={err.get('symbol')} stage={err.get('stage')} error={err.get('error')}"
            )
        if len(result.errors) > 5:
            typer.echo(f"[close-snapshot] ... {len(result.errors) - 5} more errors logged")


@app.command()
def oi_probe(
    symbol: str = typer.Option("AAPL", "--symbol", "-s", help="Underlying symbol to probe"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    expiries: int = typer.Option(
        1,
        "--expiries",
        help="Number of expiries to probe starting from the offset",
    ),
    expiry_offset: int = typer.Option(
        1,
        "--expiry-offset",
        help="Skip this many nearest expiries before probing (default 1 => next expiry)",
    ),
    strikes: int = typer.Option(
        2,
        "--strikes-per-side",
        help="Number of strikes per side around spot (per expiry)",
    ),
    timeout: float = typer.Option(
        15.0,
        "--timeout",
        help="Max seconds to wait for tick 101 OI data",
    ),
    poll_interval: float = typer.Option(
        0.5,
        "--poll-interval",
        help="Polling interval while waiting for OI ticks",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional CSV output path (defaults under state/oi_probe)",
    ),
) -> None:
    """Probe real-time option open interest for a single underlying using tick 101.

    This is an operational helper and does not write to the main data/clean tree.
    """

    cfg = load_config(Path(config) if config else None)
    session = IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        client_id_pool=cfg.ib.client_id_pool,
        market_data_type=cfg.ib.market_data_type,
    )

    probe_cfg = OIProbeConfig(
        symbol=symbol.upper(),
        expiries=max(expiries, 1),
        expiry_offset=max(expiry_offset, 0),
        strikes_per_side=max(strikes, 1),
        timeout=max(timeout, 1.0),
        poll_interval=max(poll_interval, 0.1),
    )

    with session as sess:
        ib = sess.ensure_connected()
        typer.echo(
            f"[oi_probe] symbol={probe_cfg.symbol} expiries={probe_cfg.expiries} "
            f"expiry_offset={probe_cfg.expiry_offset} strikes_per_side={probe_cfg.strikes_per_side} "
            f"timeout={probe_cfg.timeout}s poll_interval={probe_cfg.poll_interval}s"
        )
        df = probe_oi(ib, probe_cfg)

    if df.empty:
        typer.echo("[oi_probe] no OI records collected (empty result)")
        raise typer.Exit(code=1)

    typer.echo(f"[oi_probe] records={len(df)} unique_strikes={df['strike'].nunique()}")
    preview = df.sort_values("open_interest", ascending=False).head(10)
    typer.echo(preview.to_string(index=False))

    if output:
        out_path = Path(output).expanduser()
    else:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out_dir = cfg.paths.state / "oi_probe"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"oi_probe_{probe_cfg.symbol}_{ts}.csv"

    df.to_csv(out_path, index=False)
    typer.echo(f"[oi_probe] written_csv={out_path}")


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
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
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
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
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
    simulate: bool = typer.Option(
        True, "--simulate/--live", help="Run jobs immediately for the day"
    ),
    snapshots: bool = typer.Option(
        True, "--snapshots/--skip-snapshots", help="Include snapshot jobs"
    ),
    rollup: bool = typer.Option(True, "--rollup/--skip-rollup", help="Include rollup job"),
    enrichment: bool = typer.Option(
        True, "--enrichment/--skip-enrichment", help="Include enrichment job"
    ),
    misfire_grace_seconds: int = typer.Option(300, help="Grace window for missed jobs (seconds)"),
    snapshot_interval_minutes: int = typer.Option(
        30,
        "--snapshot-interval-minutes",
        help="Minutes between intraday snapshot slots (default 30)",
    ),
    build_missing_cache: bool = typer.Option(
        True,
        "--build-missing-cache/--fail-on-missing-cache",
        help="Automatically rebuild missing/invalid contracts cache before scheduling",
    ),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
    )
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
    fields = (
        [f.strip().lower() for f in enrichment_fields.split(",") if f.strip()]
        if enrichment_fields
        else None
    )

    if snapshot_interval_minutes <= 0:
        typer.echo("--snapshot-interval-minutes must be positive", err=True)
        raise typer.Exit(code=2)

    symbols_for_run: list[str] = []
    effective_universe = (
        cfg.universe.intraday_file
        if cfg.universe.intraday_file and cfg.universe.intraday_file.exists()
        else cfg.universe.file
    )
    universe_entries = load_universe(effective_universe) if snapshots else []
    entries_by_symbol = {e.symbol: e for e in universe_entries}
    if snapshots:
        if symbol_list:
            symbols_for_run = symbol_list
        else:
            if not universe_entries:
                typer.echo(
                    "[schedule] no symbols available from universe for snapshot precheck", err=True
                )
                raise typer.Exit(code=1)
            symbols_for_run = [u.symbol for u in universe_entries]

        _precheck_contract_caches(
            cfg,
            trade_date,
            symbols_for_run,
            entries_by_symbol,
            universe_path=Path(effective_universe),
            build_missing_cache=build_missing_cache,
            prefix="schedule",
        )

    def format_progress(kind: str):
        def _progress(symbol: str, status: str, extra: Dict[str, Any]) -> None:
            parts = [f"[{kind}:{status}]"]
            if symbol:
                parts.append(symbol)
            slot_label = extra.get("slot")
            if slot_label:
                parts.append(f"slot={slot_label}")
            details = []
            for key, value in extra.items():
                if key == "slot":
                    continue
                details.append(f"{key}={value}")
            if details:
                parts.append(", ".join(details))
            typer.echo(" ".join(parts))

        return _progress

    snapshot_runner = SnapshotRunner(cfg, slot_minutes=snapshot_interval_minutes)
    slots_today = snapshot_runner.available_slots(trade_date)
    if not slots_today:
        typer.echo(f"[schedule] no snapshot slots available for {trade_date}", err=True)
        raise typer.Exit(code=1)
    close_slot_idx = slots_today[-1].index
    fallback_slot_idx = slots_today[-2].index if len(slots_today) >= 2 else close_slot_idx
    rollup_runner = RollupRunner(cfg, close_slot=close_slot_idx, fallback_slot=fallback_slot_idx)

    snapshot_progress = format_progress("snapshot")
    rollup_progress = format_progress("rollup")
    enrichment_progress = format_progress("enrichment")

    runner = ScheduleRunner(
        cfg,
        snapshot_runner=snapshot_runner,
        rollup_runner=rollup_runner,
    )
    jobs = runner.plan_day(
        trade_date,
        symbols=symbol_list,
        enrichment_fields=fields,
        include_snapshots=snapshots,
        include_rollup=rollup,
        include_enrichment=enrichment,
    )

    if not jobs:
        typer.echo(
            f"[schedule] no jobs planned for {trade_date} (non-trading day or all tasks skipped)"
        )
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
            snapshot_progress=snapshot_progress,
            rollup_progress=rollup_progress,
            enrichment_progress=enrichment_progress,
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
        typer.echo(
            "[schedule] APScheduler is not installed; install apscheduler>=3.10 to use --live",
            err=True,
        )
        raise typer.Exit(code=1)

    logging.getLogger("apscheduler").setLevel(logging.ERROR)
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
        snapshot_progress=snapshot_progress,
        rollup_progress=rollup_progress,
        enrichment_progress=enrichment_progress,
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
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
    )

    calculator = QAMetricsCalculator(cfg)
    result = calculator.evaluate(trade_date)

    typer.echo(
        f"[qa] trade_date={trade_date} status={result.status} breaches={result.breaches or 'NONE'}"
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
    log_warn_keywords: str = typer.Option(
        "No open interest data returned",
        help="Comma-separated keywords treated as WARN (non-fatal unless exceeding warn threshold)",
    ),
    log_max_total: int = typer.Option(
        0, help="Max allowed matches across keywords before failing (<=0 means any hit fails)"
    ),
    log_warn_max_total: int = typer.Option(
        10,
        help=(
            "Max allowed WARN keyword matches before failing "
            "(<=0 means any WARN hit fails; set negative to ignore)"
        ),
    ),
    log_warn_ratio_threshold: float = typer.Option(
        0.01,
        help=(
            "Additional WARN threshold as a ratio of daily rows; "
            "effective limit is max(log_warn_max_total, ceil(daily_rows * ratio)). "
            "Set to 0 to disable ratio-based threshold."
        ),
    ),
    write: bool = typer.Option(True, "--write/--no-write", help="Persist selfcheck JSON report"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    trade_date = (
        to_et_date(datetime.now(ZoneInfo("UTC"))) if date_str == "today" else date.fromisoformat(date_str)
    )

    qa_calc = QAMetricsCalculator(cfg)
    qa_result = qa_calc.evaluate(trade_date)

    fatal_keys = [k.strip() for k in log_keywords.split(",") if k.strip()]
    warn_keys = [k.strip() for k in log_warn_keywords.split(",") if k.strip()]
    all_keys = sorted(set(fatal_keys + warn_keys))
    counters, matched_files = scan_logs(cfg, trade_date, all_keys)

    fatal_counts = {k: counters.get(k, 0) for k in fatal_keys}
    warn_counts = {k: counters.get(k, 0) for k in warn_keys}
    fatal_total = sum(fatal_counts.values())
    warn_total = sum(warn_counts.values())

    status = "PASS"
    reasons: list[str] = []

    if qa_result.status != "PASS":
        status = "FAIL"
        reasons.extend(f"qa:{name}" for name in qa_result.breaches)

    if log_max_total >= 0 and fatal_total > log_max_total:
        status = "FAIL"
        reasons.append(f"logs:fatal_total>{log_max_total}")

    warn_thresholds: list[int] = []
    if log_warn_max_total >= 0:
        warn_thresholds.append(log_warn_max_total)
    daily_rows = int(qa_result.extra.get("daily_rows", 0) or 0)
    if log_warn_ratio_threshold > 0 and daily_rows > 0:
        warn_thresholds.append(math.ceil(daily_rows * log_warn_ratio_threshold))

    warn_threshold = max(warn_thresholds) if warn_thresholds else None
    if warn_threshold is not None and warn_total > warn_threshold:
        status = "FAIL"
        reasons.append(f"logs:warn_total>{warn_threshold}")

    typer.echo(
        f"[selfcheck] date={trade_date} status={status} fatal_log_matches={fatal_total} "
        f"warn_log_matches={warn_total} "
        f"qa_status={qa_result.status} reasons={reasons or 'NONE'}"
    )

    for metric in qa_result.metrics:
        typer.echo(
            f"[selfcheck:qa] {metric.name} value={metric.value:.4f} "
            f"threshold{metric.comparator}{metric.threshold:.4f} passed={metric.passed}"
        )

    if fatal_counts:
        for k, v in sorted(fatal_counts.items(), key=lambda kv: kv[0]):
            if v:
                typer.echo(f"[selfcheck:logs:fatal] keyword={k} count={v}")
    if warn_counts:
        for k, v in sorted(warn_counts.items(), key=lambda kv: kv[0]):
            if v:
                typer.echo(f"[selfcheck:logs:warn] keyword={k} count={v}")

    report = {
        "trade_date": trade_date.isoformat(),
        "status": status,
        "reasons": reasons,
        "qa": qa_result.as_dict(),
        "logs": {
            "fatal_keywords": fatal_keys,
            "warn_keywords": warn_keys,
            "fatal_total_matches": fatal_total,
            "warn_total_matches": warn_total,
            "counts": counters,
            "files_scanned": matched_files,
            "log_max_total": log_max_total,
            "log_warn_max_total": log_warn_max_total,
            "log_warn_ratio_threshold": log_warn_ratio_threshold,
            "log_warn_effective_threshold": warn_threshold,
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
    warn_keywords: str = typer.Option(
        "No open interest data returned",
        help="Comma-separated keywords treated as WARN (non-fatal unless exceeding warn threshold)",
    ),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    write_summary: bool = typer.Option(True, help="Write JSON summary under run_logs/errors"),
    max_total: int = typer.Option(0, help="Max allowed total matches before exiting with failure"),
    warn_max_total: int = typer.Option(
        10,
        help=(
            "Max allowed WARN keyword matches before exiting with failure "
            "(<=0 means any WARN hit fails; set negative to ignore)"
        ),
    ),
) -> None:
    """Aggregate errors and important markers from run logs for the given day."""
    cfg = load_config(Path(config) if config else None)

    def parse_et(value: str) -> date:
        if value == "today":
            return to_et_date(datetime.now(ZoneInfo("UTC")))
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

    fatal_keys = [k.strip() for k in keywords.split(",") if k.strip()]
    warn_keys = [k.strip() for k in warn_keywords.split(",") if k.strip()]
    all_keys = sorted(set(fatal_keys + warn_keys))
    counters, matched_files = scan_logs(cfg, target_day, all_keys)

    fatal_counts = {k: counters.get(k, 0) for k in fatal_keys}
    warn_counts = {k: counters.get(k, 0) for k in warn_keys}

    fatal_total = sum(fatal_counts.values())
    warn_total = sum(warn_counts.values())
    total_matches = sum(counters.values())

    summary = {
        "date": ymd,
        "fatal_keywords": fatal_keys,
        "warn_keywords": warn_keys,
        "files_scanned": matched_files,
        "counts": counters,
        "fatal_counts": fatal_counts,
        "warn_counts": warn_counts,
        "fatal_total_matches": fatal_total,
        "warn_total_matches": warn_total,
        "total_matches": total_matches,
    }
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))

    if write_summary:
        out_path = errors_dir / f"summary_{ymd_compact}.json"
        try:
            out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - fs issues
            typer.echo(f"[logscan] failed to write summary: {exc}", err=True)

    if max_total >= 0 and fatal_total > max_total:
        typer.echo(
            f"[logscan] fatal_total {fatal_total} exceeds max_total {max_total}", err=True
        )
        raise typer.Exit(code=1)

    if warn_max_total >= 0 and warn_total > warn_max_total:
        typer.echo(
            f"[logscan] warn_total {warn_total} exceeds warn_max_total {warn_max_total}", err=True
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
