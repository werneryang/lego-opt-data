from __future__ import annotations

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

import math
import pandas as pd

from ..config import AppConfig
from ..storage.layout import partition_for
from ..storage.writer import ParquetWriter
from ..util.ratelimit import TokenBucket
from .cleaning import CleaningPipeline
from ..ib.session import IBSession


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


def _default_session_factory(cfg: AppConfig) -> IBSession:
    return IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
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
        self._oi_fetcher = oi_fetcher or self._fetch_open_interest
        self._writer = writer or ParquetWriter(cfg)
        self._cleaner = cleaner or CleaningPipeline.create(cfg)
        self._now_fn = now_fn or datetime.utcnow
        self._oi_duration = oi_duration or cfg.enrichment.oi_duration
        self._oi_use_rth = oi_use_rth if oi_use_rth is not None else cfg.enrichment.oi_use_rth
        self._limiter = TokenBucket.create(
            capacity=cfg.rate_limits.historical.burst,
            refill_per_minute=cfg.rate_limits.historical.per_minute,
        )

    def run(
        self,
        trade_date: date,
        symbols: Sequence[str] | None = None,
        *,
        fields: Sequence[str] | None = None,
        progress: callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> EnrichmentResult:
        ingest_id = uuid.uuid4().hex
        errors: list[dict[str, Any]] = []
        enrichment_records: list[dict[str, Any]] = []
        daily_clean_paths: list[Path] = []
        daily_adjusted_paths: list[Path] = []
        enrichment_paths: list[Path] = []

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

        total_considered = 0
        total_updated = 0
        symbols_touched: set[str] = set()

        session = self._session_factory()
        error_file = Path(self.cfg.paths.run_logs) / "errors" / f"errors_{trade_date:%Y%m%d}.log"

        with session as sess:
            ib = sess.ensure_connected()
            for part_path in sorted(target_dir.rglob("part-000.parquet")):
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

                mask = df.apply(_needs_open_interest, axis=1)
                considered = int(mask.sum())
                if considered == 0:
                    continue

                total_considered += considered
                updated_here = 0

                for idx, row in df.loc[mask].iterrows():
                    conid = int(row["conid"])
                    fetch_result = self._fetch_with_limits(
                        ib,
                        row,
                        trade_date,
                    )
                    if fetch_result is None:
                        payload = {
                            "component": "enrichment",
                            "stage": "fetch_open_interest",
                            "symbol": underlying,
                            "exchange": exchange,
                            "conid": conid,
                            "message": "No open interest data returned",
                        }
                        errors.append(payload)
                        _write_error_line(error_file, payload)
                        if progress:
                            progress(
                                underlying,
                                "open_interest_missing",
                                {"conid": conid},
                            )
                        continue

                    oi_value, asof_date = fetch_result
                    df.at[idx, "open_interest"] = oi_value
                    df.at[idx, "oi_asof_date"] = pd.Timestamp(asof_date)
                    df.at[idx, "ingest_id"] = ingest_id
                    df.at[idx, "ingest_run_type"] = "enrichment"
                    df.at[idx, "data_quality_flag"] = _flags_after_success(
                        row.get("data_quality_flag")
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
                            {"conid": conid, "open_interest": oi_value},
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

    def _fetch_with_limits(
        self,
        ib: Any,
        row: pd.Series,
        trade_date: date,
    ) -> tuple[int | float, date] | None:
        while not self._limiter.try_acquire():
            # Simple sleep to avoid busy waiting
            import time

            time.sleep(0.1)
        return self._oi_fetcher(
            ib,
            row,
            trade_date,
            duration=self._oi_duration,
            use_rth=self._oi_use_rth,
        )

    def _fetch_open_interest(
        self,
        ib: Any,
        row: pd.Series,
        trade_date: date,
    ) -> tuple[int | float, date] | None:
        """Fetch previous-day OI via real-time tick 101 on T+1.

        This uses reqMktData + genericTickList='101' and reads callOpenInterest/putOpenInterest
        (or openInterest) from the ticker. It is intended to run on T+1 after the exchange
        has published end-of-day open interest.
        """

        from ib_insync import Contract  # type: ignore

        contract = Contract()
        contract.conId = int(row["conid"])
        contract.secType = "OPT"
        contract.exchange = row.get("exchange") or "SMART"
        contract.symbol = row.get("underlying") or row.get("symbol", "")
        contract.currency = row.get("currency") or "USD"

        try:
            ib.qualifyContracts(contract)
        except Exception:  # pragma: no cover - network specific
            return None

        try:
            ticker = ib.reqMktData(contract, genericTickList="101", snapshot=False)
        except Exception:  # pragma: no cover - network specific
            return None

        timeout = float(self.cfg.acquisition.historical_timeout)
        elapsed = 0.0
        right = str(row.get("right") or "").upper()

        def _extract_oi() -> float | None:
            # Prefer side-specific OI if available, fall back to openInterest
            if right == "C":
                value = getattr(ticker, "callOpenInterest", None)
            elif right == "P":
                value = getattr(ticker, "putOpenInterest", None)
            else:
                value = None
            if value is None:
                value = getattr(ticker, "openInterest", None)
            if value is None:
                return None
            try:
                num = float(value)
            except (TypeError, ValueError):
                return None
            if math.isnan(num) or num <= 0:
                return None
            return num

        oi_value: float | None = None
        try:
            while elapsed < timeout:
                oi_value = _extract_oi()
                if oi_value is not None:
                    break
                ib.sleep(0.5)
                elapsed += 0.5
        finally:
            try:
                ib.cancelMktData(contract)
            except Exception:  # pragma: no cover - best effort
                pass

        if oi_value is None:
            return None

        # Tick-101 OI reflects the latest published EOD open interest; on T+1 we
        # treat it as as-of the target trade_date.
        return oi_value, trade_date


def _needs_open_interest(row: pd.Series) -> bool:
    oi = row.get("open_interest")
    if pd.isna(oi):
        return True
    flags = _normalize_flags(row.get("data_quality_flag"))
    return "missing_oi" in flags


def _flags_after_success(value: Any) -> list[str]:
    flags = _normalize_flags(value)
    if "missing_oi" in flags:
        flags.remove("missing_oi")
    if "oi_enriched" not in flags:
        flags.append("oi_enriched")
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
