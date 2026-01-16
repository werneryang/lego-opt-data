from __future__ import annotations

import csv
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import AppConfig
from ..storage import ParquetWriter, partition_for


@dataclass
class CorporateActionsResult:
    ingest_id: str
    rows_written: int
    paths: list[str]
    errors: list[dict[str, Any]]


def _parse_date(value: str) -> date | None:
    raw = value.strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


class CorporateActionsRunner:
    def __init__(self, cfg: AppConfig, *, writer: ParquetWriter | None = None) -> None:
        self.cfg = cfg
        self._writer = writer or ParquetWriter(cfg)

    def run(self, *, source_path: Path | None = None) -> CorporateActionsResult:
        ingest_id = str(uuid.uuid4())
        errors: list[dict[str, Any]] = []
        paths: list[str] = []
        rows_written = 0

        src = source_path or self.cfg.reference.corporate_actions
        if not src.exists():
            errors.append({"error": "missing_source", "message": str(src)})
            return CorporateActionsResult(
                ingest_id=ingest_id,
                rows_written=0,
                paths=[],
                errors=errors,
            )

        with src.open("r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(row for row in fh if not row.startswith("#"))
            for row in reader:
                symbol = (row.get("symbol") or "").strip().upper()
                event_date = _parse_date(row.get("event_date", ""))
                event_type = (row.get("event_type") or "").strip().lower()
                ratio_raw = (row.get("ratio") or "").strip()
                cash_raw = (row.get("cash_amount") or "").strip()
                notes = (row.get("notes") or "").strip()

                if not symbol or not event_date or not event_type:
                    errors.append(
                        {
                            "error": "invalid_row",
                            "row": row,
                        }
                    )
                    continue

                ratio = float(ratio_raw) if ratio_raw else None
                cash_amount = float(cash_raw) if cash_raw else None
                record = {
                    "trade_date": event_date,
                    "symbol": symbol,
                    "exchange": "SMART",
                    "event_date": event_date,
                    "event_type": event_type,
                    "ratio": ratio,
                    "cash_amount": cash_amount,
                    "notes": notes or None,
                    "source": "manual",
                    "asof_ts": datetime.utcnow(),
                    "ingest_id": ingest_id,
                    "ingest_run_type": "eod",
                    "data_quality_flag": [],
                }

                df = pd.DataFrame([record])
                part = partition_for(
                    self.cfg,
                    self.cfg.paths.clean / "view=corporate_actions",
                    event_date,
                    symbol,
                    "SMART",
                )
                path = self._writer.write_dataframe(df, part)
                rows_written += len(df)
                paths.append(str(path))

        return CorporateActionsResult(
            ingest_id=ingest_id,
            rows_written=rows_written,
            paths=paths,
            errors=errors,
        )
