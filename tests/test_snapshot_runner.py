from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from zoneinfo import ZoneInfo

from opt_data.pipeline.snapshot import SnapshotRunner
from opt_data.util.calendar import TradingSession

from helpers import build_config


class DummySession:
    def __init__(self, ib: Any) -> None:
        self._ib = ib

    def ensure_connected(self) -> Any:
        return self._ib

    def __enter__(self) -> "DummySession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class DummyIB:
    pass


def test_snapshot_runner_writes_intraday_partition(tmp_path):
    cfg = build_config(tmp_path)
    now_et = datetime(2025, 10, 6, 9, 31, tzinfo=ZoneInfo("America/New_York"))
    progress_log: list[tuple[str, str, dict]] = []

    contracts: List[Dict[str, Any]] = [
        {
            "conid": 1001,
            "symbol": "AAPL",
            "expiry": "2025-11-15",
            "right": "C",
            "strike": 150.0,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "multiplier": 100,
        },
        {
            "conid": 1002,
            "symbol": "AAPL",
            "expiry": "2025-11-15",
            "right": "P",
            "strike": 140.0,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "multiplier": 100,
        },
    ]

    snapshot_rows: List[Dict[str, Any]] = [
        {
            **contracts[0],
            "bid": 10.0,
            "ask": 10.5,
            "last": 10.2,
            "close": 10.1,
            "volume": 123,
            "open_interest": None,
            "iv": 0.25,
            "delta": 0.55,
            "gamma": 0.04,
            "theta": -0.02,
            "vega": 0.11,
            "market_data_type": 1,
            "asof": "2025-10-06T13:30:05Z",
        },
        {
            **contracts[1],
            "bid": 5.0,
            "ask": 5.4,
            "last": 5.1,
            "close": 5.0,
            "volume": 456,
            "open_interest": 200,
            "iv": 0.30,
            "delta": -0.45,
            "gamma": 0.03,
            "theta": -0.01,
            "vega": 0.09,
            "market_data_type": 3,
            "asof": "2025-10-06T13:30:10Z",
        },
    ]

    runner = SnapshotRunner(
        cfg,
        session_factory=lambda: DummySession(DummyIB()),
        contract_fetcher=lambda *_, **__: contracts,
        snapshot_fetcher=lambda *_, **__: snapshot_rows,
        underlying_fetcher=lambda *_, **__: 172.35,
        now_fn=lambda: now_et,
        # capture progress to ensure per-symbol timing is emitted
        cleaner=None,
    )

    def progress_cb(symbol: str, status: str, extra: Dict) -> None:
        progress_log.append((symbol, status, extra))

    trade_date = date(2025, 10, 6)
    slot = runner.resolve_slot(trade_date, "09:30")
    result = runner.run(trade_date, slot, progress=progress_cb)

    assert result.rows_written == 2
    assert len(result.raw_paths) == 1
    assert len(result.clean_paths) == 1
    assert result.errors == []

    raw_file = result.raw_paths[0]
    assert raw_file.exists()

    df = pd.read_parquet(raw_file)
    assert set(df["conid"].tolist()) == {1001, 1002}
    assert (df["slot_30m"] == 0).all()
    assert (df["underlying"].str.upper() == "AAPL").all()
    assert "sample_time" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["sample_time"])
    # market_data_type propagated and delayed fallback flagged
    row_flags = {row.conid: set(row.data_quality_flag) for row in df.itertuples()}
    assert "missing_oi" in row_flags[1001]
    assert "delayed_fallback" in row_flags[1002]
    done_events = [evt for evt in progress_log if evt[1] == "done"]
    assert done_events, "expected per-symbol done event with timing"
    done = done_events[0]
    assert done[0] == "AAPL"
    assert done[2]["rows"] == 2
    assert done[2]["contracts"] == 2
    assert done[2]["result"] == "success"
    assert done[2]["elapsed_seconds"] >= 0
    assert "start_time_et" in done[2] and "end_time_et" in done[2]


