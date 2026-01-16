from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Optional
from zoneinfo import ZoneInfo

from ..config import AppConfig
from ..ib.session import IBSession
from ..ib import sec_def_params
from ..pipeline.backfill import fetch_underlying_close
from ..streaming.selection import (
    diff_strikes,
    select_expiries,
    select_strikes_around_spot,
    should_rebalance,
    strike_step,
)
from ..universe import load_universe
from ..util.calendar import to_et_date
from .writer import StreamingWriter

logger = logging.getLogger(__name__)

DEFAULT_FLUSH_INTERVAL = 15.0
DEFAULT_REBALANCE_INTERVAL = 1.0
DEFAULT_MAX_BUFFER_ROWS = 5000
DEFAULT_METRICS_INTERVAL = 300.0


@dataclass
class StreamingResult:
    ingest_id: str
    started_at: datetime
    ended_at: datetime
    option_rows: int
    spot_rows: int
    bar_rows: int
    rebalances: int


class StreamingRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        session_factory: Callable[[], IBSession] | None = None,
        writer: StreamingWriter | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.cfg = cfg
        self._session_factory = session_factory or (
            lambda: IBSession(
                host=cfg.ib.host,
                port=cfg.ib.port,
                client_id=cfg.ib.client_id,
                client_id_pool=cfg.ib.client_id_pool,
                market_data_type=cfg.ib.market_data_type,
            )
        )
        base_root = Path(cfg.paths.raw).parent / "streaming"
        self._writer = writer or StreamingWriter(cfg, base_root)
        self._now_fn = now_fn or datetime.utcnow
        self._et_tz = ZoneInfo("America/New_York")

        self._buffers: dict[str, list[dict]] = {"options": [], "spot": [], "bars": []}
        self._lock = threading.Lock()

        self._spot_prices: dict[str, float] = {}
        self._spot_contracts: dict[str, Any] = {}
        self._option_strikes: dict[str, list[float]] = {}
        self._option_expiries: dict[str, list[date]] = {}
        self._last_rebalance_spot: dict[str, float] = {}
        self._chain_strikes: dict[str, list[float]] = {}
        self._chain_exchange: dict[str, str] = {}
        self._chain_trading_class: dict[str, str] = {}
        self._option_tickers: dict[str, dict[tuple, Any]] = {}
        self._bar_streams: dict[str, Any] = {}

        self._option_rows = 0
        self._spot_rows = 0
        self._bar_rows = 0
        self._rebalances = 0
        self._last_flush_rows = 0
        self._last_flush_at: datetime | None = None

    def run(
        self,
        trade_date: date | None = None,
        *,
        symbols: list[str] | None = None,
        duration_seconds: float | None = None,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
        rebalance_check_interval: float = DEFAULT_REBALANCE_INTERVAL,
        max_buffer_rows: int = DEFAULT_MAX_BUFFER_ROWS,
        metrics_interval: float = DEFAULT_METRICS_INTERVAL,
    ) -> StreamingResult:
        ingest_id = uuid.uuid4().hex
        started_at = datetime.utcnow()
        streaming_cfg = self.cfg.streaming
        trade_date = trade_date or to_et_date(datetime.now(ZoneInfo("UTC")))
        symbols = symbols or streaming_cfg.underlyings
        symbols = [s.strip().upper() for s in symbols if str(s).strip()]
        if not symbols:
            raise ValueError("No underlyings configured for streaming")

        include_greeks = any(field.lower() in {"iv", "greeks"} for field in streaming_cfg.fields)
        generic_ticks = self.cfg.snapshot.generic_ticks if include_greeks else ""

        per_kind_config = {
            "options": (
                streaming_cfg.options_flush_interval_sec,
                streaming_cfg.options_max_buffer_rows,
            ),
            "spot": (
                streaming_cfg.spot_flush_interval_sec,
                streaming_cfg.spot_max_buffer_rows,
            ),
            "bars": (
                streaming_cfg.bars_flush_interval_sec,
                streaming_cfg.bars_max_buffer_rows,
            ),
        }
        buffer_kinds = list(self._buffers.keys())
        per_kind_config = {k: v for k, v in per_kind_config.items() if k in buffer_kinds}
        use_per_kind = any(
            interval is not None or max_rows is not None
            for interval, max_rows in per_kind_config.values()
        )
        if use_per_kind:
            flush_intervals = {
                kind: (interval if interval is not None else flush_interval)
                for kind, (interval, _) in per_kind_config.items()
            }
            max_rows_by_kind = {
                kind: (max_rows if max_rows is not None else max_buffer_rows)
                for kind, (_, max_rows) in per_kind_config.items()
            }

        universe_entries = load_universe(Path(self.cfg.universe.file))
        conid_map = {entry.symbol: entry.conid for entry in universe_entries}

        session = self._session_factory()
        with session as sess:
            ib = sess.ensure_connected()
            self._subscribe_spot(ib, ingest_id, streaming_cfg)
            self._subscribe_bars(ib, ingest_id, streaming_cfg)
            self._subscribe_options(
                ib,
                ingest_id,
                symbols,
                trade_date,
                conid_map,
                streaming_cfg,
                generic_ticks,
            )

            next_flush = self._now_fn()
            next_flush_by_kind = {kind: self._now_fn() for kind in buffer_kinds}
            next_rebalance = self._now_fn()
            next_metrics = self._now_fn()
            end_time = (
                self._now_fn() + _timedelta_seconds(duration_seconds) if duration_seconds else None
            )

            try:
                while True:
                    if end_time and self._now_fn() >= end_time:
                        break
                    now = self._now_fn()
                    if now >= next_rebalance:
                        self._maybe_rebalance(
                            ib,
                            symbols,
                            streaming_cfg,
                            generic_ticks,
                            ingest_id,
                        )
                        next_rebalance = now + _timedelta_seconds(rebalance_check_interval)

                    if use_per_kind:
                        for kind, interval in flush_intervals.items():
                            if interval <= 0:
                                continue
                            if now >= next_flush_by_kind[kind]:
                                self._flush_buffers([kind])
                                next_flush_by_kind[kind] = now + _timedelta_seconds(interval)
                        self._flush_if_large_by_kind(max_rows_by_kind)
                    else:
                        if now >= next_flush:
                            self._flush_buffers()
                            next_flush = now + _timedelta_seconds(flush_interval)
                        self._flush_if_large(max_buffer_rows)
                    if metrics_interval > 0 and now >= next_metrics:
                        buffer_rows = self._buffer_rows()
                        last_flush_et = None
                        if self._last_flush_at:
                            last_flush_et = (
                                self._last_flush_at.replace(tzinfo=ZoneInfo("UTC"))
                                .astimezone(self._et_tz)
                                .isoformat()
                            )
                        logger.info(
                            "[streaming:metrics] buffer_rows=%s last_flush_rows=%s last_flush_at=%s",
                            buffer_rows,
                            self._last_flush_rows,
                            last_flush_et or "none",
                        )
                        next_metrics = now + _timedelta_seconds(metrics_interval)
                    ib.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("Streaming interrupted by user")
            finally:
                self._flush_buffers()
                self._unsubscribe_all(ib)

        ended_at = datetime.utcnow()
        return StreamingResult(
            ingest_id=ingest_id,
            started_at=started_at,
            ended_at=ended_at,
            option_rows=self._option_rows,
            spot_rows=self._spot_rows,
            bar_rows=self._bar_rows,
            rebalances=self._rebalances,
        )

    def _subscribe_spot(self, ib: Any, ingest_id: str, streaming_cfg) -> None:
        from ib_insync import Stock, Index  # type: ignore

        for symbol in streaming_cfg.spot_symbols:
            sym = symbol.upper()
            if sym in {"VIX", "SPX", "NDX"}:
                contract = Index(sym, "CBOE")
                exchange = "CBOE"
            else:
                contract = Stock(sym, "SMART", "USD")
                exchange = "SMART"
            ib.qualifyContracts(contract)
            ticker = ib.reqMktData(contract, "", False, False)
            setattr(
                ticker,
                "_stream_meta",
                {
                    "symbol": sym,
                    "exchange": exchange,
                    "ingest_id": ingest_id,
                    "trade_date": self._trade_date_str(),
                },
            )
            ticker.updateEvent += self._handle_spot_update
            self._spot_contracts[sym] = contract

    def _subscribe_bars(self, ib: Any, ingest_id: str, streaming_cfg) -> None:
        from ib_insync import Stock  # type: ignore

        bar_size = parse_bar_seconds(streaming_cfg.bars_interval)
        for symbol in streaming_cfg.bars_symbols:
            sym = symbol.upper()
            contract = Stock(sym, "SMART", "USD")
            ib.qualifyContracts(contract)
            bars = ib.reqRealTimeBars(contract, bar_size, "TRADES", True)
            setattr(
                bars,
                "_stream_meta",
                {
                    "symbol": sym,
                    "exchange": "SMART",
                    "ingest_id": ingest_id,
                    "trade_date": self._trade_date_str(),
                    "bar_size": streaming_cfg.bars_interval,
                },
            )
            bars.updateEvent += self._handle_bar_update
            self._bar_streams[sym] = bars

    def _subscribe_options(
        self,
        ib: Any,
        ingest_id: str,
        symbols: list[str],
        trade_date: date,
        conid_map: dict[str, int | None],
        streaming_cfg,
        generic_ticks: str,
    ) -> None:
        for symbol in symbols:
            sym = symbol.upper()
            spot = self._seed_spot(ib, sym, trade_date, conid_map.get(sym))
            params = sec_def_params(ib, sym, underlying_conid=conid_map.get(sym))
            chain = _select_chain(params, sym, streaming_cfg.exchange)
            if chain is None:
                raise RuntimeError(f"No secdef params for {sym}")
            strikes_all = [float(s) for s in getattr(chain, "strikes", []) if s is not None]
            expiries = select_expiries(getattr(chain, "expirations", []), trade_date)
            strikes = select_strikes_around_spot(
                strikes_all,
                spot,
                streaming_cfg.strikes_per_side,
            )
            self._chain_strikes[sym] = strikes_all
            self._chain_exchange[sym] = (getattr(chain, "exchange", "") or "SMART").upper()
            self._chain_trading_class[sym] = getattr(chain, "tradingClass", None) or sym
            self._option_expiries[sym] = expiries
            self._option_strikes[sym] = strikes
            self._last_rebalance_spot[sym] = spot

            tickers = self._subscribe_option_strikes(
                ib,
                sym,
                expiries,
                strikes,
                streaming_cfg,
                generic_ticks,
                ingest_id,
            )
            self._option_tickers[sym] = tickers

    def _subscribe_option_strikes(
        self,
        ib: Any,
        symbol: str,
        expiries: list[date],
        strikes: list[float],
        streaming_cfg,
        generic_ticks: str,
        ingest_id: str,
    ) -> dict[tuple, Any]:
        from ib_insync import Option  # type: ignore

        rights = [r.upper() for r in streaming_cfg.rights] or ["C", "P"]
        exchange = self._chain_exchange.get(symbol, streaming_cfg.exchange).upper()
        trading_class = self._chain_trading_class.get(symbol, symbol)

        contracts = []
        contract_meta = []
        for expiry in expiries:
            expiry_yyyymmdd = expiry.strftime("%Y%m%d")
            for strike in strikes:
                for right in rights:
                    contract = Option(
                        symbol=symbol,
                        lastTradeDateOrContractMonth=expiry_yyyymmdd,
                        strike=strike,
                        right=right,
                        exchange=exchange,
                        currency="USD",
                        tradingClass=trading_class,
                    )
                    contracts.append(contract)
                    contract_meta.append(
                        {
                            "symbol": symbol,
                            "expiry": expiry.isoformat(),
                            "strike": float(strike),
                            "right": right,
                            "exchange": exchange,
                            "tradingClass": trading_class,
                        }
                    )

        tickers: dict[tuple, Any] = {}
        if not contracts:
            return tickers

        qualified = ib.qualifyContracts(*contracts)
        for contract, meta in zip(qualified, contract_meta):
            ticker = ib.reqMktData(contract, generic_ticks, False, False)
            meta.update(
                {
                    "conid": int(getattr(contract, "conId", 0) or 0),
                    "ingest_id": ingest_id,
                    "trade_date": self._trade_date_str(),
                }
            )
            setattr(ticker, "_stream_meta", meta)
            ticker.updateEvent += self._handle_option_update
            key = (meta["expiry"], meta["strike"], meta["right"])
            tickers[key] = ticker
        return tickers

    def _maybe_rebalance(
        self,
        ib: Any,
        symbols: list[str],
        streaming_cfg,
        generic_ticks: str,
        ingest_id: str,
    ) -> None:
        for symbol in symbols:
            spot = self._spot_prices.get(symbol)
            if spot is None or spot <= 0:
                continue
            last_spot = self._last_rebalance_spot.get(symbol, spot)
            strikes_all = self._chain_strikes.get(symbol, [])
            step = strike_step(strikes_all, spot)
            if not should_rebalance(
                last_spot,
                spot,
                step,
                streaming_cfg.rebalance_threshold_steps,
            ):
                continue

            new_strikes = select_strikes_around_spot(
                strikes_all,
                spot,
                streaming_cfg.strikes_per_side,
            )
            old_strikes = self._option_strikes.get(symbol, [])
            removed, added = diff_strikes(old_strikes, new_strikes)
            if removed or added:
                self._update_option_subscriptions(
                    ib,
                    symbol,
                    removed,
                    added,
                    streaming_cfg,
                    generic_ticks,
                    ingest_id,
                )
                self._option_strikes[symbol] = new_strikes
                self._last_rebalance_spot[symbol] = spot
                self._rebalances += 1

    def _update_option_subscriptions(
        self,
        ib: Any,
        symbol: str,
        removed: list[float],
        added: list[float],
        streaming_cfg,
        generic_ticks: str,
        ingest_id: str,
    ) -> None:
        expiries = self._option_expiries.get(symbol, [])
        tickers = self._option_tickers.get(symbol, {})
        rights = [r.upper() for r in streaming_cfg.rights] or ["C", "P"]
        exchange = self._chain_exchange.get(symbol, streaming_cfg.exchange).upper()
        trading_class = self._chain_trading_class.get(symbol, symbol)

        for strike in removed:
            for expiry in expiries:
                for right in rights:
                    key = (expiry.isoformat(), float(strike), right)
                    ticker = tickers.pop(key, None)
                    if ticker is None:
                        continue
                    try:
                        ticker.updateEvent -= self._handle_option_update
                    except Exception:
                        pass
                    ib.cancelMktData(ticker.contract)

        if not added:
            return

        from ib_insync import Option  # type: ignore

        contracts = []
        metas = []
        for strike in added:
            for expiry in expiries:
                expiry_yyyymmdd = expiry.strftime("%Y%m%d")
                for right in rights:
                    contract = Option(
                        symbol=symbol,
                        lastTradeDateOrContractMonth=expiry_yyyymmdd,
                        strike=strike,
                        right=right,
                        exchange=exchange,
                        currency="USD",
                        tradingClass=trading_class,
                    )
                    contracts.append(contract)
                    metas.append(
                        {
                            "symbol": symbol,
                            "expiry": expiry.isoformat(),
                            "strike": float(strike),
                            "right": right,
                            "exchange": exchange,
                            "tradingClass": trading_class,
                        }
                    )

        qualified = ib.qualifyContracts(*contracts) if contracts else []
        for contract, meta in zip(qualified, metas):
            ticker = ib.reqMktData(contract, generic_ticks, False, False)
            meta.update(
                {
                    "conid": int(getattr(contract, "conId", 0) or 0),
                    "ingest_id": ingest_id,
                    "trade_date": self._trade_date_str(),
                }
            )
            setattr(ticker, "_stream_meta", meta)
            ticker.updateEvent += self._handle_option_update
            key = (meta["expiry"], meta["strike"], meta["right"])
            tickers[key] = ticker

    def _handle_option_update(self, ticker) -> None:
        meta = getattr(ticker, "_stream_meta", None)
        if not meta:
            return
        record = {
            "trade_date": meta["trade_date"],
            "asof_ts": datetime.utcnow().isoformat() + "Z",
            "underlying": meta["symbol"],
            "symbol": meta["symbol"],
            "expiry": meta["expiry"],
            "strike": meta["strike"],
            "right": meta["right"],
            "conid": meta.get("conid"),
            "exchange": meta["exchange"],
            "tradingClass": meta.get("tradingClass"),
            "bid": _to_float(getattr(ticker, "bid", None)),
            "ask": _to_float(getattr(ticker, "ask", None)),
            "last": _to_float(getattr(ticker, "last", None)),
            "bid_size": _to_float(getattr(ticker, "bidSize", None)),
            "ask_size": _to_float(getattr(ticker, "askSize", None)),
            "volume": _to_float(getattr(ticker, "volume", None)),
            "iv": _extract_iv(ticker),
            "delta": _extract_greek(ticker, "delta"),
            "gamma": _extract_greek(ticker, "gamma"),
            "theta": _extract_greek(ticker, "theta"),
            "vega": _extract_greek(ticker, "vega"),
            "market_data_type": getattr(ticker, "marketDataType", None),
            "source": "IBKR",
            "ingest_id": meta["ingest_id"],
        }
        self._append_buffer("options", record)

    def _handle_spot_update(self, ticker) -> None:
        meta = getattr(ticker, "_stream_meta", None)
        if not meta:
            return
        symbol = meta["symbol"]
        price = _market_price(ticker)
        if price:
            self._spot_prices[symbol] = price
        record = {
            "trade_date": meta["trade_date"],
            "asof_ts": datetime.utcnow().isoformat() + "Z",
            "underlying": symbol,
            "symbol": symbol,
            "exchange": meta["exchange"],
            "market_price": price,
            "bid": _to_float(getattr(ticker, "bid", None)),
            "ask": _to_float(getattr(ticker, "ask", None)),
            "last": _to_float(getattr(ticker, "last", None)),
            "close": _to_float(getattr(ticker, "close", None)),
            "volume": _to_float(getattr(ticker, "volume", None)),
            "market_data_type": getattr(ticker, "marketDataType", None),
            "source": "IBKR",
            "ingest_id": meta["ingest_id"],
        }
        self._append_buffer("spot", record)

    def _handle_bar_update(self, bars, *args) -> None:
        meta = getattr(bars, "_stream_meta", None)
        if not meta or not bars:
            return
        bar = bars[-1]
        bar_time = getattr(bar, "time", None)
        if isinstance(bar_time, datetime):
            asof_ts = bar_time.isoformat()
        else:
            asof_ts = datetime.utcnow().isoformat() + "Z"
        record = {
            "trade_date": meta["trade_date"],
            "asof_ts": asof_ts,
            "underlying": meta["symbol"],
            "symbol": meta["symbol"],
            "exchange": meta["exchange"],
            "bar_size": meta["bar_size"],
            "open": _to_float(getattr(bar, "open", None)),
            "high": _to_float(getattr(bar, "high", None)),
            "low": _to_float(getattr(bar, "low", None)),
            "close": _to_float(getattr(bar, "close", None)),
            "volume": _to_float(getattr(bar, "volume", None)),
            "wap": _to_float(getattr(bar, "wap", None)),
            "count": _to_float(getattr(bar, "count", None)),
            "source": "IBKR",
            "ingest_id": meta["ingest_id"],
        }
        self._append_buffer("bars", record)

    def _append_buffer(self, kind: str, record: dict) -> None:
        with self._lock:
            self._buffers[kind].append(record)

    def _flush_buffers(self, kinds: Iterable[str] | None = None) -> int:
        drained = {}
        kinds = list(kinds) if kinds is not None else list(self._buffers.keys())
        with self._lock:
            for kind in kinds:
                buf = self._buffers.get(kind, [])
                if buf:
                    drained[kind] = buf[:]
                    self._buffers[kind] = []
        flushed_rows = 0
        for kind, rows in drained.items():
            count = self._writer.write_records(kind, rows)
            if kind == "options":
                self._option_rows += count
            elif kind == "spot":
                self._spot_rows += count
            elif kind == "bars":
                self._bar_rows += count
            flushed_rows += count
        if flushed_rows:
            self._last_flush_rows = flushed_rows
            self._last_flush_at = self._now_fn()
        return flushed_rows

    def _buffer_rows(self) -> int:
        with self._lock:
            return sum(len(buf) for buf in self._buffers.values())

    def _flush_if_large(self, max_rows: int) -> None:
        if max_rows <= 0:
            return
        with self._lock:
            total = sum(len(buf) for buf in self._buffers.values())
        if total >= max_rows:
            self._flush_buffers()

    def _flush_if_large_by_kind(self, max_rows_by_kind: dict[str, int]) -> None:
        to_flush: list[str] = []
        with self._lock:
            for kind, max_rows in max_rows_by_kind.items():
                if max_rows <= 0:
                    continue
                buf = self._buffers.get(kind, [])
                if len(buf) >= max_rows:
                    to_flush.append(kind)
        if to_flush:
            self._flush_buffers(to_flush)

    def _unsubscribe_all(self, ib: Any) -> None:
        for symbol, tickers in self._option_tickers.items():
            for ticker in tickers.values():
                try:
                    ticker.updateEvent -= self._handle_option_update
                except Exception:
                    pass
                ib.cancelMktData(ticker.contract)
        for symbol, contract in self._spot_contracts.items():
            try:
                ib.cancelMktData(contract)
            except Exception:
                pass
        for bars in self._bar_streams.values():
            try:
                bars.updateEvent -= self._handle_bar_update
            except Exception:
                pass
            ib.cancelRealTimeBars(bars)

    def _trade_date_str(self) -> str:
        return to_et_date(datetime.now(ZoneInfo("UTC"))).isoformat()

    def _seed_spot(self, ib: Any, symbol: str, trade_date: date, conid: Optional[int]) -> float:
        spot = None
        if symbol in self._spot_prices:
            spot = self._spot_prices.get(symbol)
        if spot is None or spot <= 0:
            spot = fetch_underlying_close(ib, symbol, trade_date, conid)
        self._spot_prices[symbol] = spot
        return spot


