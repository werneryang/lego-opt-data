from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import pyarrow.parquet as pq

from opt_data.pipeline.rollup import RollupRunner
from opt_data.storage.writer import ParquetWriter
from opt_data.storage.layout import partition_for

from helpers import build_config


def test_rollup_runner_generates_daily_views(tmp_path):
    cfg = build_config(tmp_path)
    trade_date = date(2025, 10, 6)
    intraday_root = cfg.paths.clean / "view=intraday"

    rows = [
        {
            "trade_date": datetime(2025, 10, 6),
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
            "asof_ts": "2025-10-06T19:30:05Z",
            "sample_time": datetime(2025, 10, 6, 19, 30, 0),
            "sample_time_et": "15:30",
            "slot_30m": 12,
            "ingest_id": "abc",
            "ingest_run_type": "intraday",
            "underlying_close": 172.35,
            "data_quality_flag": [],
        },
        {
            "trade_date": datetime(2025, 10, 6),
            "underlying": "AAPL",
            "symbol": "AAPL  251220C00150000",
            "conid": 1001,
            "expiry": datetime(2025, 12, 20),
            "right": "C",
            "strike": 150.0,
            "multiplier": 100,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "bid": 10.1,
            "ask": 10.6,
            "mid": 10.35,
            "last": 10.3,
            "volume": 150,
            "iv": 0.26,
            "delta": 0.56,
            "gamma": 0.04,
            "theta": -0.02,
            "vega": 0.11,
            "market_data_type": 1,
            "asof_ts": "2025-10-06T20:00:05Z",
            "sample_time": datetime(2025, 10, 6, 20, 0, 0),
            "sample_time_et": "16:00",
            "slot_30m": 13,
            "ingest_id": "def",
            "ingest_run_type": "intraday",
            "underlying_close": 173.0,
            "data_quality_flag": [],
        },
        {
            "trade_date": datetime(2025, 10, 6),
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
            "market_data_type": 3,
            "asof_ts": "2025-10-06T19:30:10Z",
            "sample_time": datetime(2025, 10, 6, 19, 30, 0),
            "sample_time_et": "15:30",
            "slot_30m": 12,
            "ingest_id": "ghi",
            "ingest_run_type": "intraday",
            "underlying_close": 173.0,
            "data_quality_flag": ["delayed_fallback"],
        },
        {
            "trade_date": datetime(2025, 10, 6),
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
            "asof_ts": "2025-10-06T19:00:10Z",
            "sample_time": datetime(2025, 10, 6, 19, 0, 0),
            "sample_time_et": "15:00",
            "slot_30m": 11,
            "ingest_id": "jkl",
            "ingest_run_type": "intraday",
            "underlying_close": 173.0,
            "data_quality_flag": [],
        },
    ]

    df = pd.DataFrame(rows)
    writer = ParquetWriter(cfg)
    part = partition_for(cfg, intraday_root, trade_date, "AAPL", "SMART")
    writer.write_dataframe(df, part)

    runner = RollupRunner(cfg)
    result = runner.run(trade_date)

    assert result.rows_written == 3
    assert result.symbols_processed == 1
    assert result.errors == []
    assert result.strategy_counts == {"close": 1, "slot_1530": 1, "last_good": 1}
    assert len(result.daily_clean_paths) == 1
    assert len(result.daily_adjusted_paths) == 1

    daily_clean_file = result.daily_clean_paths[0]
    assert daily_clean_file.exists()
    daily_df = pq.read_table(daily_clean_file).to_pandas()

    assert "slot_30m" not in daily_df.columns
    assert "rollup_source_time" in daily_df.columns
    assert (daily_df["ingest_run_type"] == "eod_rollup").all()

    strategies = {row.conid: row.rollup_strategy for row in daily_df.itertuples()}
    assert strategies[1001] == "close"
    assert strategies[1002] == "slot_1530"
    assert strategies[1003] == "last_good"

    flags_value = daily_df.loc[daily_df["conid"] == 1002, "data_quality_flag"].iloc[0]
    assert list(flags_value) == ["delayed_fallback"]

    daily_adj_file = result.daily_adjusted_paths[0]
    adjusted_df = pq.read_table(daily_adj_file).to_pandas()
    assert "underlying_close_adj" in adjusted_df.columns
    assert (adjusted_df["underlying_close_adj"] == adjusted_df["underlying_close"]).all()
