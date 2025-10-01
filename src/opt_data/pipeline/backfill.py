from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Sequence

from ..config import AppConfig
from ..universe import load_universe
from ..util.queue import PersistentQueue


@dataclass
class BackfillTask:
    symbol: str
    start_date: str


class BackfillPlanner:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    def queue_path(self, start_date: date) -> Path:
        name = f"backfill_{start_date.isoformat()}.jsonl"
        return self.cfg.paths.state / name

    def plan(self, start_date: date, symbols: Sequence[str] | None = None) -> PersistentQueue[dict]:
        universe = load_universe(self.cfg.universe.file)
        if symbols:
            wanted = {s.upper() for s in symbols}
            entries = [u for u in universe if u.symbol in wanted]
        else:
            entries = universe

        tasks: List[dict] = [
            {"symbol": entry.symbol, "start_date": start_date.isoformat()}
            for entry in entries
        ]

        state_file = self.queue_path(start_date)
        queue = PersistentQueue.create(state_file, tasks)
        queue.save()
        return queue

    def load_queue(self, start_date: date) -> PersistentQueue[dict]:
        return PersistentQueue.load(self.queue_path(start_date))
