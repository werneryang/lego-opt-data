from __future__ import annotations

from pathlib import Path
import json
import logging
import shutil
import socket
import time
from urllib.parse import urlparse
import typer

from datetime import date, datetime, time as dtime, timedelta
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


@app.callback()
def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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


def _parse_run_time(value: str) -> dtime:
    raw = value.strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    raise typer.BadParameter("run-time must be HH:MM or HH:MM:SS")


def _parse_date_dir(name: str) -> date | None:
    if not name.startswith("date="):
        return None
    value = name.replace("date=", "", 1)
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _next_run_at(now: datetime, run_time: dtime) -> datetime:
    candidate = now.replace(
        hour=run_time.hour,
        minute=run_time.minute,
        second=run_time.second,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_months(value: date, months: int) -> date:
    total = value.year * 12 + (value.month - 1) + months
    year = total // 12
    month = total % 12 + 1
    return date(year, month, 1)


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
    mode: str = "snapshot",
    trade_date: str = "today",
    end_date: str = "today",
    days: int = 365,
    auto_from_latest: bool = typer.Option(
        False,
        help="Start from latest existing date per symbol; falls back to --days if no data.",
    ),
    symbols: str = "",
    exchange: str = "SMART",
    currency: str = "USD",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    throttle_sec: float = 0.7,
    batch_size: int = 50,
) -> None:
    """Fetch daily bars and write parquet output."""
    cfg = _load_cfg(config)
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or None
    runner = DailyBarsRunner(cfg, throttle_sec=throttle_sec)
    mode_norm = mode.strip().lower()
    if mode_norm == "snapshot":
        target_date = _parse_trade_date(trade_date, cfg.timezone.name)
        result = runner.run(
            trade_date=target_date,
            symbols=symbol_list,
            exchange=exchange,
            currency=currency,
            what_to_show=what_to_show,
            use_rth=use_rth,
            batch_size=batch_size,
        )
    elif mode_norm == "backfill":
        target_end = _parse_trade_date(end_date, cfg.timezone.name)
        result = runner.run_backfill(
            end_date=target_end,
            days=days,
            auto_from_latest=auto_from_latest,
            symbols=symbol_list,
            exchange=exchange,
            currency=currency,
            what_to_show=what_to_show,
            use_rth=use_rth,
            batch_size=batch_size,
        )
    else:
        raise typer.BadParameter("mode must be 'snapshot' or 'backfill'")
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
    auto_from_latest: bool = typer.Option(
        False,
        help="Start from latest existing date per symbol; falls back to --days if no data.",
    ),
    symbols: str = "",
    exchange: str = "SMART",
    currency: str = "USD",
    generic_ticks: str = "106",
    timeout: float = 12.0,
    poll_interval: float = 0.25,
    throttle_sec: float = 0.7,
    batch_size: int = 50,
) -> None:
    """Fetch daily IV/HV snapshot or backfill history."""
    cfg = _load_cfg(config)
    runner = VolatilityRunner(cfg, throttle_sec=throttle_sec)
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
            batch_size=batch_size,
        )
    elif mode_norm == "backfill":
        target_end = _parse_trade_date(end_date, cfg.timezone.name)
        result = runner.run_backfill(
            end_date=target_end,
            days=days,
            auto_from_latest=auto_from_latest,
            symbols=symbol_list,
            exchange=exchange,
            currency=currency,
            batch_size=batch_size,
        )
    else:
        raise typer.BadParameter("mode must be 'snapshot' or 'backfill'")

    typer.echo(f"ingest_id={result.ingest_id}")
    typer.echo(f"rows_written={result.rows_written}")
    if result.errors:
        typer.echo(f"errors={len(result.errors)}", err=True)


