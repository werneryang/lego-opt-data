from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from .layout import Partition, codec_for_date
from ..config import AppConfig


@dataclass
class ParquetWriter:
    cfg: AppConfig

    def write_dataframe(self, df: pd.DataFrame, part: Partition) -> Path:
        part_dir = part.path()
        part_dir.mkdir(parents=True, exist_ok=True)

        d = part.trade_date
        codec, options = codec_for_date(self.cfg, d)

        file_path = part_dir / "part-000.parquet"
        # Defer pyarrow import until needed to avoid import cost in tests
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore

        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, file_path, compression=codec, **options)
        return file_path
