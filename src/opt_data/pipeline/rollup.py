from __future__ import annotations

import json
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
from .cleaning import CleaningPipeline


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
        close_slot: int = 13,
        fallback_slot: int = 12,
    ) -> None:
        self.cfg = cfg
        self._writer = writer or ParquetWriter(cfg)
        self._cleaner = cleaner or CleaningPipeline.create(cfg)
        self._close_slot = close_slot
        self._fallback_slot = fallback_slot

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

        error_file = Path(self.cfg.paths.run_logs) / "errors" / f"errors_{trade_date:%Y%m%d}.log"
        error_file.parent.mkdir(parents=True, exist_ok=True)

        intraday_df, read_errors = self._load_intraday(trade_date)
        for err in read_errors:
            err.update({"component": "rollup", "stage": "read_intraday"})
            errors.append(err)
            _write_error_line(error_file, err)

        if symbols:
            wanted = {sym.upper() for sym in symbols}
            have = {sym.upper() for sym in intraday_df.get("underlying", pd.Series(dtype="str")).unique()}
            missing = sorted(wanted - have)
            for sym in missing:
                payload = {
                    "component": "rollup",
                    "stage": "missing_intraday",
                    "symbol": sym,
                    "message": "No intraday rows for symbol",
                }
                errors.append(payload)
                _write_error_line(error_file, payload)
            intraday_df = intraday_df[intraday_df["underlying"].str.upper().isin(wanted)]

        if intraday_df.empty:
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

        selected, strategy_counter = self._select_rows(intraday_df)
        if selected.empty:
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

        selected["ingest_id"] = ingest_id
        selected["ingest_run_type"] = "eod_rollup"
        selected["rollup_source_slot"] = selected["slot_30m"].astype("int32")
        selected["rollup_source_time"] = pd.to_datetime(selected["sample_time"], utc=False)
        selected["trade_date"] = pd.to_datetime(selected["trade_date"]).dt.normalize()
        selected["underlying"] = selected["underlying"].astype(str).str.upper()
        selected["exchange"] = selected["exchange"].astype(str).str.upper()

        selected["data_quality_flag"] = selected["data_quality_flag"].apply(_ensure_flags)
        selected["data_quality_flag"] = selected["data_quality_flag"].apply(list)
        selected["asof_ts"] = pd.to_datetime(selected["asof_ts"], utc=True, errors="coerce").dt.tz_convert(
            None
        )

        cols_to_drop = ["sample_time", "sample_time_et", "slot_30m", "first_seen_slot"]
        cleaned = selected.drop(columns=[c for c in cols_to_drop if c in selected.columns])

        daily_clean_root = Path(self.cfg.paths.clean) / "view=daily_clean"
        daily_adjusted_root = Path(self.cfg.paths.clean) / "view=daily_adjusted"

        rows_written = 0
        for (underlying, exchange), group in cleaned.groupby(["underlying", "exchange"]):
            group = group.sort_values("conid")
            part = partition_for(self.cfg, daily_clean_root, trade_date, underlying, exchange)
            path = self._writer.write_dataframe(group, part)
            daily_clean_paths.append(path)
            rows_written += len(group)
            if progress:
                progress(underlying, "write_daily_clean", {"rows": len(group)})

            adjusted = self._cleaner.adjuster.apply(group)
            part_adj = partition_for(self.cfg, daily_adjusted_root, trade_date, underlying, exchange)
            path_adj = self._writer.write_dataframe(adjusted, part_adj)
            daily_adjusted_paths.append(path_adj)
            if progress:
                progress(underlying, "write_daily_adjusted", {"rows": len(group)})

        symbols_processed = cleaned["underlying"].nunique()
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
        return df, errors

    def _select_rows(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Counter[str]]:
        work = df.copy()
        work["slot_30m"] = pd.to_numeric(work["slot_30m"], errors="coerce").astype("Int64")
        work["sample_time"] = pd.to_datetime(work["sample_time"], utc=False, errors="coerce")
        work["asof_ts"] = pd.to_datetime(work["asof_ts"], utc=True, errors="coerce").dt.tz_convert(None)

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