@app.command("cleanup")
def cleanup(
    config: str = "config/stock-data.toml",
    keep_months: int = typer.Option(
        2, help="Keep the most recent N months including the current month."
    ),
    dry_run: bool = typer.Option(False, help="Print deletions without removing data."),
    views: str = typer.Option(
        "daily_bars,volatility", help="Comma-separated views to clean."
    ),
    merged_view: str = typer.Option(
        "price_volatility_monthly",
        help="Merged output view name (stored under view=...).",
    ),
    log_path: str = typer.Option(
        "",
        help="JSONL log path (default: state/run_logs/cleanup_YYYYMMDD_HHMMSS.jsonl).",
    ),
    remove_source: bool = typer.Option(
        False, help="Remove old date partitions after compaction."
    ),
) -> None:
    """Compact old partitions into a merged monthly dataset and optionally delete sources."""
    if keep_months < 1:
        raise typer.BadParameter("keep-months must be >= 1")
    if not merged_view:
        raise typer.BadParameter("merged-view must be non-empty")
    cfg = _load_cfg(config)
    tz_name = cfg.timezone.name
    today = datetime.now(ZoneInfo(tz_name)).date()
    cutoff = _shift_months(_month_start(today), -(keep_months - 1))
    log_dir = cfg.paths.state / "run_logs"
    timestamp = datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%d_%H%M%S")
    log_target = Path(log_path) if log_path else (log_dir / f"cleanup_{timestamp}.jsonl")
    log_target = log_target.expanduser()
    log_target.parent.mkdir(parents=True, exist_ok=True)

    view_names = [v.strip() for v in views.split(",") if v.strip()]
    if set(view_names) != {"daily_bars", "volatility"}:
        raise typer.BadParameter("views must be 'daily_bars,volatility'")

    price_root = cfg.paths.clean / "view=daily_bars"
    vol_root = cfg.paths.clean / "view=volatility"
    merged_root = cfg.paths.clean / f"view={merged_view}"

    log_fh = None
    try:
        log_fh = log_target.open("a", encoding="utf-8")
    except Exception as exc:
        typer.echo(f"[cleanup] failed to open log file {log_target}: {exc}", err=True)
        log_fh = None

    def _log(event: dict) -> None:
        if not log_fh:
            return
        log_fh.write(json.dumps(event, ensure_ascii=True) + "\n")
        log_fh.flush()

    _log(
        {
            "event": "cleanup_start",
            "timestamp": datetime.now(ZoneInfo(tz_name)).isoformat(),
            "cutoff": cutoff.isoformat(),
            "keep_months": keep_months,
            "dry_run": dry_run,
            "remove_source": remove_source,
            "merged_view": merged_view,
            "views": view_names,
        }
    )

    if not price_root.exists() and not vol_root.exists():
        typer.echo("[cleanup] no source views found")
        _log({"event": "cleanup_end", "status": "no_source_views"})
        if log_fh:
            log_fh.close()
        return

    def _collect_files(view_root: Path) -> tuple[dict[tuple[str, str, int, int], list[Path]], set[Path]]:
        groups: dict[tuple[str, str, int, int], list[Path]] = {}
        date_dirs: set[Path] = set()
        if not view_root.exists():
            return groups, date_dirs
        for date_dir in sorted(view_root.glob("date=*")):
            if not date_dir.is_dir():
                continue
            parsed = _parse_date_dir(date_dir.name)
            if parsed is None or parsed >= cutoff:
                continue
            date_dirs.add(date_dir)
            year = parsed.year
            month = parsed.month
            for symbol_dir in date_dir.glob("symbol=*"):
                if not symbol_dir.is_dir():
                    continue
                symbol = symbol_dir.name.replace("symbol=", "", 1)
                for exchange_dir in symbol_dir.glob("exchange=*"):
                    if not exchange_dir.is_dir():
                        continue
                    exchange = exchange_dir.name.replace("exchange=", "", 1)
                    key = (symbol, exchange, year, month)
                    groups.setdefault(key, []).extend(sorted(exchange_dir.glob("part-*.parquet")))
        return groups, date_dirs

    price_groups, price_dates = _collect_files(price_root)
    vol_groups, vol_dates = _collect_files(vol_root)
    all_keys = sorted({*price_groups.keys(), *vol_groups.keys()})
    if not all_keys:
        typer.echo("[cleanup] no partitions older than cutoff")
        _log({"event": "cleanup_end", "status": "no_partitions", "cutoff": cutoff.isoformat()})
        if log_fh:
            log_fh.close()
        return

    import pandas as pd  # type: ignore
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore

    codec = cfg.storage.cold_codec
    options = {}
    if codec.lower() == "zstd":
        options = {"compression_level": cfg.storage.cold_codec_level}

    had_errors = False
    missing_price_total = 0
    missing_vol_total = 0
    for key in all_keys:
        symbol, exchange, year, month = key
        price_files = price_groups.get(key, [])
        vol_files = vol_groups.get(key, [])
        if not price_files and not vol_files:
            continue
        month_dir = (
            merged_root
            / f"symbol={symbol}"
            / f"year={year}"
            / f"month={month:02d}"
            / f"exchange={exchange}"
        )
        output_path = month_dir / "part-000.parquet"

        if dry_run:
            typer.echo(
                f"[cleanup] dry-run merge {symbol} {exchange} {year}-{month:02d} "
                f"price_files={len(price_files)} vol_files={len(vol_files)} -> {output_path}"
            )
            _log(
                {
                    "event": "merge_plan",
                    "symbol": symbol,
                    "exchange": exchange,
                    "year": year,
                    "month": month,
                    "price_files": len(price_files),
                    "vol_files": len(vol_files),
                    "output_path": str(output_path),
                }
            )
            continue

        try:
            price_frames: list[pd.DataFrame] = []
            vol_frames: list[pd.DataFrame] = []
            if output_path.exists():
                price_frames.append(pd.read_parquet(output_path))
            for path in price_files:
                price_frames.append(pd.read_parquet(path))
            for path in vol_files:
                vol_frames.append(pd.read_parquet(path))
            price_df = pd.concat(price_frames, ignore_index=True) if price_frames else pd.DataFrame()
            vol_df = pd.concat(vol_frames, ignore_index=True) if vol_frames else pd.DataFrame()
            if price_df.empty and vol_df.empty:
                continue

            for df in (price_df, vol_df):
                if not df.empty:
                    if "symbol" in df.columns:
                        df["symbol"] = df["symbol"].astype(str).str.upper()
                    if "exchange" in df.columns:
                        df["exchange"] = df["exchange"].astype(str).str.upper()
                    if "trade_date" in df.columns:
                        df["trade_date"] = pd.to_datetime(
                            df["trade_date"], errors="coerce"
                        ).dt.date

            if price_df.empty:
                merged = vol_df.copy()
                missing_price = len(merged)
                missing_vol = 0
            elif vol_df.empty:
                merged = price_df.copy()
                missing_price = 0
                missing_vol = len(merged)
            else:
                merged = price_df.merge(
                    vol_df,
                    on=["trade_date", "symbol", "exchange"],
                    how="outer",
                    suffixes=("_price", "_vol"),
                    indicator=True,
                )
                missing_vol = int((merged["_merge"] == "left_only").sum())
                missing_price = int((merged["_merge"] == "right_only").sum())
                merged = merged.drop(columns=["_merge"])

            missing_price_total += missing_price
            missing_vol_total += missing_vol
            if missing_price or missing_vol:
                typer.echo(
                    f"[cleanup] mismatch {symbol} {exchange} {year}-{month:02d} "
                    f"missing_price={missing_price} missing_volatility={missing_vol}",
                    err=True,
                )
            _log(
                {
                    "event": "merge_result",
                    "symbol": symbol,
                    "exchange": exchange,
                    "year": year,
                    "month": month,
                    "rows": int(len(merged)),
                    "missing_price": missing_price,
                    "missing_volatility": missing_vol,
                    "output_path": str(output_path),
                }
            )

            subset = [c for c in ("trade_date", "symbol", "exchange") if c in merged.columns]
            if subset:
                merged = merged.drop_duplicates(subset=subset, keep="last")
            if "trade_date" in merged.columns:
                merged = merged.sort_values(by=["trade_date"])

            month_dir.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pandas(merged, preserve_index=False)
            pq.write_table(table, output_path, compression=codec, **options)
            typer.echo(
                f"[cleanup] merged {symbol} {exchange} {year}-{month:02d} rows={len(merged)}"
            )
        except Exception as exc:
            had_errors = True
            typer.echo(
                f"[cleanup] failed {symbol} {exchange} {year}-{month:02d}: {exc}",
                err=True,
            )
            _log(
                {
                    "event": "merge_error",
                    "symbol": symbol,
                    "exchange": exchange,
                    "year": year,
                    "month": month,
                    "error": str(exc),
                }
            )

    if remove_source:
        if dry_run:
            for date_dir in sorted(price_dates | vol_dates):
                typer.echo(f"[cleanup] dry-run delete {date_dir}")
        elif had_errors:
            typer.echo(
                "[cleanup] errors encountered; source partitions preserved",
                err=True,
            )
        else:
            for date_dir in sorted(price_dates | vol_dates):
                shutil.rmtree(date_dir)
                typer.echo(f"[cleanup] deleted {date_dir}")
        _log(
            {
                "event": "source_cleanup",
                "remove_source": True,
                "deleted_partitions": len(price_dates | vol_dates) if not dry_run else 0,
                "had_errors": had_errors,
            }
        )

    typer.echo(
        f"[cleanup] cutoff={cutoff.isoformat()} merged_groups={len(all_keys)} "
        f"missing_price_total={missing_price_total} missing_volatility_total={missing_vol_total} "
        f"delete_sources={remove_source}"
    )
    _log(
        {
            "event": "cleanup_end",
            "status": "ok" if not had_errors else "partial",
            "cutoff": cutoff.isoformat(),
            "merged_groups": len(all_keys),
            "missing_price_total": missing_price_total,
            "missing_volatility_total": missing_vol_total,
            "delete_sources": remove_source,
        }
    )
    if log_fh:
        log_fh.close()


