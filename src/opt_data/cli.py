from __future__ import annotations

import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import typer

from .config import load_config
from .pipeline.backfill import BackfillPlanner, BackfillRunner
from .util.calendar import to_et_date, is_trading_day


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
def update(
    date_arg: str = typer.Option("today", "--date", help="Update date YYYY-MM-DD or 'today'"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    if date_arg == "today":
        d = to_et_date(datetime.utcnow())
    else:
        d = date.fromisoformat(date_arg)
    typer.echo(f"[update] date={d} clean_root={cfg.paths.clean}")


@app.command()
def compact(
    older_than: int = typer.Option(14, help="Compact partitions older than N days"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    typer.echo(f"[compact] older_than={older_than} data_roots=[{cfg.paths.raw}, {cfg.paths.clean}]")


@app.command()
def inspect(
    what: str = typer.Argument("config", help="What to inspect: config|paths"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    if what == "config":
        typer.echo(repr(cfg))
    elif what == "paths":
        typer.echo(f"raw={cfg.paths.raw}\nclean={cfg.paths.clean}\nstate={cfg.paths.state}")
    else:
        typer.echo("Unknown inspect target", err=True)
        raise typer.Exit(code=2)


def main(argv: list[str] | None = None) -> int:
    try:
        app()
        return 0
    except SystemExit as e:
        return int(e.code)


if __name__ == "__main__":
    sys.exit(main())
