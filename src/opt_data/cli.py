from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer

from .config import load_config
from .pipeline.backfill import BackfillPlanner, BackfillRunner
from .util.calendar import to_et_date


app = typer.Typer(add_completion=False, help="opt-data CLI entrypoint")


@app.command()
def backfill(
    start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    symbols: Optional[str] = typer.Option(None, help="Comma separated symbols, optional"),
    config: Optional[str] = typer.Option(None, help="Path to config TOML"),
    execute: bool = typer.Option(False, "--execute/--plan-only", help="Run backfill immediately"),
    limit: Optional[int] = typer.Option(
        None, help="Limit number of symbols to process during execution"
    ),
    force_refresh: bool = typer.Option(False, help="Ignore cached contracts when executing"),
) -> None:
    cfg = load_config(Path(config) if config else None)
    try:
        start_date = date.fromisoformat(start)
    except ValueError:
        typer.echo("Invalid --start date, expected YYYY-MM-DD", err=True)
        raise typer.Exit(code=2)

    selected = [s.strip().upper() for s in symbols.split(",")] if symbols else None

    planner = BackfillPlanner(cfg)
    queue = planner.plan(start_date, selected)
    queue_path = planner.queue_path(start_date)
    typer.echo(f"[backfill] planned {len(queue)} tasks -> {queue_path}")

    if execute:
        runner = BackfillRunner(cfg)
        processed = runner.run(
            start_date,
            selected,
            limit=limit,
            force_refresh=force_refresh,
        )
        typer.echo(f"[backfill] executed tasks={processed} output_root={cfg.paths.raw}")


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
