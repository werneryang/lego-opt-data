from datetime import datetime

import pandas as pd
import pytest

from opt_data.config import (
    AppConfig,
    IBConfig,
    TimezoneConfig,
    PathsConfig,
    UniverseConfig,
    FiltersConfig,
    RateLimitClassConfig,
    RateLimitsConfig,
    StorageConfig,
    CompactionConfig,
    LoggingConfig,
    CLIConfig,
    ReferenceConfig,
    AcquisitionConfig,
)
from opt_data.pipeline.cleaning import CleaningPipeline
from opt_data.pipeline.actions import CorporateActionsAdjuster


def _cfg(tmp_path, actions_path=None) -> AppConfig:
    reference_path = actions_path or (tmp_path / "actions.csv")
    return AppConfig(
        ib=IBConfig(host="127.0.0.1", port=7497, client_id=1, market_data_type=2),
        timezone=TimezoneConfig(name="America/New_York", update_time="17:00"),
        paths=PathsConfig(
            raw=tmp_path / "raw",
            clean=tmp_path / "clean",
            state=tmp_path / "state",
            contracts_cache=tmp_path / "cache",
            run_logs=tmp_path / "logs",
        ),
        universe=UniverseConfig(file=tmp_path / "universe.csv", refresh_days=30),
        reference=ReferenceConfig(corporate_actions=reference_path),
        filters=FiltersConfig(moneyness_pct=0.3, expiry_types=["monthly", "quarterly"]),
        rate_limits=RateLimitsConfig(
            discovery=RateLimitClassConfig(per_minute=5, burst=5),
            snapshot=RateLimitClassConfig(per_minute=20, burst=10, max_concurrent=4),
            historical=RateLimitClassConfig(per_minute=20, burst=10),
        ),
        storage=StorageConfig(
            hot_days=14, cold_codec="zstd", cold_codec_level=7, hot_codec="snappy"
        ),
        compaction=CompactionConfig(
            enabled=True,
            schedule="weekly",
            weekday="sunday",
            start_time="03:00",
            min_file_size_mb=32,
            max_file_size_mb=256,
        ),
        logging=LoggingConfig(level="INFO", format="json"),
        cli=CLIConfig(default_generic_ticks="100"),
        acquisition=AcquisitionConfig(
            mode="snapshot",
            duration="1 D",
            bar_size="1 day",
            what_to_show="TRADES",
            use_rth=True,
            max_strikes_per_expiry=21,
            fill_missing_greeks_with_zero=False,
            historical_timeout=30.0,
        ),
    )


def test_cleaning_pipeline_basic(tmp_path) -> None:
    cfg = _cfg(tmp_path)
    adjuster = CorporateActionsAdjuster(actions=None)
    pipeline = CleaningPipeline(cfg, adjuster)

    data = pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL"],
            "trade_date": ["2024-10-01", "2024-10-01"],
            "strike": [150.0, 155.0],
            "multiplier": [100.0, 100.0],
            "bid": [1.2, 2.3],
            "ask": [1.4, 2.6],
            "underlying_close": [170.0, 170.0],
            "market_data_type": [2, 2],
            "asof_ts": [datetime.utcnow(), datetime.utcnow()],
        }
    )

    clean, adjusted = pipeline.process(data)

    assert "mid" in clean.columns
    assert clean.loc[0, "mid"] == pytest.approx(1.3)
    assert "moneyness_pct" in clean.columns
    assert adjusted["underlying_close_adj"].equals(clean["underlying_close"])
    assert adjusted["strike_adj"].equals(clean["strike"])
    assert adjusted["moneyness_pct_adj"].equals(clean["moneyness_pct"])


def test_corporate_actions_adjustment(tmp_path) -> None:
    actions_path = tmp_path / "actions.csv"
    actions_path.write_text(
        "symbol,effective_date,split_ratio\nAAPL,2024-09-15,2.0\n", encoding="utf-8"
    )

    cfg = _cfg(tmp_path, actions_path)
    adjuster = CorporateActionsAdjuster.from_config(cfg)
    pipeline = CleaningPipeline(cfg, adjuster)

    data = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "trade_date": ["2024-10-01"],
            "strike": [200.0],
            "multiplier": [100.0],
            "bid": [1.0],
            "ask": [1.2],
            "underlying_close": [180.0],
            "market_data_type": [2],
            "asof_ts": [datetime.utcnow()],
        }
    )

    clean, adjusted = pipeline.process(data)
    assert float(adjusted.iloc[0]["underlying_close_adj"]) == 90.0
    assert float(adjusted.iloc[0]["strike_adj"]) == 100.0
    assert abs(adjusted.iloc[0]["moneyness_pct_adj"] - clean.iloc[0]["moneyness_pct"]) < 1e-9
