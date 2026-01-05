from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ib_insync import IB  # type: ignore

from .client_id import ClientIdAllocator
from ..config import IBClientIdPoolConfig

logger = logging.getLogger(__name__)


@dataclass
class IBSession:
    host: str
    port: int
    client_id: int | None
    market_data_type: int = 1
    client_id_pool: IBClientIdPoolConfig | None = None
    timeout: float = 10.0

    def __post_init__(self) -> None:
        self._ib: Optional[IB] = None
        self._allocator: ClientIdAllocator | None = None
        self._client_id_lock: Path | None = None
        self._resolved_client_id: int | None = None

    def _resolve_client_id(self) -> int:
        if self.client_id is not None:
            return self.client_id
        if self._resolved_client_id is not None:
            return self._resolved_client_id
        if self.client_id_pool is None:
            raise ValueError("client_id is required or configure ib.client_id_pool")
        self._allocator = ClientIdAllocator.from_config(self.client_id_pool)
        for client_id, lock_path in self._allocator.iter_claims():
            self._client_id_lock = lock_path
            self._resolved_client_id = client_id
            return client_id
        raise RuntimeError("No available client IDs in pool")

    def _release_client_id(self) -> None:
        if self._allocator is not None:
            self._allocator.release(self._client_id_lock)
        self._allocator = None
        self._client_id_lock = None
        self._resolved_client_id = None

    def connect(self) -> IB:
        if self._ib and self._ib.isConnected():
            return self._ib
        ib = IB()
        client_id = self._resolve_client_id()
        try:
            ib.connect(self.host, self.port, clientId=client_id, timeout=self.timeout)
        except Exception:
            self._release_client_id()
            raise
        if self.market_data_type is not None:
            ib.reqMarketDataType(self.market_data_type)
        self._ib = ib
        logger.info(
            "Connected to IB host=%s port=%s client_id=%s",
            self.host,
            self.port,
            client_id,
        )
        return ib

    def ensure_connected(self) -> IB:
        return self.connect()

    def disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            logger.info("Disconnected from IB")
        self._release_client_id()

    def __enter__(self) -> "IBSession":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()
