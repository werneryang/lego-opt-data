from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

import math
import pandas as pd
import time

from ..config import AppConfig
from ..storage.layout import partition_for
from ..storage.writer import ParquetWriter
from ..util.performance import log_performance
from .cleaning import CleaningPipeline
from ..ib.session import IBSession

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    ingest_id: str
    trade_date: date
    symbols_processed: int
    rows_considered: int
    rows_updated: int
    daily_clean_paths: list[Path]
    daily_adjusted_paths: list[Path]
    enrichment_paths: list[Path]
    errors: list[dict[str, Any]]
    oi_stats: dict[str, int] | None = None
    oi_diffs: list[dict[str, Any]] | None = None


def _default_session_factory(cfg: AppConfig) -> IBSession:
    return IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        client_id_pool=cfg.ib.client_id_pool,
        market_data_type=cfg.ib.market_data_type,
    )


class EnrichmentRunner:
    SUPPORTED_FIELDS = {"open_interest"}

    def __init__(
        self,
        cfg: AppConfig,
        *,
        session_factory: callable[[], IBSession] | None = None,
        oi_fetcher: callable[..., tuple[int | float, date] | None] | None = None,
        writer: ParquetWriter | None = None,
        cleaner: CleaningPipeline | None = None,
        now_fn: callable[[], datetime] | None = None,
        oi_duration: str | None = None,
        oi_use_rth: bool | None = None,
    ) -> None:
        self.cfg = cfg
        self._session_factory = session_factory or (lambda: _default_session_factory(cfg))
        self._oi_fetcher = oi_fetcher  # Optional single-row fetcher for tests/overrides
        self._writer = writer or ParquetWriter(cfg)
        self._cleaner = cleaner or CleaningPipeline.create(cfg)
        self._now_fn = now_fn or datetime.utcnow
        self._oi_duration = oi_duration or cfg.enrichment.oi_duration
        self._oi_use_rth = oi_use_rth if oi_use_rth is not None else cfg.enrichment.oi_use_rth

    @log_performance(logger, "enrichment")
    def run(
        self,
        trade_date: date,
        symbols: Sequence[str] | None = None,
        *,
        fields: Sequence[str] | None = None,
        force_overwrite: bool = False,
        progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> EnrichmentResult:
        ingest_id = uuid.uuid4().hex
        errors: list[dict[str, Any]] = []
        enrichment_records: list[dict[str, Any]] = []
        daily_clean_paths: list[Path] = []
        daily_adjusted_paths: list[Path] = []
        enrichment_paths: list[Path] = []
        
        # Stats for overwrite comparison
        oi_stats = {"filled_from_missing": 0, "same": 0, "changed": 0}
        oi_diffs: list[dict[str, Any]] = []

        requested_fields = self._normalize_fields(fields)
        if not requested_fields:
            requested_fields = tuple(self.cfg.enrichment.fields)
        self._validate_fields(requested_fields)

        target_dir = Path(self.cfg.paths.clean) / f"view=daily_clean/date={trade_date.isoformat()}"
        if not target_dir.exists():
            return EnrichmentResult(
                ingest_id=ingest_id,
                trade_date=trade_date,
                symbols_processed=0,
                rows_considered=0,
                rows_updated=0,
                daily_clean_paths=daily_clean_paths,
                daily_adjusted_paths=daily_adjusted_paths,
                enrichment_paths=enrichment_paths,
                errors=errors,
            )

        wanted = {sym.upper() for sym in symbols} if symbols else None
        update_timestamp = self._now_fn()

        grand_total = 0  # total contracts to consider across all symbols
        total_updated = 0
        total_processed = 0  # counts successes + misses for progress reporting
        symbols_total = 0
        symbols_done = 0
        symbol_targets: dict[str, int] = defaultdict(int)  # symbol -> contracts needing OI
        remaining_per_symbol: dict[str, int] = {}
        completed_symbols: set[str] = set()
        total_considered = 0
        symbols_touched: set[str] = set()

        session = self._session_factory()
        error_file = Path(self.cfg.paths.run_logs) / "errors" / f"errors_{trade_date:%Y%m%d}.log"

        part_paths = sorted(target_dir.rglob("part-000.parquet"))
        if not part_paths:
            return EnrichmentResult(
                ingest_id=ingest_id,
                trade_date=trade_date,
                symbols_processed=0,
                rows_considered=0,
                rows_updated=0,
                daily_clean_paths=daily_clean_paths,
                daily_adjusted_paths=daily_adjusted_paths,
                enrichment_paths=enrichment_paths,
                errors=errors,
            )

        # Prescan to compute total work (additional read, but gives fixed totals for UI)
        for part_path in part_paths:
            try:
                df = pd.read_parquet(part_path)
            except Exception:
                continue  # actual run will log errors; skip for prescan
            if df.empty:
                continue
            underlying = str(df.get("underlying", pd.Series([""])).iloc[0]).upper()
            if wanted and underlying not in wanted:
                continue
            mask = df.apply(lambda r: _needs_open_interest(r, force_overwrite=force_overwrite), axis=1)
            considered = int(mask.sum())
            if considered == 0:
                continue
            symbol_targets[underlying] += considered
            grand_total += considered

        total_considered = grand_total
        symbols_total = len(symbol_targets)
        remaining_per_symbol = dict(symbol_targets)

        if progress and grand_total > 0:
            progress("", "init_total", {"total": grand_total, "symbols_total": symbols_total})

        if grand_total == 0:
            return EnrichmentResult(
                ingest_id=ingest_id,
                trade_date=trade_date,
                symbols_processed=0,
                rows_considered=0,
                rows_updated=0,
                daily_clean_paths=daily_clean_paths,
                daily_adjusted_paths=daily_adjusted_paths,
                enrichment_paths=enrichment_paths,
                errors=errors,
            )

        with session as sess:
            ib = sess.ensure_connected()
            # Enforce live market data for tick-101 path
            try:
                ib.reqMarketDataType(1)
            except Exception:
                pass
            for part_path in part_paths:
                try:
                    df = pd.read_parquet(part_path)
                except Exception as exc:
                    payload = {
                        "component": "enrichment",
                        "stage": "read_daily",
                        "file": str(part_path),
                        "error": str(exc),
                    }
                    errors.append(payload)
                    _write_error_line(error_file, payload)
                    continue

                if df.empty:
                    continue

                underlying = str(df.get("underlying", pd.Series([""])).iloc[0]).upper()
                exchange = str(df.get("exchange", pd.Series([""])).iloc[0]).upper()
                if wanted and underlying not in wanted:
                    continue

                mask = df.apply(lambda r: _needs_open_interest(r, force_overwrite=force_overwrite), axis=1)
                considered = int(mask.sum())
                if considered == 0:
                    continue

                updated_here = 0
                rows_to_fetch = df.loc[mask]
                use_custom_fetcher = self._oi_fetcher is not None
                batch_results: dict[int, tuple[int | float, date]] = {}
                if not use_custom_fetcher:
                    batch_results = self._fetch_batch_tick101(
                        ib,
                        rows_to_fetch,
                        trade_date,
                        timeout=8.0,
                        poll=0.25,
                        batch_size=30,
                        progress=progress,
                        symbol=underlying,
                    )

                for idx, row in rows_to_fetch.iterrows():
                    conid = int(row["conid"])
                    fetch_result: tuple[int | float, date] | None = None
                    fetch_error: Exception | None = None

                    if use_custom_fetcher:
                        try:
                            fetch_result = self._oi_fetcher(  # type: ignore[misc]
                                ib,
                                row,
                                trade_date,
                                duration=self._oi_duration,
                                use_rth=self._oi_use_rth,
                            )
                        except Exception as exc:  # pragma: no cover - passthrough for tests
                            fetch_error = exc
                    else:
                        fetch_result = batch_results.get(conid)

                    total_processed += 1

                    if fetch_result is None:
                        payload = {
                            "component": "enrichment",
                            "stage": "fetch_open_interest",
                            "symbol": underlying,
                            "exchange": exchange,
                            "conid": conid,
                            "message": "No open interest data returned"
                            if fetch_error is None
                            else str(fetch_error),
                        }
                        errors.append(payload)
                        _write_error_line(error_file, payload)
                        if progress:
                            progress(
                                underlying,
                                "open_interest_missing",
                                {
                                    "conid": conid,
                                    "done": total_processed,
                                    "total": grand_total,
                                    "symbol": underlying,
                                    "symbols_done": symbols_done,
                                    "symbols_total": symbols_total,
                                },
                            )
                        continue

                    oi_value, asof_date = fetch_result
                    
                    # Comparison logic
                    old_oi = row.get("open_interest")
                    if pd.isna(old_oi):
                        oi_stats["filled_from_missing"] += 1
                    else:
                        try:
                            # Compare as integers for safety, though they are floats
                            if int(float(old_oi)) == int(float(oi_value)):
                                oi_stats["same"] += 1
                            else:
                                oi_stats["changed"] += 1
                                if len(oi_diffs) < 100:  # Limit diffs size
                                    oi_diffs.append({
                                        "underlying": underlying,
                                        "conid": conid,
                                        "expiry": row.get("expiry"),
                                        "right": row.get("right"),
                                        "strike": row.get("strike"),
                                        "old_oi": old_oi,
                                        "new_oi": oi_value,
                                        "old_asof": row.get("oi_asof_date"),
                                        "new_asof": asof_date,
                                    })
                        except Exception:
                            # Fallback if conversion fails
                            oi_stats["changed"] += 1

                    df.at[idx, "open_interest"] = oi_value
                    df.at[idx, "oi_asof_date"] = pd.Timestamp(asof_date)
                    df.at[idx, "ingest_id"] = ingest_id
                    df.at[idx, "ingest_run_type"] = "enrichment"
                    df.at[idx, "data_quality_flag"] = _flags_after_success(
                        row.get("data_quality_flag"),
                        was_overwritten=force_overwrite and pd.notna(row.get("open_interest"))
                    )
                    updated_here += 1
                    total_updated += 1
                    symbols_touched.add(underlying)
                    enrichment_records.append(
                        {
                            "trade_date": pd.Timestamp(
                                row.get("trade_date", trade_date)
                            ).normalize(),
                            "underlying": underlying,
                            "exchange": exchange,
                            "conid": conid,
                            "fields_updated": ["open_interest"],
                            "open_interest": oi_value,
                            "oi_asof_date": pd.Timestamp(asof_date).normalize(),
                            "update_ts": update_timestamp,
                            "ingest_id": ingest_id,
                            "ingest_run_type": "enrichment",
                        }
                    )
                    if progress:
                        progress(
                            underlying,
                            "open_interest_updated",
                            {
                                "conid": conid,
                                "open_interest": oi_value,
                                "done": total_processed,
                                "total": grand_total,
                                "symbol": underlying,
                                "symbols_done": symbols_done,
                                "symbols_total": symbols_total,
                            },
                        )

                    # Track symbol completion based on prescan counts
                    if underlying in remaining_per_symbol:
                        remaining_per_symbol[underlying] -= 1
                        if remaining_per_symbol[underlying] <= 0 and underlying not in completed_symbols:
                            completed_symbols.add(underlying)
                            symbols_done += 1
                            if progress:
                                progress(
                                    underlying,
                                    "symbol_done",
                                    {
                                        "done": total_processed,
                                        "total": grand_total,
                                        "symbol": underlying,
                                        "symbols_done": symbols_done,
                                        "symbols_total": symbols_total,
                                    },
                                )

                if updated_here == 0:
                    continue

                try:
                    part = partition_for(
                        self.cfg,
                        Path(self.cfg.paths.clean) / "view=daily_clean",
                        trade_date,
                        underlying,
                        exchange,
                    )
                    daily_path = self._writer.write_dataframe(df, part)
                    daily_clean_paths.append(daily_path)
                except Exception as exc:  # pragma: no cover - IO errors
                    payload = {
                        "component": "enrichment",
                        "stage": "write_daily_clean",
                        "symbol": underlying,
                        "exchange": exchange,
                        "error": str(exc),
                    }
                    errors.append(payload)
                    _write_error_line(error_file, payload)
                    continue

                try:
                    adjusted = self._cleaner.adjuster.apply(df)
                    adj_part = partition_for(
                        self.cfg,
                        Path(self.cfg.paths.clean) / "view=daily_adjusted",
                        trade_date,
                        underlying,
                        exchange,
                    )
                    adj_path = self._writer.write_dataframe(adjusted, adj_part)
                    daily_adjusted_paths.append(adj_path)
                except Exception as exc:  # pragma: no cover - IO errors
                    payload = {
                        "component": "enrichment",
                        "stage": "write_daily_adjusted",
                        "symbol": underlying,
                        "exchange": exchange,
                        "error": str(exc),
                    }
                    errors.append(payload)
                    _write_error_line(error_file, payload)

        if enrichment_records:
            enrichment_root = Path(self.cfg.paths.clean) / "view=enrichment"
            grouped_records = defaultdict(list)
            for record in enrichment_records:
                key = (record["underlying"], record["exchange"])
                grouped_records[key].append(record)

            for (underlying, exchange), records in grouped_records.items():
                part = partition_for(self.cfg, enrichment_root, trade_date, underlying, exchange)
                existing = _read_parquet_optional(part.path() / "part-000.parquet")
                new_df = pd.DataFrame(records)
                combined = (
                    pd.concat([existing, new_df], ignore_index=True)
                    if existing is not None
                    else new_df
                )
                combined["fields_updated"] = combined["fields_updated"].apply(list)
                combined_path = self._writer.write_dataframe(combined, part)
                enrichment_paths.append(combined_path)

        return EnrichmentResult(
            ingest_id=ingest_id,
            trade_date=trade_date,
            symbols_processed=len(symbols_touched),
            rows_considered=total_considered,
            rows_updated=total_updated,
            daily_clean_paths=daily_clean_paths,
            daily_adjusted_paths=daily_adjusted_paths,
            enrichment_paths=enrichment_paths,
            errors=errors,
            oi_stats=oi_stats,
            oi_diffs=oi_diffs,
        )

    def _normalize_fields(self, fields: Sequence[str] | None) -> tuple[str, ...]:
        if not fields:
            return ()
        normalized = []
        for field in fields:
            token = field.strip()
            if not token:
                continue
            normalized.append(token.lower())
        return tuple(normalized)

    def _validate_fields(self, fields: Iterable[str]) -> None:
        unsupported = {field for field in fields if field not in self.SUPPORTED_FIELDS}
        if unsupported:
            raise ValueError(f"Unsupported enrichment fields: {sorted(unsupported)}")

    def _fetch_batch_tick101(
        self,
        ib: Any,
        rows: pd.DataFrame,
        trade_date: date,
        *,
        timeout: float = 15.0,
        poll: float = 0.25,
        batch_size: int = 50,
        progress: callable[[str, str, dict[str, Any]], None] | None = None,
        symbol: str | None = None,
    ) -> dict[int, tuple[int | float, date]]:
        from ib_insync import Option

        results: dict[int, tuple[int | float, date]] = {}
        if rows.empty:
            return results

        # Prepare contracts; no intra-batch concurrency to avoid pacing hits
        contracts: list[Option] = []
        for _, row in rows.iterrows():
            conid = int(row["conid"])
            exchange = row.get("exchange") or "SMART"
            contracts.append(Option(conId=conid, exchange=exchange))

        total_batches = math.ceil(len(contracts) / batch_size)
        # Process strictly sequentially: one batch after another, and inside each batch
        # request each contract serially before moving on.
        for i in range(0, len(contracts), batch_size):
            batch = contracts[i : i + batch_size]
            before = len(results)
            for c in batch:
                ticker = ib.reqMktData(c, "101", snapshot=False, regulatorySnapshot=False)
                deadline = time.time() + timeout
                while time.time() < deadline:
                    conid = ticker.contract.conId if ticker.contract else None
                    if conid is not None and conid not in results:
                        val = _extract_tick_oi(ticker, rows)
                        if val is not None and val > 0 and not math.isnan(val):
                            results[conid] = (float(val), trade_date)
                            break
                    # Use ib.sleep to allow the event loop to process incoming ticks
                    ib.sleep(poll)
                try:
                    ib.cancelMktData(c)
                except Exception:
                    pass

            if progress and symbol is not None:
                progress(
                    symbol,
                    "batch_done",
                    {
                        "batch_index": i // batch_size + 1,
                        "batches_total": total_batches,
                        "batch_size": len(batch),
                        "results_in_batch": len(results) - before,
                    },
                )

        return results


def _needs_open_interest(row: pd.Series, force_overwrite: bool = False) -> bool:
    if force_overwrite:
        return True
    oi = row.get("open_interest")
    # 已有有效 OI（>0 且非 NaN）则不再补
    try:
        if oi is not None and not (isinstance(oi, float) and pd.isna(oi)) and float(oi) > 0:
            return False
    except Exception:
        pass
    flags = _normalize_flags(row.get("data_quality_flag"))
    return "missing_oi" in flags or pd.isna(oi)


def _extract_tick_oi(ticker: Any, rows: pd.DataFrame) -> float | None:
    """
    Extract OI from ticker based on right; falls back to openInterest if needed.
    """
    if not ticker or not ticker.contract:
        return None
    conid = ticker.contract.conId
    row = rows.loc[rows["conid"] == conid].iloc[0]
    right = str(row.get("right", "")).upper()
    field_name = "callOpenInterest" if right.startswith("C") else "putOpenInterest"
    val = getattr(ticker, field_name, None)
    if val is None or (isinstance(val, float) and math.isnan(val)) or val <= 0:
        val = getattr(ticker, "openInterest", None)
    if val is None:
        return None
    try:
        if math.isnan(float(val)) or float(val) <= 0:
            return None
    except Exception:
        return None
    return float(val)


def _flags_after_success(value: Any, was_overwritten: bool = False) -> list[str]:
    flags = _normalize_flags(value)
    if "missing_oi" in flags:
        flags.remove("missing_oi")
    if "oi_enriched" not in flags:
        flags.append("oi_enriched")
    if was_overwritten and "oi_overwritten" not in flags:
        flags.append("oi_overwritten")
    return flags


def _normalize_flags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    if isinstance(value, (tuple, set)):
        return [str(v) for v in value if str(v)]
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed if str(v)]
            except Exception:
                pass
        return [text]
    return [str(value)]


def _read_parquet_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception:  # pragma: no cover - optional best effort
        return None


def _write_error_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        **payload,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _parse_bar_date(value: Any) -> date:
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
    if " " in text:
        text = text.split(" ")[0]
    return date.fromisoformat(text)
