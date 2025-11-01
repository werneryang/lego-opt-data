from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from opt_data.pipeline.qa import QAMetricsCalculator

from helpers import build_config


def _write_parquet(df: pd.DataFrame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_qa_metrics_pass(tmp_path):
    cfg = build_config(tmp_path)
    trade_date = date(2025, 10, 6)
    day_str = trade_date.isoformat()

    intraday_rows = []
    for symbol in ("AAPL", "MSFT"):
        for slot in range(14):
            intraday_rows.append(
                {
                    "underlying": symbol,
                    "slot_30m": slot,
                    "data_quality_flag": [],
                    "market_data_type": 1,
                    "sample_time": datetime(2025, 10, 6, 9, 30) + pd.Timedelta(minutes=30 * slot),
                }
            )
    intraday_df = pd.DataFrame(intraday_rows)
    _write_parquet(
        intraday_df[intraday_df["underlying"] == "AAPL"],
        cfg.paths.clean
        / "view=intraday"
        / f"date={day_str}"
        / "underlying=AAPL"
        / "exchange=SMART"
        / "part-000.parquet",
    )
    _write_parquet(
        intraday_df[intraday_df["underlying"] == "MSFT"],
        cfg.paths.clean
        / "view=intraday"
        / f"date={day_str}"
        / "underlying=MSFT"
        / "exchange=SMART"
        / "part-000.parquet",
    )

    daily_df = pd.DataFrame(
        [
            {
                "underlying": "AAPL",
                "rollup_strategy": "close",
                "open_interest": 123,
                "data_quality_flag": ["oi_enriched"],
            },
            {
                "underlying": "MSFT",
                "rollup_strategy": "close",
                "open_interest": 456,
                "data_quality_flag": ["oi_enriched"],
            },
        ]
    )
    _write_parquet(
        daily_df,
        cfg.paths.clean
        / "view=daily_clean"
        / f"date={day_str}"
        / "underlying=AAPL"
        / "exchange=SMART"
        / "part-000.parquet",
    )
    _write_parquet(
        daily_df[daily_df["underlying"] == "MSFT"],
        cfg.paths.clean
        / "view=daily_clean"
        / f"date={day_str}"
        / "underlying=MSFT"
        / "exchange=SMART"
        / "part-000.parquet",
    )

    calculator = QAMetricsCalculator(cfg)
    result = calculator.evaluate(trade_date)

    assert result.status == "PASS"
    assert not result.breaches
    path = calculator.persist(result)
    assert path.exists()


def test_qa_metrics_detects_failures(tmp_path):
    cfg = build_config(tmp_path)
    trade_date = date(2025, 10, 6)
    day_str = trade_date.isoformat()

    # Only 4 slots captured and delayed rows present
    intraday_df = pd.DataFrame(
        [
            {
                "underlying": "AAPL",
                "slot_30m": slot,
                "data_quality_flag": ["delayed_fallback"],
                "market_data_type": 3,
                "sample_time": datetime(2025, 10, 6, 9, 30) + pd.Timedelta(minutes=30 * slot),
            }
            for slot in range(4)
        ]
    )
    _write_parquet(
        intraday_df,
        cfg.paths.clean
        / "view=intraday"
        / f"date={day_str}"
        / "underlying=AAPL"
        / "exchange=SMART"
        / "part-000.parquet",
    )

    daily_df = pd.DataFrame(
        [
            {
                "underlying": "AAPL",
                "rollup_strategy": "last_good",
                "open_interest": None,
                "data_quality_flag": ["missing_oi"],
            }
        ]
    )
    _write_parquet(
        daily_df,
        cfg.paths.clean
        / "view=daily_clean"
        / f"date={day_str}"
        / "underlying=AAPL"
        / "exchange=SMART"
        / "part-000.parquet",
    )

    calculator = QAMetricsCalculator(cfg)
    result = calculator.evaluate(trade_date)

    assert result.status == "FAIL"
    assert set(result.breaches) == {
        "slot_coverage_min",
        "delayed_ratio",
        "rollup_fallback_ratio",
        "oi_enrichment_ratio",
    }
