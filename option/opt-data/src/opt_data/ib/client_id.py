from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Tuple

from opt_data.config import IBClientIdPoolConfig


DEFAULT_POOL_RANGES: dict[str, tuple[int, int]] = {
    "prod": (0, 99),
    "remote": (100, 199),
    "test": (200, 250),
}


@dataclass
class ClientIdAllocator:
    role: str
    pool_range: tuple[int, int]
    randomize: bool
    state_dir: Path
    lock_ttl_seconds: int

    @classmethod
    def from_config(cls, cfg: IBClientIdPoolConfig) -> "ClientIdAllocator":
        role = (cfg.role or "prod").lower()
        pool_range = cfg.range
        if role in DEFAULT_POOL_RANGES and pool_range == (0, 0):
            pool_range = DEFAULT_POOL_RANGES[role]
        return cls(
            role=role,
            pool_range=pool_range,
            randomize=cfg.randomize,
            state_dir=cfg.state_dir,
            lock_ttl_seconds=cfg.lock_ttl_seconds,
        )

    def _candidates(self, limit: int | None = None) -> list[int]:
        low, high = self.pool_range
        ids = list(range(low, high + 1))
        if self.randomize:
            random.shuffle(ids)
        return ids if limit is None else ids[:limit]

    def _lock_path(self, client_id: int) -> Path:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir / f"{self.role}-{client_id}.lock"

    def _is_expired(self, path: Path) -> bool:
        if not path.exists():
            return False
        mtime = path.stat().st_mtime
        return (time.time() - mtime) > self.lock_ttl_seconds

    def _try_claim(self, client_id: int) -> Path | None:
        lock_path = self._lock_path(client_id)
        if lock_path.exists() and self._is_expired(lock_path):
            try:
                lock_path.unlink()
            except OSError:
                pass

        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(lock_path, flags)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(f"{os.getpid()},{int(time.time())}\n")
            return lock_path
        except FileExistsError:
            return None

    def iter_claims(self, limit: int = 5) -> Iterator[Tuple[int, Path]]:
        for client_id in self._candidates(limit=limit):
            lock_path = self._try_claim(client_id)
            if lock_path is not None:
                yield client_id, lock_path

    def release(self, lock_path: Path | None) -> None:
        if lock_path is None:
            return
        try:
            lock_path.unlink()
        except FileNotFoundError:
            return
        except OSError:
            return
