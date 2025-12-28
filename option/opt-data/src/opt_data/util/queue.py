from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Generic, Iterable, Optional, TypeVar
import json

T = TypeVar("T")


@dataclass
class PersistentQueue(Generic[T]):
    """Minimal persistent queue backed by a JSONL file.

    Not intended for high throughput; suitable for simple resumable batches.
    """

    path: Path
    _q: Deque[T]

    @classmethod
    def create(cls, path: Path, initial: Optional[Iterable[T]] = None) -> "PersistentQueue[T]":
        q = deque(initial or [])
        return cls(path=path, _q=q)

    def push(self, item: T) -> None:
        self._q.append(item)

    def extend(self, items: Iterable[T]) -> None:
        self._q.extend(items)

    def pop(self) -> T:
        return self._q.popleft()

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._q)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            for item in self._q:
                fh.write(json.dumps(item) + "\n")

    @classmethod
    def load(cls, path: Path) -> "PersistentQueue":
        items: list = []
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    items.append(json.loads(line))
        return cls.create(path, items)
