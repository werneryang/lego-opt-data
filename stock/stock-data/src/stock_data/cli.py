from __future__ import annotations

from pathlib import Path
import socket
from urllib.parse import urlparse
import typer

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .config import load_config
from .pipeline import (
    CorporateActionsRunner,
    DailyBarsRunner,
    FundamentalsRunner,
    VolatilityRunner,
)
from .pipeline.fundamentals import DEFAULT_FMP_BASE_URL
from .universe import load_universe


app = typer.Typer(add_completion=False, help="stock-data CLI entrypoint")


def _resolve_config_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    project_root = Path(__file__).resolve().parents[2]
    return project_root / path


def _load_cfg(path: str) -> object:
    return load_config(_resolve_config_path(path))


@app.command("inspect")
def inspect_config(config: str = "config/stock-data.toml") -> None:
    """Print resolved config paths."""
    cfg = _load_cfg(config)
    typer.echo(f"raw={cfg.paths.raw}")
    typer.echo(f"clean={cfg.paths.clean}")
    typer.echo(f"state={cfg.paths.state}")
    typer.echo(f"universe={cfg.universe.file}")


@app.command("list-universe")
def list_universe(config: str = "config/stock-data.toml", limit: int = 10) -> None:
    """List universe symbols."""
    cfg = _load_cfg(config)
    entries = load_universe(Path(cfg.universe.file))
    typer.echo(f"count={len(entries)}")
    for entry in entries[: max(limit, 0)]:
        typer.echo(entry.symbol)


def _parse_trade_date(value: str, tz_name: str) -> date:
    if value.lower() in {"today", "now"}:
        return datetime.now(ZoneInfo(tz_name)).date()
    return date.fromisoformat(value)


def _check_fmp_dns(base_url: str) -> None:
    host = urlparse(base_url).hostname or base_url
    try:
        socket.getaddrinfo(host, 443)
    except socket.gaierror as exc:
        raise typer.BadParameter(
            f"DNS lookup failed for {host}. Check network/DNS or FMP base URL."
        ) from exc


@app.command("daily-bars")
def daily_bars(
    config: str = "config/stock-data.toml",
    trade_date: str = "today",
    symbols: str = "",
    exchange: str = "SMART",
    currency: str = "USD",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
) -> None:
    """Fetch daily bars and write parquet output."""
    cfg = _load_cfg(config)
    target_date = _parse_trade_date(trade_date, cfg.timezone.name)
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or None
    runner = DailyBarsRunner(cfg)
    result = runner.run(
        trade_date=target_date,
        symbols=symbol_list,
        exchange=exchange,
        currency=currency,
        what_to_show=what_to_show,
        use_rth=use_rth,
    )
    typer.echo(f"ingest_id={result.ingest_id}")
    typer.echo(f"rows_written={result.rows_written}")
    if result.errors:
        typer.echo(f"errors={len(result.errors)}", err=True)


@app.command("volatility")
def volatility(
    config: str = "config/stock-data.toml",
    mode: str = "snapshot",
    trade_date: str = "today",
    end_date: str = "today",
    days: int = 365,
    symbols: str = "",
    exchange: str = "SMART",
    currency: str = "USD",
    generic_ticks: str = "106",
    timeout: float = 12.0,
    poll_interval: float = 0.25,
) -> None:
    """Fetch daily IV/HV snapshot or backfill history."""
    cfg = _load_cfg(config)
    runner = VolatilityRunner(cfg)
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or None

    mode_norm = mode.strip().lower()
    if mode_norm == "snapshot":
        target_date = _parse_trade_date(trade_date, cfg.timezone.name)
        result = runner.run_snapshot(
            trade_date=target_date,
            symbols=symbol_list,
            exchange=exchange,
            currency=currency,
            generic_ticks=generic_ticks,
            timeout=timeout,
            poll_interval=poll_interval,
        )
    elif mode_norm == "backfill":
        target_end = _parse_trade_date(end_date, cfg.timezone.name)
        result = runner.run_backfill(
            end_date=target_end,
            days=days,
            symbols=symbol_list,
            exchange=exchange,
            currency=currency,
        )
    else:
        raise typer.BadParameter("mode must be 'snapshot' or 'backfill'")

    typer.echo(f"ingest_id={result.ingest_id}")
    typer.echo(f"rows_written={result.rows_written}")
    if result.errors:
        typer.echo(f"errors={len(result.errors)}", err=True)


@app.command("fundamentals")
def fundamentals(
    config: str = "config/stock-data.toml",
    trade_date: str = "today",
    symbols: str = "",
    exchange: str = "SMART",
    report_types: str = "",
    force_refresh: bool = False,
    cache_ttl_days: int = 7,
    throttle_sec: float = 5.0,
    fmp_api_key: str = "",
    max_symbols: int = 0,
) -> None:
    """Fetch fundamentals reports and store raw JSON."""
    cfg = _load_cfg(config)
    _check_fmp_dns(DEFAULT_FMP_BASE_URL)
    target_date = _parse_trade_date(trade_date, cfg.timezone.name)
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or None
    types = [t.strip() for t in report_types.split(",") if t.strip()] or None
    runner = FundamentalsRunner(
        cfg,
        throttle_sec=throttle_sec,
        fmp_api_key=fmp_api_key.strip() or None,
    )
    result = runner.run(
        trade_date=target_date,
        symbols=symbol_list,
        exchange=exchange,
        report_types=types,
        force_refresh=force_refresh,
        cache_ttl_days=cache_ttl_days,
        max_symbols=max_symbols or None,
    )
    typer.echo(f"ingest_id={result.ingest_id}")
    typer.echo(f"rows_written={result.rows_written}")
    if result.errors:
        typer.echo(f"errors={len(result.errors)}", err=True)


@app.command("corporate-actions")
def corporate_actions(config: str = "config/stock-data.toml") -> None:
    """Load corporate actions from CSV and store parquet."""
    cfg = _load_cfg(config)
    runner = CorporateActionsRunner(cfg)
    result = runner.run()
    typer.echo(f"ingest_id={result.ingest_id}")
    typer.echo(f"rows_written={result.rows_written}")
    if result.errors:
        typer.echo(f"errors={len(result.errors)}", err=True)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