def _select_chain(params: Iterable[Any], symbol: str, exchange: str):
    params = list(params)
    if not params:
        return None
    exch = exchange.upper()
    exch_matches = [p for p in params if (getattr(p, "exchange", "") or "").upper() == exch]
    if exch_matches:
        return max(exch_matches, key=lambda p: len(getattr(p, "strikes", []) or []))
    tc_matches = [
        p for p in params if (getattr(p, "tradingClass", "") or "").upper() == symbol.upper()
    ]
    if tc_matches:
        return max(tc_matches, key=lambda p: len(getattr(p, "strikes", []) or []))
    return max(params, key=lambda p: len(getattr(p, "strikes", []) or []))


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _market_price(ticker: Any) -> float | None:
    price = None
    try:
        price = ticker.marketPrice()
    except Exception:
        price = None
    if price and price > 0:
        return float(price)
    for candidate in (getattr(ticker, "last", None), getattr(ticker, "close", None)):
        try:
            if candidate and float(candidate) > 0:
                return float(candidate)
        except Exception:
            continue
    for candidate in (getattr(ticker, "bid", None), getattr(ticker, "ask", None)):
        try:
            if candidate and float(candidate) > 0:
                return float(candidate)
        except Exception:
            continue
    return None


def _extract_iv(ticker: Any) -> float | None:
    iv = _to_float(getattr(ticker, "impliedVolatility", None))
    if iv is not None:
        return iv
    greeks = getattr(ticker, "modelGreeks", None)
    if greeks is not None:
        return _to_float(getattr(greeks, "impliedVolatility", None))
    return None


def _extract_greek(ticker: Any, name: str) -> float | None:
    greeks = getattr(ticker, "modelGreeks", None)
    if greeks is None:
        greeks = getattr(ticker, "lastGreeks", None)
    return _to_float(getattr(greeks, name, None)) if greeks is not None else None


def parse_bar_seconds(value: str) -> int:
    text = str(value).strip().lower()
    if text.endswith("sec"):
        text = text[:-3]
    if text.endswith("s"):
        text = text[:-1]
    try:
        return max(int(float(text)), 1)
    except ValueError:
        return 5


def _timedelta_seconds(seconds: float | None) -> timedelta:
    if seconds is None:
        seconds = 0.0
    return timedelta(seconds=seconds)
