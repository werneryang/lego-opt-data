from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..config import AppConfig
from ..storage.layout import codec_for_date, partition_for


@dataclass
class StreamingWriter:
    cfg: AppConfig
    root: Path
    counter: int = 0

    def write_records(self, kind: str, records: Iterable[dict]) -> int:
        rows = list(records)
        if not rows:
            return 0
        df = pd.DataFrame(rows)
        if df.empty:
            return 0
        if "trade_date" not in df.columns:
            df["trade_date"] = datetime.utcnow().date().isoformat()
        if "underlying" not in df.columns:
            df["underlying"] = "UNKNOWN"
        if "exchange" not in df.columns:
            df["exchange"] = "UNKNOWN"

        written = 0
        kind_root = (self.root / f"kind={kind}").resolve()
        grouped = df.groupby(["trade_date", "underlying", "exchange"], dropna=False)
        for (trade_date_value, underlying, exchange), group in grouped:
            trade_date_obj = _coerce_date(trade_date_value) or datetime.utcnow().date()
            part = partition_for(self.cfg, kind_root, trade_date_obj, str(underlying), str(exchange))
            part_dir = part.path()
            part_dir.mkdir(parents=True, exist_ok=True)

            codec, options = codec_for_date(self.cfg, trade_date_obj)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            file_path = part_dir / f"part-{ts}-{self.counter:06d}.parquet"

            import pyarrow as pa  # type: ignore
            import pyarrow.parquet as pq  # type: ignore

            table = pa.Table.from_pandas(group, preserve_index=False)
            pq.write_table(table, file_path, compression=codec, **options)
            written += len(group)
            self.counter += 1

        return written


def _coerce_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    text = str(value) if value is not None else ""
    if len(text) >= 10:
        text = text[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
