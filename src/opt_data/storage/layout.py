from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from ..config import AppConfig


@dataclass
class Partition:
    root: Path
    trade_date: date
    underlying: str
    exchange: str

    def path(self) -> Path:
        d = self.trade_date.strftime("%Y-%m-%d")
        return (self.root / f"date={d}" / f"underlying={self.underlying}" / f"exchange={self.exchange}").resolve()


def partition_for(cfg: AppConfig, root: Path, trade_date: date, underlying: str, exchange: str) -> Partition:
    return Partition(root=root, trade_date=trade_date, underlying=underlying.upper(), exchange=exchange.upper())


def codec_for_date(cfg: AppConfig, trade_date: date, today: date | None = None) -> tuple[str, dict]:
    """Return (codec, options) based on hot/cold policy."""
    t = today or datetime.utcnow().date()
    if trade_date >= t - timedelta(days=cfg.storage.hot_days):
        return cfg.storage.hot_codec, {}
    # cold
    if cfg.storage.cold_codec.lower() == "zstd":
        return "zstd", {"compression_level": cfg.storage.cold_codec_level}
    return cfg.storage.cold_codec, {}