@app.command("schedule")
def schedule(
    config: str = "config/stock-data.toml",
    run_time: str | None = typer.Option(
        None, help="Daily run time in HH:MM or HH:MM:SS (defaults to config timezone.update_time)."
    ),
    days: int = 365,
    auto_from_latest: bool = typer.Option(
        True,
        help="Start from latest existing date per symbol; falls back to --days if no data.",
    ),
    symbols: str = "",
    exchange: str = "SMART",
    currency: str = "USD",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    throttle_sec: float = 0.7,
    batch_size: int = 50,
) -> None:
    """Run daily bars and volatility backfill on a daily schedule."""
    cfg = _load_cfg(config)
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or None
    tz_name = cfg.timezone.name
    schedule_value = run_time or cfg.timezone.update_time or "16:30"
    schedule_time = _parse_run_time(schedule_value)

    daily_runner = DailyBarsRunner(cfg, throttle_sec=throttle_sec)
    vol_runner = VolatilityRunner(cfg, throttle_sec=throttle_sec)

    while True:
        now = datetime.now(ZoneInfo(tz_name))
        next_run = _next_run_at(now, schedule_time)
        sleep_seconds = max(0.0, (next_run - now).total_seconds())
        typer.echo(f"[schedule] next_run={next_run.isoformat()}")
        time.sleep(sleep_seconds)

        target_end = datetime.now(ZoneInfo(tz_name)).date()
        try:
            result = daily_runner.run_backfill(
                end_date=target_end,
                days=days,
                auto_from_latest=auto_from_latest,
                symbols=symbol_list,
                exchange=exchange,
                currency=currency,
                what_to_show=what_to_show,
                use_rth=use_rth,
                batch_size=batch_size,
            )
            typer.echo(
                f"[schedule] daily-bars rows_written={result.rows_written} errors={len(result.errors)}"
            )
        except Exception as exc:
            typer.echo(f"[schedule] daily-bars failed: {exc}", err=True)

        try:
            result = vol_runner.run_backfill(
                end_date=target_end,
                days=days,
                auto_from_latest=auto_from_latest,
                symbols=symbol_list,
                exchange=exchange,
                currency=currency,
                batch_size=batch_size,
            )
            typer.echo(
                f"[schedule] volatility rows_written={result.rows_written} errors={len(result.errors)}"
            )
        except Exception as exc:
            typer.echo(f"[schedule] volatility failed: {exc}", err=True)

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
