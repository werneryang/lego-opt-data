from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import AppConfig

logger = logging.getLogger(__name__)


class DataAccess:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        allow_raw: bool = True,
        allow_clean: bool = True,
        timezone: str | None = None,
    ) -> None:
        self.raw_root = Path(cfg.paths.raw)
        self.clean_root = Path(cfg.paths.clean)
        self.run_logs = Path(cfg.paths.run_logs)
        self.metrics_db = Path(cfg.observability.metrics_db_path)
        self.allow_raw = allow_raw
        self.allow_clean = allow_clean
        self.tz_name = timezone or cfg.timezone.name

    def list_run_log_files(self, subdir: str, pattern: str) -> list[Path]:
        root = self.run_logs / subdir
        if not root.exists():
            return []
        return sorted(root.glob(pattern), reverse=True)

    def read_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - input issues
            logger.warning(f"Failed to read JSON {path}: {exc}")
            return None

    def recent_metrics_db(self, limit: int) -> list[dict[str, Any]]:
        if not self.metrics_db.exists():
            return []
        try:
            with sqlite3.connect(self.metrics_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning(f"Failed to query metrics DB: {exc}")
            return []

    def recent_dates(self, days: int) -> list[str]:
        now = datetime.now(ZoneInfo(self.tz_name)).date()
        return [(now - timedelta(days=offset)).isoformat() for offset in range(days)]

    def find_parquet_files(
        self,
        root: Path,
        *,
        view: str,
        symbol: str | None,
        days: int,
    ) -> list[Path]:
        candidates: list[Path] = []
        for day in self.recent_dates(days):
            day_root = root / f"view={view}" / f"date={day}"
            if not day_root.exists():
                continue
            if symbol:
                symbol_root = day_root / f"underlying={symbol.upper()}"
                if symbol_root.exists():
                    candidates.extend(sorted(symbol_root.rglob("*.parquet")))
            else:
                candidates.extend(sorted(day_root.rglob("*.parquet")))
        return candidates

    def read_parquet_sample(
        self,
        files: Iterable[Path],
        *,
        limit: int,
        columns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        remaining = limit
        for file_path in files:
            if remaining <= 0:
                break
            try:
                df = pd.read_parquet(file_path, columns=columns)
            except Exception as exc:  # pragma: no cover - corrupt or missing parquet
                logger.warning(f"Failed to read parquet {file_path}: {exc}")
                continue
            if df.empty:
                continue
            sample = df.head(remaining)
            rows.extend(sample.to_dict(orient="records"))
            remaining = limit - len(rows)
        return rows
