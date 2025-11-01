from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import pyarrow.parquet as pq

from opt_data.pipeline.rollup import RollupRunner
from opt_data.pipeline.enrichment import EnrichmentRunner
from opt_data.storage.writer import ParquetWriter
from opt_data.storage.layout import partition_for

from helpers import build_config


def test_enrichment_updates_missing_open_interest(tmp_path):
    cfg = build_config(tmp_path)
    trade_date = date(2025, 10, 7)
    intraday_root = cfg.paths.clean / "view=intraday"

    rows = [
        {
            "trade_date": datetime(2025, 10, 7),
            "underlying": "AAPL",
            "symbol": "AAPL  251220C00150000",
            "conid": 1001,
            "expiry": datetime(2025, 12, 20),
            "right": "C",
            "strike": 150.0,
            "multiplier": 100,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "bid": 10.0,
            "ask": 10.5,
            "mid": 10.25,
            "last": 10.2,
            "volume": 123,
            "iv": 0.25,
            "delta": 0.55,
            "gamma": 0.04,
            "theta": -0.02,
            "vega": 0.11,
            "market_data_type": 1,
            "asof_ts": "2025-10-07T20:00:05Z",
            "sample_time": datetime(2025, 10, 7, 20, 0, 0),
            "sample_time_et": "16:00",
            "slot_30m": 13,
            "ingest_id": "slot",
            "ingest_run_type": "intraday",
            "underlying_close": 173.0,
            "open_interest": None,
            "data_quality_flag": ["missing_oi"],
        },
        {
            "trade_date": datetime(2025, 10, 7),
            "underlying": "AAPL",
            "symbol": "AAPL  251220P00150000",
            "conid": 1002,
            "expiry": datetime(2025, 12, 20),
            "right": "P",
            "strike": 150.0,
            "multiplier": 100,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "bid": 5.0,
            "ask": 5.4,
            "mid": 5.2,
            "last": 5.1,
            "volume": 456,
            "iv": 0.30,
            "delta": -0.45,
            "gamma": 0.03,
            "theta": -0.01,
            "vega": 0.09,
            "market_data_type": 1,
            "asof_ts": "2025-10-07T20:00:05Z",
            "sample_time": datetime(2025, 10, 7, 20, 0, 0),
            "sample_time_et": "16:00",
            "slot_30m": 13,
            "ingest_id": "slot",
            "ingest_run_type": "intraday",
            "underlying_close": 173.0,
            "open_interest": 200,
            "data_quality_flag": [],
        },
        {
            "trade_date": datetime(2025, 10, 7),
            "underlying": "AAPL",
            "symbol": "AAPL  251220P00160000",
            "conid": 1003,
            "expiry": datetime(2025, 12, 20),
            "right": "P",
            "strike": 160.0,
            "multiplier": 100,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "bid": 6.0,
            "ask": 6.5,
            "mid": 6.25,
            "last": 6.1,
            "volume": 100,
            "iv": 0.28,
            "delta": -0.35,
            "gamma": 0.02,
            "theta": -0.02,
            "vega": 0.08,
            "market_data_type": 1,
            "asof_ts": "2025-10-07T19:30:05Z",
            "sample_time": datetime(2025, 10, 7, 19, 30, 0),
            "sample_time_et": "15:30",
            "slot_30m": 12,
            "ingest_id": "slot",
            "ingest_run_type": "intraday",
            "underlying_close": 172.5,
            "open_interest": None,
            "data_quality_flag": ["missing_oi"],
        },
    ]

    df = pd.DataFrame(rows)
    writer = ParquetWriter(cfg)
    part = partition_for(cfg, intraday_root, trade_date, "AAPL", "SMART")
    writer.write_dataframe(df, part)

    rollup_runner = RollupRunner(cfg)
    rollup_runner.run(trade_date)

    def fake_fetcher(_ib, row, _trade_date, *, duration, use_rth):
        assert duration == cfg.enrichment.oi_duration
        assert use_rth == cfg.enrichment.oi_use_rth
        if int(row["conid"]) == 1001:
            return 555, trade_date
        return None

    class DummySession:
        def ensure_connected(self):
            return object()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    runner = EnrichmentRunner(
        cfg,
        session_factory=lambda: DummySession(),
        oi_fetcher=fake_fetcher,
    )
    result = runner.run(trade_date)

    assert result.rows_updated == 1
    assert result.rows_considered == 2
    assert result.symbols_processed == 1
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.get("conid") == 1003
    assert error.get("stage") == "fetch_open_interest"
    assert len(result.enrichment_paths) == 1

    daily_file = result.daily_clean_paths[0]
    daily_df = pq.read_table(daily_file).to_pandas()

    row_1001 = daily_df.loc[daily_df["conid"] == 1001].iloc[0]
    assert row_1001["open_interest"] == 555
    assert str(row_1001["ingest_run_type"]) == "enrichment"
    assert "missing_oi" not in list(row_1001["data_quality_flag"])
    assert "oi_enriched" in list(row_1001["data_quality_flag"])

    row_1003 = daily_df.loc[daily_df["conid"] == 1003].iloc[0]
    assert pd.isna(row_1003["open_interest"])
    assert "missing_oi" in list(row_1003["data_quality_flag"])

    enrichment_file = result.enrichment_paths[0]
    enrichment_df = pq.read_table(enrichment_file).to_pandas()
    assert len(enrichment_df) == 1
    record = enrichment_df.iloc[0]
    assert record["conid"] == 1001
    assert list(record["fields_updated"]) == ["open_interest"]
    assert str(record["ingest_run_type"]) == "enrichment"
