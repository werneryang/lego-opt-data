from datetime import date, timedelta
from pathlib import Path

from opt_data.config import AppConfig, IBConfig, TimezoneConfig, PathsConfig, UniverseConfig, FiltersConfig, RateLimitClassConfig, RateLimitsConfig, StorageConfig, CompactionConfig, LoggingConfig, CLIConfig
from opt_data.storage.layout import partition_for, codec_for_date


def _cfg(tmp_path: Path) -> AppConfig:
    return AppConfig(
        ib=IBConfig(host="127.0.0.1", port=7497, client_id=1, market_data_type=2),
        timezone=TimezoneConfig(name="America/New_York", update_time="17:00"),
        paths=PathsConfig(
            raw=tmp_path / "raw",
            clean=tmp_path / "clean",
            state=tmp_path / "state",
            contracts_cache=tmp_path / "state/contracts_cache",
            run_logs=tmp_path / "state/run_logs",
        ),
        universe=UniverseConfig(file=tmp_path / "universe.csv", refresh_days=30),
        filters=FiltersConfig(moneyness_pct=0.3, expiry_types=["monthly", "quarterly"]),
        rate_limits=RateLimitsConfig(
            discovery=RateLimitClassConfig(per_minute=5, burst=5),
            snapshot=RateLimitClassConfig(per_minute=20, burst=10, max_concurrent=4),
            historical=RateLimitClassConfig(per_minute=20, burst=10),
        ),
        storage=StorageConfig(hot_days=14, cold_codec="zstd", cold_codec_level=7, hot_codec="snappy"),
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
    )


def test_partition_path_building(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    d = date(2024, 10, 1)
    part = partition_for(cfg, cfg.paths.raw, d, "AAPL", "CBOE")
    p = part.path()
    assert "date=2024-10-01" in str(p)
    assert "underlying=AAPL" in str(p)
    assert "exchange=CBOE" in str(p)


def test_codec_selection_hot_and_cold(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    today = date(2025, 1, 15)
    hot_date = today - timedelta(days=5)
    cold_date = today - timedelta(days=30)

    codec_hot, opts_hot = codec_for_date(cfg, hot_date, today)
    codec_cold, opts_cold = codec_for_date(cfg, cold_date, today)

    assert codec_hot == "snappy" and opts_hot == {}
    assert codec_cold == "zstd" and "compression_level" in opts_cold

