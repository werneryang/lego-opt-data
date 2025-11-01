from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

import pandas as pd
from zoneinfo import ZoneInfo

from opt_data.pipeline.snapshot import SnapshotRunner

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
    )

    trade_date = date(2025, 10, 6)
    slot = runner.resolve_slot(trade_date, "09:30")
    result = runner.run(trade_date, slot)

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
    row_flags = {
        row.conid: row.data_quality_flag for row in df.itertuples()
    }
    assert row_flags[1002] == ["delayed_fallback"]


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
