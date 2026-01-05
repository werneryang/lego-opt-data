from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, List
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import AppConfig
from ..ib import IBSession, fetch_daily_bars, make_throttle
from ..storage import ParquetWriter, partition_for
from ..universe import load_universe

logger = logging.getLogger(__name__)


@dataclass
class DailyBarsResult:
    ingest_id: str
    trade_date: date
    symbols_processed: int
    rows_written: int
    paths: list[str]
    errors: list[dict[str, Any]]


def _bar_to_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        raw = value.strip()
        if raw.isdigit() and len(raw) == 8:
            try:
                return datetime.strptime(raw, "%Y%m%d").date()
            except ValueError:
                return None
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError:
            return None
    return None


def _pick_bar_for_date(bars: Iterable[Any], target: date) -> Any | None:
    for bar in bars:
        bar_date = _bar_to_date(getattr(bar, "date", None))
        if bar_date == target:
            return bar
    return None


class DailyBarsRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        session_factory: callable[[], IBSession] | None = None,
        writer: ParquetWriter | None = None,
        now_fn: callable[[], datetime] | None = None,
    ) -> None:
        self.cfg = cfg
        self._session_factory = session_factory or (
            lambda: IBSession(
                host=cfg.ib.host,
                port=cfg.ib.port,
                client_id=cfg.ib.client_id,
                market_data_type=cfg.ib.market_data_type,
                client_id_pool=cfg.ib.client_id_pool,
            )
        )
        self._writer = writer or ParquetWriter(cfg)
        self._now_fn = now_fn or (lambda: datetime.now(ZoneInfo(cfg.timezone.name)))
        self._throttle = make_throttle()

    def run(
        self,
        *,
        trade_date: date | None = None,
        symbols: List[str] | None = None,
        exchange: str = "SMART",
        currency: str = "USD",
        what_to_show: str = "TRADES",
        use_rth: bool = True,
    ) -> DailyBarsResult:
        target_date = trade_date or self._now_fn().date()
        ingest_id = str(uuid.uuid4())

        if symbols is None:
            universe = load_universe(self.cfg.universe.file)
            symbols = [entry.symbol for entry in universe]

        errors: list[dict[str, Any]] = []
        paths: list[str] = []
        rows_written = 0

        session = self._session_factory()
        with session as sess:
            ib = sess.ensure_connected()
            from ib_insync import Stock  # type: ignore

            for symbol in symbols:
                contract = Stock(symbol, exchange, currency)
                qualified = ib.qualifyContracts(contract)
                if not qualified:
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": "qualify_failed",
                            "message": "Failed to qualify contract",
                        }
                    )
                    continue

                end_dt = target_date.strftime("%Y%m%d 23:59:59")
                bars = fetch_daily_bars(
                    ib,
                    qualified[0],
                    what_to_show=what_to_show,
                    duration="2 D",
                    bar_size="1 day",
                    end_date_time=end_dt,
                    use_rth=use_rth,
                    format_date=2,
                    throttle=self._throttle,
                )
                bar = _pick_bar_for_date(bars, target_date)
                if bar is None:
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": "missing_bar",
                            "message": f"No bar for {target_date.isoformat()}",
                        }
                    )
                    continue

                record = {
                    "trade_date": target_date,
                    "symbol": symbol,
                    "exchange": exchange,
                    "open": getattr(bar, "open", None),
                    "high": getattr(bar, "high", None),
                    "low": getattr(bar, "low", None),
                    "close": getattr(bar, "close", None),
                    "volume": getattr(bar, "volume", None),
                    "barCount": getattr(bar, "barCount", None),
                    "wap": getattr(bar, "wap", None),
                    "source": "IBKR",
                    "asof_ts": datetime.utcnow(),
                    "ingest_id": ingest_id,
                    "ingest_run_type": "eod",
                    "market_data_type": self.cfg.ib.market_data_type,
                    "data_quality_flag": [],
                }

                df = pd.DataFrame([record])
                part = partition_for(
                    self.cfg,
                    self.cfg.paths.clean / "view=daily_bars",
                    target_date,
                    symbol,
                    exchange,
                )
                path = self._writer.write_dataframe(df, part)
                rows_written += len(df)
                paths.append(str(path))

        return DailyBarsResult(
            ingest_id=ingest_id,
            trade_date=target_date,
            symbols_processed=len(symbols),
            rows_written=rows_written,
            paths=paths,
            errors=errors,
        )
