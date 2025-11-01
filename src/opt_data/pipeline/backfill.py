from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, List, Sequence, Optional, Dict, Any

import asyncio
import logging
import math
import time
import pandas as pd

from ..config import AppConfig
from ..universe import load_universe
from ..util.queue import PersistentQueue
from ..ib.session import IBSession
from ..ib.discovery import discover_contracts_for_symbol
from ..storage.writer import ParquetWriter
from ..storage.layout import partition_for
from ..util.calendar import is_trading_day
from ..util.ratelimit import TokenBucket
from .cleaning import CleaningPipeline

logger = logging.getLogger(__name__)


@dataclass
class BackfillTask:
    symbol: str
    start_date: str


class BackfillPlanner:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    def queue_path(self, start_date: date) -> Path:
        name = f"backfill_{start_date.isoformat()}.jsonl"
        return self.cfg.paths.state / name

    def plan(self, start_date: date, symbols: Sequence[str] | None = None) -> PersistentQueue[dict]:
        universe = load_universe(self.cfg.universe.file)
        if symbols:
            wanted = {s.upper() for s in symbols}
            entries = [u for u in universe if u.symbol in wanted]
        else:
            entries = universe

        tasks: List[dict] = [
            {
                "symbol": entry.symbol,
                "start_date": start_date.isoformat(),
                "underlying_conid": entry.conid,
            }
            for entry in entries
        ]

        state_file = self.queue_path(start_date)
        queue = PersistentQueue.create(state_file, tasks)
        queue.save()
        return queue

    def load_queue(self, start_date: date) -> PersistentQueue[dict]:
        return PersistentQueue.load(self.queue_path(start_date))


def _default_session_factory(cfg: AppConfig) -> IBSession:
    return IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        market_data_type=cfg.ib.market_data_type,
    )


def fetch_underlying_close(
    ib: Any, symbol: str, trade_date: date, conid: Optional[int] = None
) -> float:
    from ib_insync import Stock  # type: ignore

    # Qualify the underlying contract
    if conid:
        contract = Stock(symbol, "SMART", "USD", conId=conid)
    else:
        contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)

    end_dt = f"{trade_date.strftime('%Y%m%d')} 23:59:59"
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end_dt,
        durationStr="1 D",
        barSizeSetting="1 day",
        whatToShow="TRADES",
        useRTH=False,
        formatDate=1,
    )
    if not bars:
        raise RuntimeError(f"No historical data returned for {symbol} on {trade_date}")
    return float(bars[-1].close)


def _has_market_data(ticker: Any) -> bool:
    fields = [ticker.last, ticker.close, ticker.bid, ticker.ask]
    for val in fields:
        if val is None:
            continue
        try:
            if not math.isnan(val):
                return True
        except TypeError:
            return True
    greeks = getattr(ticker, "modelGreeks", None)
    return greeks is not None


def fetch_option_snapshots(
    ib: Any,
    contracts: List[Dict[str, Any]],
    generic_ticks: str,
    *,
    timeout: float = 10.0,
    poll_interval: float = 0.5,
    acquire_token: Optional[Callable[[], None]] = None,
) -> List[Dict[str, Any]]:
    from ib_insync import Option  # type: ignore

    rows: List[Dict[str, Any]] = []
    for info in contracts:
        expiry_yyyymmdd = info["expiry"].replace("-", "")
        option = Option(
            symbol=info["symbol"],
            lastTradeDateOrContractMonth=expiry_yyyymmdd,
            strike=info["strike"],
            right=info["right"],
            exchange=info["exchange"],
            currency=info.get("currency", "USD"),
            tradingClass=info.get("tradingClass"),
        )

        if acquire_token:
            acquire_token()
        ticker = ib.reqMktData(option, genericTickList=generic_ticks, snapshot=True)
        elapsed = 0.0
        while elapsed < timeout and not _has_market_data(ticker):
            ib.sleep(poll_interval)
            elapsed += poll_interval

        greeks = getattr(ticker, "modelGreeks", None)
        timestamp = getattr(ticker, "time", None)

        rows.append(
            {
                **info,
                "bid": float(ticker.bid) if ticker.bid is not None else math.nan,
                "ask": float(ticker.ask) if ticker.ask is not None else math.nan,
                "last": float(ticker.last) if ticker.last is not None else math.nan,
                "close": float(ticker.close) if ticker.close is not None else math.nan,
                "volume": getattr(ticker, "volume", None),
                "open_interest": getattr(ticker, "openInterest", None),
                "iv": getattr(greeks, "impliedVol", math.nan) if greeks else math.nan,
                "delta": getattr(greeks, "delta", math.nan) if greeks else math.nan,
                "gamma": getattr(greeks, "gamma", math.nan) if greeks else math.nan,
                "theta": getattr(greeks, "theta", math.nan) if greeks else math.nan,
                "vega": getattr(greeks, "vega", math.nan) if greeks else math.nan,
                "market_data_type": getattr(ticker, "marketDataType", None),
                "asof": timestamp.isoformat() if timestamp else None,
            }
        )

        try:
            ib.cancelMktData(option)
        except Exception:  # pragma: no cover - cleanup best effort
            pass

    return rows


class BackfillRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        session_factory: Optional[Callable[[], IBSession]] = None,
        contract_fetcher: Optional[Callable[..., List[Dict[str, Any]]]] = None,
        snapshot_fetcher: Optional[Callable[..., List[Dict[str, Any]]]] = None,
        underlying_fetcher: Optional[Callable[..., float]] = None,
        writer: Optional[ParquetWriter] = None,
        cleaner: Optional[CleaningPipeline] = None,
    ) -> None:
        self.cfg = cfg
        self.mode = cfg.acquisition.mode.lower()
        self.session_factory = session_factory or (lambda: _default_session_factory(cfg))
        self.contract_fetcher = contract_fetcher or (
            lambda session,
            symbol,
            trade_date,
            price,
            config,
            **kwargs: discover_contracts_for_symbol(
                session,
                symbol,
                trade_date,
                price,
                config,
                **kwargs,
                max_strikes_per_expiry=config.acquisition.max_strikes_per_expiry,
            )
        )
        self.snapshot_fetcher = snapshot_fetcher or (
            lambda ib, contracts, ticks, acquire_token=None: fetch_option_snapshots(
                ib, contracts, ticks, acquire_token=acquire_token
            )
        )
        self.underlying_fetcher = underlying_fetcher or (
            lambda ib, symbol, dt, conid=None: fetch_underlying_close(ib, symbol, dt, conid)
        )
        self.writer = writer or ParquetWriter(cfg)
        self.cleaner = cleaner or CleaningPipeline.create(cfg)

        self._limiters: Dict[str, TokenBucket] = {
            "discovery": TokenBucket.create(
                capacity=self.cfg.rate_limits.discovery.burst,
                refill_per_minute=self.cfg.rate_limits.discovery.per_minute,
            ),
            "snapshot": TokenBucket.create(
                capacity=self.cfg.rate_limits.snapshot.burst,
                refill_per_minute=self.cfg.rate_limits.snapshot.per_minute,
            ),
            "historical": TokenBucket.create(
                capacity=self.cfg.rate_limits.historical.burst,
                refill_per_minute=self.cfg.rate_limits.historical.per_minute,
            ),
        }

    def run(
        self,
        start_date: date,
        symbols: Optional[Sequence[str]] = None,
        *,
        limit: Optional[int] = None,
        force_refresh: bool = False,
        progress: Optional[Callable[[date, str, str, Dict[str, Any]], None]] = None,
        stop_requested: Optional[Callable[[], bool]] = None,
    ) -> int:
        planner = BackfillPlanner(self.cfg)
        queue_path = planner.queue_path(start_date)
        if queue_path.exists():
            queue = planner.load_queue(start_date)
        else:
            queue = planner.plan(start_date, symbols)

        if len(queue) == 0:
            return 0

        processed = 0
        session = self.session_factory()
        with session:
            ib = session.ensure_connected()
            max_items = len(queue) if limit is None else min(limit, len(queue))
            for _ in range(max_items):
                if len(queue) == 0:
                    break
                task = queue.pop()
                symbol = task["symbol"]
                underlying_conid = task.get("underlying_conid")
                try:
                    if stop_requested and stop_requested():
                        if progress:
                            progress(
                                start_date,
                                symbol,
                                "timeout",
                                {"stage": "before_start"},
                            )
                        queue.push(task)
                        queue.save()
                        break
                    if progress:
                        progress(
                            start_date,
                            symbol,
                            "start",
                            {"remaining": len(queue)},
                        )
                    if self.mode == "historical":
                        self._acquire("historical")
                    underlying_close = self.underlying_fetcher(
                        ib, symbol, start_date, underlying_conid
                    )
                    if progress:
                        progress(
                            start_date,
                            symbol,
                            "underlying",
                            {"price": underlying_close},
                        )
                    if progress:
                        progress(
                            start_date,
                            symbol,
                            "contracts_fetch",
                            {},
                        )
                    contracts = self.contract_fetcher(
                        session,
                        symbol,
                        start_date,
                        underlying_close,
                        self.cfg,
                        underlying_conid=underlying_conid,
                        force_refresh=force_refresh,
                        acquire_token=self._make_acquire("discovery"),
                    )
                    if not contracts:
                        logger.warning(
                            "No contracts discovered", extra={"symbol": symbol, "date": start_date}
                        )
                        if progress:
                            progress(
                                start_date,
                                symbol,
                                "no_contracts",
                                {"underlying_close": underlying_close},
                            )
                        queue.save()
                        continue
                    if progress:
                        progress(
                            start_date,
                            symbol,
                            "contracts_ready",
                            {"count": len(contracts)},
                        )

                    if self.mode == "historical":
                        market_rows = self._fetch_historical_rows(
                            ib,
                            contracts,
                            start_date,
                            acquire_token=self._make_acquire("historical"),
                            progress=progress,
                            stop_requested=stop_requested,
                        )
                    else:
                        market_rows = self.snapshot_fetcher(
                            ib,
                            contracts,
                            self.cfg.cli.default_generic_ticks,
                            acquire_token=self._make_acquire("snapshot"),
                        )
                        if progress:
                            progress(
                                start_date,
                                symbol,
                                "snapshot_rows",
                                {"rows": len(market_rows)},
                            )
                    if not market_rows:
                        logger.warning(
                            "No market data snapshots", extra={"symbol": symbol, "date": start_date}
                        )
                        queue.save()
                        continue

                    df = pd.DataFrame(market_rows)
                    df["trade_date"] = start_date
                    df["underlying_close"] = underlying_close
                    df["symbol"] = symbol
                    if "asof" in df.columns:
                        df["asof_ts"] = pd.to_datetime(df["asof"], errors="coerce")
                        df.drop(columns=["asof"], inplace=True)
                        fallback_ts = pd.Timestamp.utcnow().tz_localize(None)
                        df.loc[df["asof_ts"].isna(), "asof_ts"] = fallback_ts
                    else:
                        df["asof_ts"] = pd.Timestamp.utcnow().tz_localize(None)

                    for exchange, group in df.groupby("exchange", dropna=False):
                        partition = partition_for(
                            self.cfg,
                            self.cfg.paths.raw,
                            start_date,
                            symbol,
                            (exchange or "SMART"),
                        )
                        self.writer.write_dataframe(group.reset_index(drop=True), partition)

                    clean_df, adjusted_df = self.cleaner.process(df)

                    for exchange, group in clean_df.groupby("exchange", dropna=False):
                        partition = partition_for(
                            self.cfg,
                            self.cfg.paths.clean / "view=clean",
                            start_date,
                            symbol,
                            (exchange or "SMART"),
                        )
                        self.writer.write_dataframe(group.reset_index(drop=True), partition)

                    for exchange, group in adjusted_df.groupby("exchange", dropna=False):
                        partition = partition_for(
                            self.cfg,
                            self.cfg.paths.clean / "view=adjusted",
                            start_date,
                            symbol,
                            (exchange or "SMART"),
                        )
                        self.writer.write_dataframe(group.reset_index(drop=True), partition)

                    processed += 1
                    queue.save()
                    if progress:
                        progress(
                            start_date,
                            symbol,
                            "success",
                            {"rows": len(df)},
                        )
                except Exception as exc:
                    logger.exception(
                        "Backfill task failed",
                        extra={"symbol": symbol, "date": start_date},
                        exc_info=exc,
                    )
                    queue.push(task)
                    queue.save()
                    if progress:
                        progress(
                            start_date,
                            symbol,
                            "error",
                            {"error": str(exc)},
                        )
                    break
        return processed

    def run_range(
        self,
        start_date: date,
        end_date: date,
        symbols: Optional[Sequence[str]] = None,
        *,
        force_refresh: bool = False,
        limit_per_day: Optional[int] = None,
        progress: Optional[Callable[[date, str, str, Dict[str, Any]], None]] = None,
        stop_requested: Optional[Callable[[], bool]] = None,
    ) -> int:
        if end_date < start_date:
            raise ValueError("end date must be on or after start date")

        total_processed = 0
        current = start_date
        while current <= end_date:
            if stop_requested and stop_requested():
                if progress:
                    progress(current, "", "timeout", {"stage": "range"})
                break
            if is_trading_day(current):
                if progress:
                    progress(current, "", "day_start", {})
                processed_today = self.run(
                    current,
                    symbols,
                    limit=limit_per_day,
                    force_refresh=force_refresh,
                    progress=progress,
                    stop_requested=stop_requested,
                )
                total_processed += processed_today
                if progress:
                    progress(current, "", "day_end", {"processed": processed_today})
            else:
                if progress:
                    progress(current, "", "non_trading", {})
            current += timedelta(days=1)
        return total_processed

    def _acquire(self, name: str, tokens: int = 1) -> None:
        limiter = self._limiters[name]
        while not limiter.try_acquire(tokens):
            time.sleep(1.0)

    def _make_acquire(self, name: str) -> Callable[[], None]:
        return lambda: self._acquire(name)

    def _fetch_historical_rows(
        self,
        ib: Any,
        contracts: List[Dict[str, Any]],
        trade_date: date,
        *,
        acquire_token: Optional[Callable[[], None]] = None,
        progress: Optional[Callable[[date, str, str, Dict[str, Any]], None]] = None,
        stop_requested: Optional[Callable[[], bool]] = None,
    ) -> List[Dict[str, Any]]:
        from ib_insync import Option  # type: ignore

        rows: List[Dict[str, Any]] = []
        asof = pd.Timestamp.utcnow().tz_localize(None)
        duration = self.cfg.acquisition.duration
        bar_size = self.cfg.acquisition.bar_size
        raw_wts = self.cfg.acquisition.what_to_show or "TRADES"
        what_to_shows = [w.strip() for w in raw_wts.split(",") if w.strip()] or ["TRADES"]
        if "TRADES" not in what_to_shows:
            # ensure TRADES attempted before fallback to keep behaviour predictable
            what_to_shows = ["TRADES"] + [w for w in what_to_shows if w != "TRADES"]
        if "MIDPOINT" not in what_to_shows:
            what_to_shows.append("MIDPOINT")
        use_rth = self.cfg.acquisition.use_rth
        end_dt = f"{trade_date.strftime('%Y%m%d')} 23:59:59"

        for info in contracts:
            try:
                if stop_requested and stop_requested():
                    if progress:
                        progress(
                            trade_date,
                            info.get("symbol", ""),
                            "timeout",
                            {"stage": "historical_loop"},
                        )
                    break
                option = Option(
                    info.get("symbol"),
                    info.get("expiry", "").replace("-", ""),
                    float(info.get("strike", 0.0)),
                    info.get("right", "C"),
                    info.get("exchange") or "",
                    info.get("currency", "USD"),
                    info.get("tradingClass"),
                )
                if info.get("conid"):
                    option.conId = int(info["conid"])
                option.includeExpired = True

                if acquire_token:
                    acquire_token()
                qualified = ib.qualifyContracts(option)
                if not qualified:
                    logger.debug(
                        "Failed to qualify contract",
                        extra={"symbol": info.get("symbol"), "expiry": info.get("expiry")},
                    )
                    continue
                contract = qualified[0]

                bars = None
                last_error: Optional[str] = None
                for what_to_show in what_to_shows:
                    try:
                        if acquire_token:
                            acquire_token()
                        if progress:
                            progress(
                                trade_date,
                                info.get("symbol", ""),
                                "historical_try",
                                {
                                    "expiry": info.get("expiry"),
                                    "strike": info.get("strike"),
                                    "right": info.get("right"),
                                    "what": what_to_show,
                                },
                            )
                        timeout_s = max(self.cfg.acquisition.historical_timeout, 1.0)
                        try:
                            bars = ib.run(
                                asyncio.wait_for(
                                    ib.reqHistoricalDataAsync(
                                        contract,
                                        endDateTime=end_dt,
                                        durationStr=duration,
                                        barSizeSetting=bar_size,
                                        whatToShow=what_to_show,
                                        useRTH=use_rth,
                                        formatDate=1,
                                    ),
                                    timeout=timeout_s,
                                )
                            )
                        except asyncio.TimeoutError:
                            last_error = f"timeout({timeout_s}s)"
                            if progress:
                                progress(
                                    trade_date,
                                    info.get("symbol", ""),
                                    "historical_error",
                                    {
                                        "expiry": info.get("expiry"),
                                        "strike": info.get("strike"),
                                        "right": info.get("right"),
                                        "what": what_to_show,
                                        "error": last_error,
                                    },
                                )
                            logger.warning(
                                "Historical data request timeout",
                                extra={
                                    "symbol": info.get("symbol"),
                                    "expiry": info.get("expiry"),
                                    "what": what_to_show,
                                    "timeout": timeout_s,
                                },
                            )
                            continue
                        if bars:
                            if progress:
                                progress(
                                    trade_date,
                                    info.get("symbol", ""),
                                    "historical_success",
                                    {
                                        "expiry": info.get("expiry"),
                                        "strike": info.get("strike"),
                                        "right": info.get("right"),
                                        "what": what_to_show,
                                        "rows": len(bars),
                                    },
                                )
                            break
                        else:
                            last_error = "no_bars"
                    except Exception as exc:
                        last_error = str(exc)
                        logger.warning(
                            "Historical data request failed",
                            extra={
                                "symbol": info.get("symbol"),
                                "expiry": info.get("expiry"),
                                "what": what_to_show,
                            },
                            exc_info=exc,
                        )
                        if progress:
                            progress(
                                trade_date,
                                info.get("symbol", ""),
                                "historical_error",
                                {
                                    "expiry": info.get("expiry"),
                                    "strike": info.get("strike"),
                                    "right": info.get("right"),
                                    "what": what_to_show,
                                    "error": str(exc),
                                },
                            )
                        continue

                if not bars:
                    if progress:
                        progress(
                            trade_date,
                            info.get("symbol", ""),
                            "historical_empty",
                            {
                                "expiry": info.get("expiry"),
                                "strike": info.get("strike"),
                                "right": info.get("right"),
                                "last_error": last_error,
                            },
                        )
                    continue

                for bar in bars:
                    try:
                        bar_ts = pd.Timestamp(bar.date)
                    except Exception:
                        bar_ts = pd.Timestamp(trade_date)

                    rows.append(
                        {
                            **info,
                            "open": float(getattr(bar, "open", float("nan"))),
                            "high": float(getattr(bar, "high", float("nan"))),
                            "low": float(getattr(bar, "low", float("nan"))),
                            "close": float(getattr(bar, "close", float("nan"))),
                            "last": float(getattr(bar, "close", float("nan"))),
                            "volume": int(getattr(bar, "volume", 0) or 0),
                            "bid": pd.NA,
                            "ask": pd.NA,
                            "mid": pd.NA,
                            "iv": pd.NA,
                            "delta": pd.NA,
                            "gamma": pd.NA,
                            "theta": pd.NA,
                            "vega": pd.NA,
                            "open_interest": pd.NA,
                            "market_data_type": None,
                            "bar_timestamp": bar_ts,
                            "asof_ts": asof,
                        }
                    )
            except Exception as exc:  # pragma: no cover - network failure
                logger.warning(
                    "Historical data request failed",
                    extra={"symbol": info.get("symbol"), "expiry": info.get("expiry")},
                    exc_info=exc,
                )
                continue

        return rows
