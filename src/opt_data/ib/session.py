from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional
import logging

from opt_data.util.retry import retry_with_backoff

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
    client_id: int
    market_data_type: int = 2

    ib: Optional[object] = None

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
            logger.info(f"Connecting to IB Gateway at {self.host}:{self.port}")
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.ib.reqMarketDataType(self.market_data_type)
            logger.info(f"Successfully connected to IB Gateway")

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

    def __enter__(self) -> "IBSession":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()
