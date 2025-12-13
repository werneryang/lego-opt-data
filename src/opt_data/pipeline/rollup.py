from __future__ import annotations

import json
import logging
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Sequence

import pandas as pd
import ast

from ..config import AppConfig
from ..storage.layout import partition_for
from ..storage.writer import ParquetWriter
from ..util.performance import log_performance
from ..util.memory import optimize_dataframe_dtypes
from ..quality import OptionMarketDataSchema, detect_anomalies
from ..quality.report import DailyQualityReport, QualityMetrics
from .cleaning import CleaningPipeline
from ..observability import MetricsCollector, AlertManager
import pandera.pandas as pa

logger = logging.getLogger(__name__)


@dataclass
class RollupResult:
    ingest_id: str
    trade_date: date
    rows_written: int
    symbols_processed: int
    strategy_counts: Dict[str, int]
    daily_clean_paths: list[Path]
    daily_adjusted_paths: list[Path]
    errors: list[dict[str, Any]]


class RollupRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        writer: ParquetWriter | None = None,
        cleaner: CleaningPipeline | None = None,
        close_slot: int | None = None,
        fallback_slot: int | None = None,
    ) -> None:
        self.cfg = cfg
        self._writer = writer or ParquetWriter(cfg)
        self._cleaner = cleaner or CleaningPipeline.create(cfg)
        # Use config values, with parameter overrides for backward compatibility
        self._close_slot = close_slot if close_slot is not None else cfg.rollup.close_slot
        self._fallback_slot = (
            fallback_slot if fallback_slot is not None else cfg.rollup.fallback_slot
        )
        self._allow_intraday_fallback = cfg.rollup.allow_intraday_fallback

        # Observability
        self.metrics = MetricsCollector(cfg.observability.metrics_db_path)
        self.alerts = AlertManager(cfg.observability.webhook_url)

    @log_performance(logger, "rollup")
    def run(
        self,
        trade_date: date,
        symbols: Sequence[str] | None = None,
        *,
        progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> RollupResult:
        ingest_id = uuid.uuid4().hex
        errors: list[dict[str, Any]] = []
        strategy_counter: Counter[str] = Counter()
        daily_clean_paths: list[Path] = []
        daily_adjusted_paths: list[Path] = []
        using_intraday_fallback = False
        schema_errors: list[str] = []
        quality_stats = {
            "total_rows": 0,
            "error_rows": 0,
            "missing_greeks": 0,
            "crossed_market": 0,
            "extreme_iv": 0,
        }
        symbols_written: set[str] = set()
        rows_written = 0

        error_file = Path(self.cfg.paths.run_logs) / "errors" / f"errors_{trade_date:%Y%m%d}.log"
        error_file.parent.mkdir(parents=True, exist_ok=True)

        wanted = {sym.upper() for sym in symbols} if symbols else None

        close_root = Path(self.cfg.paths.clean) / "view=close" / f"date={trade_date.isoformat()}"
        partition_dirs = self._list_partition_dirs(close_root)
        source_view = "close"

        if not partition_dirs:
            if not self._allow_intraday_fallback:
                payload = {
                    "component": "rollup",
                    "stage": "load_close",
                    "message": f"No close snapshot data for {trade_date}; intraday fallback disabled",
                }
                errors.append(payload)
                _write_error_line(error_file, payload)
                logger.error(
                    f"No close snapshot data for {trade_date}; set rollup.allow_intraday_fallback=true to use intraday data"
                )
                return RollupResult(
                    ingest_id=ingest_id,
                    trade_date=trade_date,
                    rows_written=0,
                    symbols_processed=0,
                    strategy_counts=dict(strategy_counter),
                    daily_clean_paths=daily_clean_paths,
                    daily_adjusted_paths=daily_adjusted_paths,
                    errors=errors,
                )

            logger.warning(f"No close snapshot for {trade_date}, falling back to intraday data")
            intraday_root = (
                Path(self.cfg.paths.clean) / "view=intraday" / f"date={trade_date.isoformat()}"
            )
            partition_dirs = self._list_partition_dirs(intraday_root)
            source_view = "intraday"
            using_intraday_fallback = True

        if not partition_dirs:
            return RollupResult(
                ingest_id=ingest_id,
                trade_date=trade_date,
                rows_written=0,
                symbols_processed=0,
                strategy_counts=dict(strategy_counter),
                daily_clean_paths=daily_clean_paths,
                daily_adjusted_paths=daily_adjusted_paths,
                errors=errors,
            )

        seen_symbols: set[str] = set()

        for part_dir in partition_dirs:
            underlying, exchange = self._partition_values(part_dir)
            if not underlying or not exchange:
                continue
            seen_symbols.add(underlying)
            if wanted and underlying not in wanted:
                continue

            df, read_errs = self._read_partition(part_dir)
            for err in read_errs:
                payload = {
                    "component": "rollup",
                    "stage": f"load_{source_view}",
                    "message": f"Failed to read parquet: {err['file']}: {err['error']}",
                }
                errors.append(payload)
                _write_error_line(error_file, payload)

            if df.empty:
                continue

            if "symbol" in df.columns and "underlying" not in df.columns:
                df["underlying"] = df["symbol"]
            if "underlying" not in df.columns:
                logger.warning("Missing 'underlying' column in rollup input; skipping partition")
                continue
            if "exchange" not in df.columns:
                df["exchange"] = exchange

            df["underlying"] = df["underlying"].astype(str).str.upper()
            df["exchange"] = df["exchange"].astype(str).str.upper()

            if "asof_ts" not in df.columns and "asof" in df.columns:
                df["asof_ts"] = pd.to_datetime(df["asof"], errors="coerce")

            if "snapshot_error" in df.columns:
                error_mask = df["snapshot_error"].fillna(False).astype(bool)
                error_count = int(error_mask.sum())
                if error_count > 0:
                    logger.warning(f"Filtering {error_count} error rows from rollup input")
                    df = df[~error_mask]

            if df.empty:
                continue

            selected, part_counter = self._select_rows(df)
            if selected.empty:
                continue
            strategy_counter.update(part_counter)

            selected["ingest_id"] = ingest_id
            selected["ingest_run_type"] = "eod_rollup"
            selected["rollup_source_slot"] = selected["slot_30m"].astype("int32")
            selected["rollup_source_time"] = pd.to_datetime(selected["sample_time"], utc=False)
            selected["trade_date"] = pd.to_datetime(selected["trade_date"]).dt.normalize()
            selected["underlying"] = selected["underlying"].astype(str).str.upper()
            selected["exchange"] = selected["exchange"].astype(str).str.upper()

            selected["data_quality_flag"] = selected["data_quality_flag"].apply(_ensure_flags)
            selected["data_quality_flag"] = selected["data_quality_flag"].apply(list)

            if using_intraday_fallback:
                selected["data_quality_flag"] = selected["data_quality_flag"].apply(
                    lambda flags: flags
                    if "fallback_intraday" in flags
                    else flags + ["fallback_intraday"]
                )
                logger.info(f"Added 'fallback_intraday' flag to {len(selected)} rows")

            selected["asof_ts"] = pd.to_datetime(
                selected["asof_ts"], utc=True, errors="coerce"
            ).dt.tz_convert(None)

            anomaly_flags = detect_anomalies(selected)
            selected["data_quality_flag"] = [
                list(set(existing + new))
                for existing, new in zip(selected["data_quality_flag"], anomaly_flags)
            ]

            try:
                OptionMarketDataSchema.validate(selected, lazy=True)
            except pa.errors.SchemaErrors as err:
                logger.warning(f"Schema validation failed with {len(err.failure_cases)} errors")
                for _, row in err.failure_cases.head(10).iterrows():
                    schema_errors.append(
                        f"{row['column']}: {row['check']} failed for value {row['failure_case']}"
                    )
                if len(err.failure_cases) > 10:
                    schema_errors.append(f"... and {len(err.failure_cases) - 10} more")
            except Exception as e:
                logger.warning(f"Schema validation error: {e}")
                schema_errors.append(str(e))

            quality_stats["total_rows"] += len(selected)
            symbols_written.add(underlying)
            if "snapshot_error" in selected.columns:
                quality_stats["error_rows"] += int(selected["snapshot_error"].fillna(False).sum())
            if "delta" in selected.columns:
                quality_stats["missing_greeks"] += int(selected["delta"].isna().sum())
            if "bid" in selected.columns and "ask" in selected.columns:
                quality_stats["crossed_market"] += int(
                    (
                        (selected["bid"] > selected["ask"])
                        & selected["bid"].notna()
                        & selected["ask"].notna()
                    ).sum()
                )
            if "iv" in selected.columns:
                quality_stats["extreme_iv"] += int((selected["iv"] > 5.0).sum())

            cols_to_drop = ["sample_time", "sample_time_et", "slot_30m", "first_seen_slot"]
            cleaned = selected.drop(columns=[c for c in cols_to_drop if c in selected.columns])

            daily_clean_root = Path(self.cfg.paths.clean) / "view=daily_clean"
            daily_adjusted_root = Path(self.cfg.paths.clean) / "view=daily_adjusted"

            for (u, ex), group in cleaned.groupby(["underlying", "exchange"]):
                group = group.sort_values("conid")
                part = partition_for(self.cfg, daily_clean_root, trade_date, u, ex)
                path = self._writer.write_dataframe(group, part)
                daily_clean_paths.append(path)
                rows_written += len(group)
                if progress:
                    progress(u, "write_daily_clean", {"rows": len(group)})

                adjusted = self._cleaner.adjuster.apply(group)
                part_adj = partition_for(self.cfg, daily_adjusted_root, trade_date, u, ex)
                path_adj = self._writer.write_dataframe(adjusted, part_adj)
                daily_adjusted_paths.append(path_adj)
                if progress:
                    progress(u, "write_daily_adjusted", {"rows": len(group)})

            del df, cleaned

        if wanted:
            missing = sorted(wanted - seen_symbols)
            for sym in missing:
                payload = {
                    "component": "rollup",
                    "stage": "missing_intraday",
                    "symbol": sym,
                    "message": "No intraday rows for symbol",
                }
                errors.append(payload)
                _write_error_line(error_file, payload)

        symbols_processed = len(symbols_written)

        if quality_stats["total_rows"] > 0:
            try:
                metrics = QualityMetrics(
                    total_rows=quality_stats["total_rows"],
                    symbols_count=symbols_processed,
                    error_rows_count=quality_stats["error_rows"],
                    crossed_market_count=quality_stats["crossed_market"],
                    missing_greeks_count=quality_stats["missing_greeks"],
                    extreme_iv_count=quality_stats["extreme_iv"],
                    schema_errors=schema_errors,
                )
                report = DailyQualityReport(
                    trade_date=trade_date.isoformat(),
                    generated_at=datetime.utcnow().isoformat(),
                    metrics=metrics,
                )
                report_dir = Path(self.cfg.paths.clean) / "reports" / "quality"
                report_path = report.save(report_dir)
                logger.info(f"Quality report generated: {report_path}")
            except Exception as e:
                logger.error(f"Failed to generate quality report: {e}")

        self.metrics.count("rollup.run.total", 1)
        self.metrics.count("rollup.rows_written", rows_written)
        self.metrics.count("rollup.symbols_processed", symbols_processed)
        if errors:
            self.metrics.count("rollup.errors", len(errors))
            self.alerts.send_alert(
                "Rollup Errors",
                f"Rollup encountered {len(errors)} errors for {trade_date}",
                level="warning",
            )

        return RollupResult(
            ingest_id=ingest_id,
            trade_date=trade_date,
            rows_written=rows_written,
            symbols_processed=symbols_processed,
            strategy_counts=dict(strategy_counter),
            daily_clean_paths=daily_clean_paths,
            daily_adjusted_paths=daily_adjusted_paths,
            errors=errors,
        )

    def _list_partition_dirs(self, root: Path) -> list[Path]:
        if not root.exists():
            return []
        return sorted({p.parent for p in root.rglob("*.parquet")})

    def _partition_values(self, part_dir: Path) -> tuple[str | None, str | None]:
        try:
            underlying_part = part_dir.parent.name
            exchange_part = part_dir.name
            underlying = (
                underlying_part.split("=", 1)[1]
                if "=" in underlying_part
                else underlying_part
            )
            exchange = exchange_part.split("=", 1)[1] if "=" in exchange_part else exchange_part
            return underlying.upper(), exchange.upper()
        except Exception:
            return None, None

    def _read_partition(self, part_dir: Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
        frames: list[pd.DataFrame] = []
        errors: list[dict[str, Any]] = []
        for parquet_path in sorted(part_dir.glob("*.parquet")):
            try:
                frames.append(pd.read_parquet(parquet_path))
            except Exception as exc:
                errors.append({"file": str(parquet_path), "error": str(exc)})
        if not frames:
            return pd.DataFrame(), errors

        df = pd.concat(frames, ignore_index=True)
        df = optimize_dataframe_dtypes(df, verbose=False)
        return df, errors

    def _load_intraday(self, trade_date: date) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
        root = Path(self.cfg.paths.clean) / "view=intraday" / f"date={trade_date.isoformat()}"
        if not root.exists():
            return pd.DataFrame(), []

        frames: list[pd.DataFrame] = []
        errors: list[dict[str, Any]] = []

        for parquet_path in sorted(root.rglob("*.parquet")):
            try:
                frames.append(pd.read_parquet(parquet_path))
            except Exception as exc:
                errors.append(
                    {
                        "file": str(parquet_path),
                        "error": str(exc),
                    }
                )
        if not frames:
            return pd.DataFrame(), errors
        df = pd.concat(frames, ignore_index=True)

        # Optimize memory usage by downcasting data types
        df = optimize_dataframe_dtypes(df, verbose=False)

        return df, errors

    def _load_close(self, trade_date: date) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
        """Load data from view=close for the given date."""
        root = Path(self.cfg.paths.clean) / "view=close" / f"date={trade_date.isoformat()}"
        if not root.exists():
            return pd.DataFrame(), []

        frames: list[pd.DataFrame] = []
        errors: list[dict[str, Any]] = []

        for parquet_path in sorted(root.rglob("*.parquet")):
            try:
                frames.append(pd.read_parquet(parquet_path))
            except Exception as exc:
                errors.append(
                    {
                        "file": str(parquet_path),
                        "error": str(exc),
                    }
                )
        if not frames:
            return pd.DataFrame(), errors
        df = pd.concat(frames, ignore_index=True)

        # Optimize memory usage by downcasting data types
        df = optimize_dataframe_dtypes(df, verbose=False)

        return df, errors

    def _select_rows(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Counter[str]]:
        work = df.copy()
        work["slot_30m"] = pd.to_numeric(work["slot_30m"], errors="coerce").astype("Int64")
        work["sample_time"] = pd.to_datetime(work["sample_time"], utc=False, errors="coerce")
        work["asof_ts"] = pd.to_datetime(work["asof_ts"], utc=True, errors="coerce").dt.tz_convert(
            None
        )

        work = work.dropna(subset=["slot_30m", "sample_time"])

        selections: list[pd.Series] = []
        counter: Counter[str] = Counter()

        group_keys = ["underlying", "exchange", "conid"]
        for _, group in work.groupby(group_keys, dropna=False):
            group = group.sort_values(["slot_30m", "sample_time", "asof_ts"])
            chosen: pd.Series | None = None
            strategy = "last_good"

            closing = group[group["slot_30m"] == self._close_slot]
            if not closing.empty:
                chosen = closing.iloc[-1].copy()
                strategy = "close"
            else:
                fallback = group[group["slot_30m"] == self._fallback_slot]
                if not fallback.empty:
                    chosen = fallback.iloc[-1].copy()
                    strategy = "slot_1530"
            if chosen is None:
                chosen = group.iloc[-1].copy()
                strategy = "last_good"

            chosen["rollup_strategy"] = strategy
            selections.append(chosen)
            counter[strategy] += 1

        if not selections:
            return pd.DataFrame(), counter

        selected_df = pd.DataFrame(selections)
        return selected_df, counter


def _ensure_flags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        try:
            return [str(v) for v in list(value)]
        except TypeError:
            pass
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed]
            except (ValueError, SyntaxError):
                pass
        return [value]
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [str(value)]


def _write_error_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        **payload,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
