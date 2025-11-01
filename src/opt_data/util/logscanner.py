from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple

from ..config import AppConfig
from .calendar import to_et_date


def scan_logs(
    cfg: AppConfig,
    target_day: date,
    keywords: List[str],
) -> Tuple[Dict[str, int], List[str]]:
    keywords = [k.strip() for k in keywords if k.strip()]
    counters: Counter[str] = Counter()
    matched_files: list[str] = []

    run_logs = cfg.paths.run_logs
    errors_dir = run_logs / "errors"
    ymd_compact = target_day.strftime("%Y%m%d")

    def scan_file(path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # pragma: no cover - file/permission issues
            return
        low = text.lower()
        for key in keywords:
            count = low.count(key.lower())
            if count:
                counters[key] += count

    consolidated = errors_dir / f"errors_{ymd_compact}.log"
    if consolidated.exists():
        matched_files.append(str(consolidated))
        scan_file(consolidated)
    else:
        for path in run_logs.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".log", ".jsonl", ".txt"}:
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
            except Exception:
                mtime = None
            if mtime and to_et_date(mtime) != target_day:
                continue
            matched_files.append(str(path))
            scan_file(path)

    return dict(counters), matched_files
