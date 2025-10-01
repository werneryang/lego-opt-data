from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import csv


@dataclass
class UniverseEntry:
    symbol: str
    conid: int | None = None


def load_universe(path: Path) -> List[UniverseEntry]:
    entries: List[UniverseEntry] = []
    if not path.exists():
        return entries

    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(row for row in fh if not row.startswith("#"))
        for row in reader:
            symbol = (row.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            conid_raw = (row.get("conid") or "").strip()
            conid = int(conid_raw) if conid_raw else None
            entries.append(UniverseEntry(symbol=symbol, conid=conid))
    return entries

