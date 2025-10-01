from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IBSession:
    host: str
    port: int
    client_id: int
    market_data_type: int = 2

    ib: Optional[object] = None

    def connect(self) -> None:
        # Lazy import to avoid dependency during tests without network
        from ib_insync import IB  # type: ignore

        if self.ib is None:
            self.ib = IB()
        if not getattr(self.ib, "isConnected", lambda: False)():
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.ib.reqMarketDataType(self.market_data_type)

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
