from __future__ import annotations

import json
import logging
import math
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import AppConfig
from ..ib.discovery import discover_contracts_for_symbol
from ..ib.session import IBSession
from ..storage.layout import partition_for
from ..storage.writer import ParquetWriter
from ..universe import load_universe
from ..util.ratelimit import TokenBucket
from ..util.calendar import get_trading_session
from ..ib.snapshot import collect_option_snapshots
from .backfill import fetch_underlying_close
from .cleaning import CleaningPipeline

logger = logging.getLogger(__name__)


DEFAULT_SNAPSHOT_GRACE_SECONDS = 120

SCOPE_REQUIRED_FIELDS = {
    "conid": None,
    "symbol": None,
    "expiry": None,
    "right": None,
    "strike": None,
    "multiplier": None,
    "exchange": None,
    "tradingClass": None,
    "bid": None,
    "ask": None,
    "mid": None,
    "last": None,
    "volume": None,
    "iv": None,
    "delta": None,
    "gamma": None,
    "theta": None,
    "vega": None,
    "market_data_type": None,
    "asof_ts": None,
    "sample_time": None,
    "slot_30m": None,
    "source": "IBKR",
    "ingest_id": None,
    "ingest_run_type": "intraday",
    "data_quality_flag": [],
}


@dataclass(frozen=True)
class SnapshotSlot:
    index: int
    et: datetime
    utc: datetime

    @property
    def label(self) -> str:
        return self.et.strftime("%H:%M")

    @property
    def et_iso(self) -> str:
        return self.et.isoformat()

    @property
    def utc_iso(self) -> str:
        return self.utc.isoformat().replace("+00:00", "Z")


@dataclass
class SnapshotResult:
    ingest_id: str
    slot: SnapshotSlot
    symbols_processed: int
    contracts_discovered: int
    rows_written: int
    raw_paths: list[Path]
    clean_paths: list[Path]
    errors: list[dict[str, Any]]


def _slot_schedule(trade_date: date, tz_name: str) -> list[SnapshotSlot]:
    tz = ZoneInfo(tz_name)

    session = get_trading_session(trade_date)
    start = session.market_open.astimezone(tz)
    end_dt = session.market_close.astimezone(tz)

    if end_dt <= start:
        end_dt = datetime.combine(trade_date, dtime(hour=16, minute=0), tzinfo=tz)
        start = datetime.combine(trade_date, dtime(hour=9, minute=30), tzinfo=tz)

    slots: list[SnapshotSlot] = []
    current = start
    index = 0
    while current < end_dt:
        slots.append(
            SnapshotSlot(
                index=index,
                et=current,
                utc=current.astimezone(ZoneInfo("UTC")),
            )
        )
        current = current + timedelta(minutes=30)
        index += 1
    if not slots or slots[-1].et != end_dt:
        slots.append(
            SnapshotSlot(
                index=index,
                et=end_dt,
                utc=end_dt.astimezone(ZoneInfo("UTC")),
            )
        )
    return slots


def _default_session_factory(cfg: AppConfig) -> IBSession:
    return IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        market_data_type=cfg.ib.market_data_type,
    )


def _write_error_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        **payload,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


class SnapshotRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        session_factory: Callable[[], IBSession] | None = None,
        contract_fetcher: Callable[..., List[Dict[str, Any]]] | None = None,
        snapshot_fetcher: Callable[..., List[Dict[str, Any]]] | None = None,
        underlying_fetcher: Callable[..., float] | None = None,
        writer: ParquetWriter | None = None,
        cleaner: CleaningPipeline | None = None,
        now_fn: Callable[[], datetime] | None = None,
        snapshot_grace_seconds: int = DEFAULT_SNAPSHOT_GRACE_SECONDS,
    ) -> None:
        self.cfg = cfg
        self._session_factory = session_factory or (lambda: _default_session_factory(cfg))
        self._contract_fetcher = contract_fetcher or (
            lambda session,
            symbol,
            trade_date,
            price,
            config,
            **kwargs: discover_contracts_for_symbol(  # type: ignore[return-value]
                session,
                symbol,
                trade_date,
                price,
                config,
                max_strikes_per_expiry=config.acquisition.max_strikes_per_expiry,
                **kwargs,
            )
        )
        self._snapshot_fetcher = snapshot_fetcher or collect_option_snapshots
        self._underlying_fetcher = underlying_fetcher or (
            lambda ib, symbol, dt, conid=None: fetch_underlying_close(ib, symbol, dt, conid)
        )
        self._writer = writer or ParquetWriter(cfg)
        self._cleaner = cleaner or CleaningPipeline.create(cfg)
        self._now_fn = now_fn or (lambda: datetime.now(ZoneInfo(cfg.timezone.name)))
        self._tz = ZoneInfo(cfg.timezone.name)
        snapshot_cfg = getattr(cfg, "snapshot", None)
        if snapshot_cfg is not None:
            self._generic_ticks = snapshot_cfg.generic_ticks or cfg.cli.default_generic_ticks
        else:
            self._generic_ticks = cfg.cli.default_generic_ticks
        if not self._generic_ticks:
            self._generic_ticks = "100,101,104,105,106,165,221,225,233,293,294,295"
        self._snapshot_cfg = snapshot_cfg
        self._grace_seconds = snapshot_grace_seconds

        self._limiters: dict[str, TokenBucket] = {
            "discovery": TokenBucket.create(
                capacity=cfg.rate_limits.discovery.burst,
                refill_per_minute=cfg.rate_limits.discovery.per_minute,
            ),
            "snapshot": TokenBucket.create(
                capacity=cfg.rate_limits.snapshot.burst,
                refill_per_minute=cfg.rate_limits.snapshot.per_minute,
            ),
        }

    def available_slots(self, trade_date: date) -> list[SnapshotSlot]:
        return _slot_schedule(trade_date, self.cfg.timezone.name)

    def resolve_slot(self, trade_date: date, slot_label: str | None) -> SnapshotSlot:
        slots = self.available_slots(trade_date)
        if not slots:
            raise ValueError("No slots available for the given date")

        if slot_label is None or slot_label.lower() in {"now", "next"}:
            now_et = self._now_fn().astimezone(self._tz)
            first = slots[0]
            if now_et <= first.et + timedelta(seconds=self._grace_seconds):
                return first
            last = slots[-1]
            if now_et >= last.et + timedelta(minutes=30):
                return last
            base = first.et
            delta = now_et - base
            if delta.total_seconds() < 0:
                return first
            slot_index = int(delta.total_seconds() // (30 * 60))
            slot_index = max(0, min(slot_index, len(slots) - 1))
            return slots[slot_index]

        normalized = slot_label.strip()
        for slot in slots:
            if slot.label == normalized:
                return slot
        raise ValueError(f"Unknown slot label: {slot_label}")

    def run(
        self,
        trade_date: date,
        slot: SnapshotSlot,
        symbols: Sequence[str] | None = None,
        *,
        force_refresh: bool = False,
        progress: Callable[[str, str, Dict[str, Any]], None] | None = None,
    ) -> SnapshotResult:
        universe = load_universe(self.cfg.universe.file)
        wanted = {sym.upper() for sym in symbols} if symbols else None
        entries = [u for u in universe if wanted is None or u.symbol in wanted]
        if not entries:
            raise ValueError("No symbols available after filtering; check universe configuration")

        ingest_id = uuid.uuid4().hex
        errors: list[dict[str, Any]] = []
        raw_files: list[Path] = []
        clean_files: list[Path] = []
        all_rows: list[dict[str, Any]] = []
        contracts_total = 0

        log_dir = Path(self.cfg.paths.run_logs) / "snapshot"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        log_file = (
            log_dir
            / f"snapshot_{trade_date.isoformat()}_{slot.label.replace(':', '')}_{timestamp}.log"
        )

        def log_line(message: str) -> None:
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(message + "\n")

        error_file = (
            Path(self.cfg.paths.run_logs) / "errors" / f"errors_{trade_date.strftime('%Y%m%d')}.log"
        )

        def record_error(
            symbol: str, stage: str, exc: Exception | None, extra: dict[str, Any] | None = None
        ) -> None:
            payload = {
                "component": "snapshot",
                "symbol": symbol,
                "stage": stage,
                "slot": slot.label,
            }
            if extra:
                payload.update(extra)
            if exc is not None:
                payload["error"] = str(exc)
            errors.append(payload)
            _write_error_line(error_file, payload)

        def emit(symbol: str, status: str, details: dict[str, Any]) -> None:
            msg = json.dumps(
                {
                    "symbol": symbol,
                    "status": status,
                    "slot": slot.label,
                    **details,
                },
                ensure_ascii=False,
            )
            log_line(msg)
            if progress:
                progress(symbol, status, details)

        session = self._session_factory()

        with session as sess:
            ib = sess.ensure_connected()
            for entry in entries:
                symbol = entry.symbol
                emit(symbol, "start", {})
                try:
                    reference_price = self._fetch_reference_price(
                        ib, symbol, trade_date, entry.conid
                    )
                    emit(symbol, "reference_price", {"price": reference_price})
                except Exception as exc:
                    record_error(symbol, "reference_price", exc, {})
                    emit(symbol, "skip", {"reason": "reference_price_failed"})
                    continue

                try:
                    contracts = self._contract_fetcher(
                        sess,
                        symbol,
                        trade_date,
                        reference_price,
                        self.cfg,
                        underlying_conid=entry.conid,
                        force_refresh=force_refresh,
                        acquire_token=self._make_acquire("discovery"),
                    )
                except Exception as exc:
                    record_error(symbol, "contracts", exc, {})
                    emit(symbol, "skip", {"reason": "contracts_failed"})
                    continue

                if not contracts:
                    emit(symbol, "no_contracts", {"reference_price": reference_price})
                    continue

                contracts_total += len(contracts)

                try:
                    rows = self._capture_snapshot_rows(
                        ib,
                        contracts,
                        reference_price=reference_price,
                        acquire_token=self._make_acquire("snapshot"),
                    )
                except Exception as exc:
                    record_error(symbol, "snapshot", exc, {"contracts": len(contracts)})
                    emit(symbol, "skip", {"reason": "snapshot_failed"})
                    continue

                if not rows:
                    record_error(symbol, "snapshot", None, {"reason": "no_rows"})
                    emit(symbol, "skip", {"reason": "snapshot_empty"})
                    continue

                enriched = self._enrich_rows(
                    rows,
                    symbol=symbol,
                    trade_date=trade_date,
                    slot=slot,
                    ingest_id=ingest_id,
                    reference_price=reference_price,
                )
                all_rows.extend(enriched)
                emit(symbol, "rows", {"count": len(enriched)})

        if not all_rows:
            return SnapshotResult(
                ingest_id=ingest_id,
                slot=slot,
                symbols_processed=len(entries),
                contracts_discovered=contracts_total,
                rows_written=0,
                raw_paths=[],
                clean_paths=[],
                errors=errors,
            )

        raw_df = pd.DataFrame(all_rows)
        raw_df = self._deduplicate(raw_df)

        clean_df, _ = self._cleaner.process(raw_df.copy())
        if "data_quality_flag" in raw_df.columns and "data_quality_flag" in clean_df.columns:
            clean_df["data_quality_flag"] = raw_df["data_quality_flag"]

        raw_root = Path(self.cfg.paths.raw) / "view=intraday"
        clean_root = Path(self.cfg.paths.clean) / "view=intraday"

        group_keys = ["symbol", "exchange"]
        rows_written = 0
        for (symbol, exchange), group in raw_df.groupby(group_keys):
            part = partition_for(self.cfg, raw_root, trade_date, symbol, exchange)
            path = self._writer.write_dataframe(group, part)
            raw_files.append(path)
            rows_written += len(group)

        for (symbol, exchange), group in clean_df.groupby(group_keys):
            part = partition_for(self.cfg, clean_root, trade_date, symbol, exchange)
            path = self._writer.write_dataframe(group, part)
            clean_files.append(path)

        return SnapshotResult(
            ingest_id=ingest_id,
            slot=slot,
            symbols_processed=len(entries),
            contracts_discovered=contracts_total,
            rows_written=rows_written,
            raw_paths=raw_files,
            clean_paths=clean_files,
            errors=errors,
        )

    def _fetch_reference_price(
        self, ib: Any, symbol: str, trade_date: date, underlying_conid: Optional[int]
    ) -> float:
        # Try the trade_date first, fall back to previous days if necessary
        attempts = 0
        current_date = trade_date
        last_exception: Exception | None = None
        while attempts < 3:
            try:
                price = self._underlying_fetcher(ib, symbol, current_date, underlying_conid)
                if math.isnan(price) or price <= 0:
                    raise ValueError(f"invalid reference price {price}")
                return price
            except Exception as exc:  # pragma: no cover - network behaviour
                last_exception = exc
                attempts += 1
                current_date = current_date - timedelta(days=1)
        assert last_exception is not None
        raise last_exception

    def _enrich_rows(
        self,
        rows: Iterable[Dict[str, Any]],
        *,
        symbol: str,
        trade_date: date,
        slot: SnapshotSlot,
        ingest_id: str,
        reference_price: float,
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        sample_time_utc_str = slot.utc_iso
        sample_time_et = slot.et_iso
        sample_time_dt = slot.utc.replace(tzinfo=None)
        for row in rows:
            asof_value = row.pop("asof", None) or sample_time_utc_str
            market_data_type = row.get("market_data_type")
            flags: list[str] = []
            if market_data_type not in (None, 1):
                flags.append("delayed_fallback")
            if row.get("open_interest") in (None, ""):
                flags.append("missing_oi")

            price_ready = row.pop("price_ready", True)
            greeks_ready = row.pop("greeks_ready", True)
            if not price_ready:
                flags.append("missing_price")
            if not greeks_ready:
                flags.append("missing_greeks")

            if row.pop("snapshot_timed_out", False):
                flags.append("snapshot_timeout")

            exchange_rank = row.pop("_exchange_rank", 0)
            if exchange_rank:
                flags.append("exchange_fallback")

            enriched.append(
                self._apply_scope_defaults(
                    {
                        **row,
                        "trade_date": datetime.combine(trade_date, dtime.min),
                        "sample_time": sample_time_dt,
                        "sample_time_et": sample_time_et,
                        "slot_30m": slot.index,
                        "asof_ts": asof_value,
                        "underlying": symbol,
                        "underlying_close": reference_price,
                        "ingest_id": ingest_id,
                        "ingest_run_type": "intraday",
                        "source": "IBKR",
                        "data_quality_flag": flags,
                    }
                )
            )
        return enriched

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        df["trade_date"] = pd.to_datetime(
            df["trade_date"], utc=False, errors="coerce"
        ).dt.normalize()
        df["sample_time"] = pd.to_datetime(df["sample_time"], utc=False, errors="coerce")
        df["asof_ts"] = pd.to_datetime(df["asof_ts"], utc=True, errors="coerce").dt.tz_convert(None)
        if "exchange" in df.columns:
            df["exchange"] = df["exchange"].astype(str).str.upper()
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].astype(str).str.upper()
        df.sort_values(by=["conid", "sample_time", "asof_ts"], inplace=True)
        deduped = df.drop_duplicates(subset=["conid", "sample_time"], keep="last")
        # Ensure data_quality_flag remains list-typed
        if "data_quality_flag" in deduped.columns:
            deduped["data_quality_flag"] = deduped["data_quality_flag"].apply(
                lambda x: x if isinstance(x, list) else ([] if pd.isna(x) else [str(x)])
            )
        return deduped

    def _capture_snapshot_rows(
        self,
        ib: Any,
        contracts: Sequence[Dict[str, Any]],
        *,
        reference_price: float,
        acquire_token: Callable[[], None],
    ) -> list[dict[str, Any]]:
        preferences = self._preferred_exchanges()
        timeout = (
            self._snapshot_cfg.subscription_timeout
            if self._snapshot_cfg
            else 12.0
        )
        poll_interval = (
            self._snapshot_cfg.subscription_poll_interval
            if self._snapshot_cfg
            else 0.25
        )
        require_greeks = self._snapshot_cfg.require_greeks if self._snapshot_cfg else True

        for rank, exchange in enumerate(preferences):
            subset = self._filter_by_exchange(contracts, exchange)
            if not subset:
                continue
            limited = self._limit_contracts(subset, reference_price)
            if not limited:
                continue
            prepared = [dict(contract, _exchange_rank=rank) for contract in limited]
            rows = self._snapshot_fetcher(
                ib,
                prepared,
                generic_ticks=self._generic_ticks,
                timeout=timeout,
                poll_interval=poll_interval,
                acquire_token=acquire_token,
                require_greeks=require_greeks,
            )
            if rows:
                return rows
        return []

    def _preferred_exchanges(self) -> list[str]:
        cfg = self._snapshot_cfg
        seen: set[str] = set()
        order: list[str] = []
        if cfg:
            primary = (cfg.exchange or "").strip().upper()
            if primary and primary not in seen:
                order.append(primary)
                seen.add(primary)
            for fallback in cfg.fallback_exchanges:
                ex = str(fallback).strip().upper()
                if ex and ex not in seen:
                    order.append(ex)
                    seen.add(ex)
        else:
            order.append("SMART")
        order.append("ANY")
        return order

    def _filter_by_exchange(
        self, contracts: Sequence[Dict[str, Any]], exchange: str
    ) -> list[Dict[str, Any]]:
        if exchange in {"ANY", "*"}:
            return list(contracts)
        exchange_upper = exchange.strip().upper()
        return [
            contract
            for contract in contracts
            if str(contract.get("exchange", "")).upper() == exchange_upper
        ]

    def _limit_contracts(
        self, contracts: Sequence[Dict[str, Any]], reference_price: float
    ) -> list[Dict[str, Any]]:
        cfg = self._snapshot_cfg
        if not cfg or cfg.strikes_per_side <= 0:
            return list(contracts)
        strikes = []
        for contract in contracts:
            try:
                strike_val = float(contract.get("strike", 0.0))
            except (TypeError, ValueError):
                continue
            strikes.append(strike_val)
        if not strikes:
            return list(contracts)
        unique_strikes = sorted(set(strikes), key=lambda s: abs(s - reference_price))
        selected = unique_strikes[: cfg.strikes_per_side]
        if not selected:
            return list(contracts)
        selected_set = set(selected)
        return [
            contract
            for contract in contracts
            if _float_or_none(contract.get("strike")) in selected_set
        ]

    def _apply_scope_defaults(self, row: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(row)
        for key, default in SCOPE_REQUIRED_FIELDS.items():
            if key not in normalized or normalized[key] is None:
                normalized[key] = [] if isinstance(default, list) else default
        # ensure data_quality_flag list
        dq = normalized.get("data_quality_flag", [])
        if not isinstance(dq, list):
            dq = [dq]
        else:
            dq = [str(flag) for flag in dq if flag]
        seen: set[str] = set()
        ordered: list[str] = []
        for flag in dq:
            if flag not in seen:
                seen.add(flag)
                ordered.append(flag)
        normalized["data_quality_flag"] = ordered
        return normalized

    def _make_acquire(self, kind: str) -> Callable[[], None]:
        bucket = self._limiters[kind]

        def acquire() -> None:
            while not bucket.try_acquire():
                time.sleep(0.1)

        return acquire


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