def test_resolve_slot_defaults_to_next(tmp_path):
    cfg = build_config(tmp_path)
    runner = SnapshotRunner(
        cfg,
        session_factory=lambda: DummySession(DummyIB()),
        contract_fetcher=lambda *_, **__: [],
        snapshot_fetcher=lambda *_, **__: [],
        underlying_fetcher=lambda *_, **__: 100.0,
        now_fn=lambda: datetime(2025, 10, 6, 10, 5, tzinfo=ZoneInfo(cfg.timezone.name)),
    )

    slot = runner.resolve_slot(date(2025, 10, 6), None)
    assert slot.label == "10:00"


def test_available_slots_respects_early_close(tmp_path, monkeypatch):
    cfg = build_config(tmp_path)

    runner = SnapshotRunner(
        cfg,
        session_factory=lambda: DummySession(DummyIB()),
        contract_fetcher=lambda *_, **__: [],
        snapshot_fetcher=lambda *_, **__: [],
        underlying_fetcher=lambda *_, **__: 100.0,
        now_fn=lambda: datetime(2025, 7, 3, 12, 15, tzinfo=ZoneInfo(cfg.timezone.name)),
    )

    session = TradingSession(
        market_open=datetime(2025, 7, 3, 9, 30, tzinfo=ZoneInfo("America/New_York")),
        market_close=datetime(2025, 7, 3, 13, 0, tzinfo=ZoneInfo("America/New_York")),
        early_close=True,
    )
    monkeypatch.setattr("opt_data.pipeline.snapshot.get_trading_session", lambda _date: session)

    slots = runner.available_slots(date(2025, 7, 3))
    labels = [slot.label for slot in slots]

    assert labels[0] == "09:30"
    assert labels[-1] == "13:00"
    assert len(labels) == 8


def test_snapshot_runner_accumulates_slots(tmp_path):
    cfg = build_config(tmp_path)
    trade_date = date(2025, 10, 6)
    now_et = datetime(2025, 10, 6, 9, 35, tzinfo=ZoneInfo("America/New_York"))

    contracts: List[Dict[str, Any]] = [
        {
            "conid": 2001,
            "symbol": "AAPL",
            "expiry": "2025-11-15",
            "right": "C",
            "strike": 150.0,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "multiplier": 100,
        },
        {
            "conid": 2002,
            "symbol": "AAPL",
            "expiry": "2025-11-15",
            "right": "P",
            "strike": 150.0,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "multiplier": 100,
        },
    ]

    snapshot_rows: List[Dict[str, Any]] = [
        {
            **contracts[0],
            "bid": 1.0,
            "ask": 1.2,
            "last": 1.1,
            "volume": 50,
            "open_interest": 10,
            "iv": 0.2,
            "delta": 0.5,
            "gamma": 0.04,
            "theta": -0.01,
            "vega": 0.1,
            "market_data_type": 1,
            "asof": "2025-10-06T14:30:00Z",
        },
        {
            **contracts[1],
            "bid": 0.9,
            "ask": 1.1,
            "last": 1.0,
            "volume": 60,
            "open_interest": 12,
            "iv": 0.25,
            "delta": -0.45,
            "gamma": 0.03,
            "theta": -0.02,
            "vega": 0.11,
            "market_data_type": 1,
            "asof": "2025-10-06T14:30:00Z",
        },
    ]

    runner = SnapshotRunner(
        cfg,
        session_factory=lambda: DummySession(DummyIB()),
        contract_fetcher=lambda *_, **__: contracts,
        snapshot_fetcher=lambda *_, **__: snapshot_rows,
        underlying_fetcher=lambda *_, **__: 170.0,
        now_fn=lambda: now_et,
    )

    slots = runner.available_slots(trade_date)
    first_slot = slots[0]
    second_slot = slots[1]

    runner.run(trade_date, first_slot)
    runner.run(trade_date, second_slot)

    raw_path = (
        Path(cfg.paths.raw)
        / "view=intraday"
        / f"date={trade_date.isoformat()}"
        / "underlying=AAPL"
        / "exchange=SMART"
        / "part-000.parquet"
    )
    assert raw_path.exists()
    df = pd.read_parquet(raw_path)
    slots_present = sorted(df["slot_30m"].unique().tolist())
    assert slots_present == [first_slot.index, second_slot.index]
    assert len(df) == 4
