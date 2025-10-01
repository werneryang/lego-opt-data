from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


TimeFn = Callable[[], float]


@dataclass
class TokenBucket:
    capacity: int
    refill_per_minute: int
    tokens: float
    last_ts: float
    time_fn: TimeFn

    @classmethod
    def create(
        cls, capacity: int, refill_per_minute: int, time_fn: TimeFn | None = None
    ) -> "TokenBucket":
        tf = time_fn or time.time
        now = tf()
        return cls(
            capacity=capacity,
            refill_per_minute=refill_per_minute,
            tokens=capacity,
            last_ts=now,
            time_fn=tf,
        )

    def _refill(self) -> None:
        now = self.time_fn()
        elapsed = now - self.last_ts
        if elapsed <= 0:
            return
        rate_per_sec = self.refill_per_minute / 60.0
        self.tokens = min(self.capacity, self.tokens + elapsed * rate_per_sec)
        self.last_ts = now

    def try_acquire(self, n: int = 1) -> bool:
        self._refill()
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False
