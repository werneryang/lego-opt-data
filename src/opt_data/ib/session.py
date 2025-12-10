from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional
import logging
from pathlib import Path

from opt_data.util.retry import retry_with_backoff
from opt_data.config import IBClientIdPoolConfig
from .client_id import ClientIdAllocator

logger = logging.getLogger(__name__)

_IB_CLASS = None


def _ensure_thread_event_loop() -> None:
    """Ensure the current thread has an asyncio event loop for ib_insync/eventkit."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


def _get_ib_class():
    global _IB_CLASS
    if _IB_CLASS is None:
        _ensure_thread_event_loop()
        from ib_insync import IB  # type: ignore

        _IB_CLASS = IB
    return _IB_CLASS


@dataclass
class IBSession:
    host: str
    port: int
    client_id: int | None
    market_data_type: int = 2
    client_id_pool: IBClientIdPoolConfig | None = None

    ib: Optional[object] = None
    _lock_path: Path | None = None
    _allocator: ClientIdAllocator | None = None

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=2.0,
        retriable_exceptions=(ConnectionError, TimeoutError, OSError),
    )
    def connect(self) -> None:
        """Connect to IB Gateway/TWS with automatic retry on connection failures."""
        _ensure_thread_event_loop()
        IB = _get_ib_class()
        
        if self.ib is None:
            self.ib = IB()
        if not getattr(self.ib, "isConnected", lambda: False)():
            client_id = self._connect_with_client_id()
            self.ib.reqMarketDataType(self.market_data_type)
            logger.info(
                f"Successfully connected to IB Gateway host={self.host} port={self.port} clientId={client_id}"
            )

    def ensure_connected(self) -> object:
        self.connect()
        assert self.ib is not None
        return self.ib

    def disconnect(self) -> None:
        if self.ib is not None:
            try:
                self.ib.disconnect()
            finally:
                self.ib = None
        if self._allocator and self._lock_path:
            self._allocator.release(self._lock_path)
            self._lock_path = None
            self._allocator = None

    def __enter__(self) -> "IBSession":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    def _connect_with_client_id(self) -> int:
        if self.client_id is not None:
            logger.info(f"Connecting to IB Gateway at {self.host}:{self.port} clientId={self.client_id}")
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            return self.client_id

        if self.client_id_pool is None:
            raise ValueError("client_id_pool must be provided when client_id is None")

        allocator = ClientIdAllocator.from_config(self.client_id_pool)
        self._allocator = allocator
        last_error: Exception | None = None

        for candidate_id, lock_path in allocator.iter_claims():
            try:
                logger.info(
                    f"Connecting to IB Gateway at {self.host}:{self.port} clientId={candidate_id} role={allocator.role}"
                )
                self.ib.connect(self.host, self.port, clientId=candidate_id)
                self.client_id = candidate_id
                self._lock_path = lock_path
                return candidate_id
            except Exception as exc:
                allocator.release(lock_path)
                self._lock_path = None
                last_error = exc
                logger.warning(
                    f"clientId {candidate_id} failed to connect; trying next candidate",
                    exc_info=exc,
                )

        raise last_error or RuntimeError("Failed to acquire clientId for IB connection")
