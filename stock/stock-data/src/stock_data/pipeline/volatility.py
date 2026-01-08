from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Iterable, List
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import AppConfig
from ..ib import IBSession, fetch_daily_bars, fetch_iv_snapshot, make_throttle
from ..storage import ParquetWriter, existing_partition_dates, partition_for
from ..universe import load_universe

logger = logging.getLogger(__name__)


@dataclass
class VolatilityResult:
    ingest_id: str
    trade_date: date | None
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


def _bars_to_map(bars: Iterable[Any]) -> dict[date, Any]:
    out: dict[date, Any] = {}
    for bar in bars:
        bar_date = _bar_to_date(getattr(bar, "date", None))
        if bar_date is None:
            continue
        out[bar_date] = bar
    return out


def _normalize_tz_name(name: str) -> str:
    if name == "America/New_York":
        return "US/Eastern"
    return name


def _end_dt_for_date(target: date, tz_name: str) -> str:
    tz = _normalize_tz_name(tz_name)
    return f"{target.strftime('%Y%m%d')} 23:59:59 {tz}"


def _chunk_symbols(symbols: List[str], batch_size: int | None) -> Iterable[List[str]]:
    if not batch_size or batch_size <= 0:
        yield symbols
        return
    for idx in range(0, len(symbols), batch_size):
        yield symbols[idx : idx + batch_size]


class VolatilityRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        session_factory: callable[[], IBSession] | None = None,
        writer: ParquetWriter | None = None,
        now_fn: callable[[], datetime] | None = None,
        throttle_sec: float = 0.7,
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
        self._throttle = make_throttle(throttle_sec)

    def run_snapshot(
        self,
        *,
        trade_date: date | None = None,
        symbols: List[str] | None = None,
        exchange: str = "SMART",
        currency: str = "USD",
        generic_ticks: str = "106",
        timeout: float = 12.0,
        poll_interval: float = 0.25,
        batch_size: int | None = None,
    ) -> VolatilityResult:
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

            total = len(symbols)
            processed = 0
            for batch in _chunk_symbols(symbols, batch_size):
                for symbol in batch:
                    processed += 1
                    if processed == 1 or processed % 25 == 0 or processed == total:
                        logger.info(
                            "volatility snapshot progress %s/%s symbol=%s",
                            processed,
                            total,
                            symbol,
                        )
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

                    iv_value = fetch_iv_snapshot(
                        ib,
                        qualified[0],
                        generic_ticks=generic_ticks,
                        timeout=timeout,
                        poll_interval=poll_interval,
                    )
                    if iv_value is None:
                        errors.append(
                            {
                                "symbol": symbol,
                                "error": "missing_iv",
                                "message": "No IV snapshot returned",
                            }
                        )

                    end_dt = _end_dt_for_date(target_date, self.cfg.timezone.name)
                    hv_bars = fetch_daily_bars(
                        ib,
                        qualified[0],
                        what_to_show="HISTORICAL_VOLATILITY",
                        duration="2 D",
                        bar_size="1 day",
                        end_date_time=end_dt,
                        use_rth=True,
                        format_date=2,
                        throttle=self._throttle,
                    )
                    hv_map = _bars_to_map(hv_bars)
                    hv_bar = hv_map.get(target_date)
                    hv_value = getattr(hv_bar, "close", None) if hv_bar else None
                    if hv_value is None:
                        errors.append(
                            {
                                "symbol": symbol,
                                "error": "missing_hv",
                                "message": f"No HV bar for {target_date.isoformat()}",
                            }
                        )

                    record = {
                        "trade_date": target_date,
                        "symbol": symbol,
                        "exchange": exchange,
                        "iv_30d": iv_value,
                        "hv_30d": hv_value,
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
                        self.cfg.paths.clean / "view=volatility",
                        target_date,
                        symbol,
                        exchange,
                    )
                    path = self._writer.write_dataframe(df, part)
                    rows_written += len(df)
                    paths.append(str(path))

        return VolatilityResult(
            ingest_id=ingest_id,
            trade_date=target_date,
            symbols_processed=len(symbols),
            rows_written=rows_written,
            paths=paths,
            errors=errors,
        )

    def run_backfill(
        self,
        *,
        end_date: date | None = None,
        days: int = 365,
        symbols: List[str] | None = None,
        exchange: str = "SMART",
        currency: str = "USD",
        batch_size: int | None = None,
    ) -> VolatilityResult:
        target_end = end_date or self._now_fn().date()
        window_start = target_end - timedelta(days=max(days - 1, 0))
        ingest_id = str(uuid.uuid4())

        if symbols is None:
            universe = load_universe(self.cfg.universe.file)
            symbols = [entry.symbol for entry in universe]

        errors: list[dict[str, Any]] = []
        paths: list[str] = []
        rows_written = 0

        view_root = self.cfg.paths.clean / "view=volatility"
        session = self._session_factory()
        with session as sess:
            ib = sess.ensure_connected()
            from ib_insync import Stock  # type: ignore

            total = len(symbols)
            processed = 0
            for batch in _chunk_symbols(symbols, batch_size):
                for symbol in batch:
                    processed += 1
                    if processed == 1 or processed % 25 == 0 or processed == total:
                        logger.info(
                            "volatility backfill progress %s/%s symbol=%s",
                            processed,
                            total,
                            symbol,
                        )
                    existing_dates = existing_partition_dates(view_root, symbol, exchange)
                    start_date = window_start
                    if existing_dates:
                        latest = max(existing_dates)
                        if latest >= window_start:
                            start_date = latest + timedelta(days=1)
                    if start_date > target_end:
                        continue

                    duration_days = (target_end - start_date).days + 1
                    duration_str = f"{duration_days} D"
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

                    end_dt = _end_dt_for_date(target_end, self.cfg.timezone.name)
                    iv_bars = fetch_daily_bars(
                        ib,
                        qualified[0],
                        what_to_show="OPTION_IMPLIED_VOLATILITY",
                        duration=duration_str,
                        bar_size="1 day",
                        end_date_time=end_dt,
                        use_rth=True,
                        format_date=2,
                        throttle=self._throttle,
                    )
                    hv_bars = fetch_daily_bars(
                        ib,
                        qualified[0],
                        what_to_show="HISTORICAL_VOLATILITY",
                        duration=duration_str,
                        bar_size="1 day",
                        end_date_time=end_dt,
                        use_rth=True,
                        format_date=2,
                        throttle=self._throttle,
                    )
                    iv_map = _bars_to_map(iv_bars)
                    hv_map = _bars_to_map(hv_bars)
                    if not iv_map and not hv_map:
                        errors.append(
                            {
                                "symbol": symbol,
                                "error": "missing_bars",
                                "message": "No IV/HV bars returned",
                            }
                        )
                        continue

                    dates = sorted({*iv_map.keys(), *hv_map.keys()})
                    for bar_date in dates:
                        if bar_date < start_date or bar_date > target_end:
                            continue
                        iv_bar = iv_map.get(bar_date)
                        hv_bar = hv_map.get(bar_date)
                        record = {
                            "trade_date": bar_date,
                            "symbol": symbol,
                            "exchange": exchange,
                            "iv_30d": getattr(iv_bar, "close", None) if iv_bar else None,
                            "hv_30d": getattr(hv_bar, "close", None) if hv_bar else None,
                            "source": "IBKR",
                            "asof_ts": datetime.utcnow(),
                            "ingest_id": ingest_id,
                            "ingest_run_type": "backfill",
                            "market_data_type": self.cfg.ib.market_data_type,
                            "data_quality_flag": [],
                        }
                        df = pd.DataFrame([record])
                        part = partition_for(
                            self.cfg,
                            self.cfg.paths.clean / "view=volatility",
                            bar_date,
                            symbol,
                            exchange,
                        )
                        path = self._writer.write_dataframe(df, part)
                        rows_written += len(df)
                        paths.append(str(path))

        return VolatilityResult(
            ingest_id=ingest_id,
            trade_date=None,
            symbols_processed=len(symbols),
            rows_written=rows_written,
            paths=paths,
            errors=errors,
        )
