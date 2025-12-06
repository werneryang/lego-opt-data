from __future__ import annotations

from pathlib import Path

from opt_data.config import (
    AcquisitionConfig,
    AppConfig,
    CLIConfig,
    SnapshotConfig,
    EnrichmentConfig,
    QAConfig,
    CompactionConfig,
    FiltersConfig,
    IBConfig,
    LoggingConfig,
    PathsConfig,
    RateLimitClassConfig,
    RateLimitsConfig,
    ReferenceConfig,
    RollupConfig,
    StorageConfig,
    TimezoneConfig,
    UniverseConfig,
    ObservabilityConfig,
)


def build_config(tmp_path: Path) -> AppConfig:
    raw_root = tmp_path / "data/raw/ib/chain"
    clean_root = tmp_path / "data/clean/ib/chain"
    state_root = tmp_path / "state"

    universe_file = tmp_path / "config/universe.csv"
    universe_file.parent.mkdir(parents=True, exist_ok=True)
    universe_file.write_text("symbol,conid\nAAPL,123456\n", encoding="utf-8")

    return AppConfig(
        ib=IBConfig(host="127.0.0.1", port=7497, client_id=101, market_data_type=1),
        timezone=TimezoneConfig(name="America/New_York", update_time="17:00"),
        paths=PathsConfig(
            raw=raw_root,
            clean=clean_root,
            state=state_root,
            contracts_cache=state_root / "contracts_cache",
            run_logs=state_root / "run_logs",
        ),
    universe=UniverseConfig(file=universe_file, refresh_days=30, intraday_file=None, close_file=None),
    reference=ReferenceConfig(corporate_actions=tmp_path / "config/corporate_actions.csv"),
    filters=FiltersConfig(
        moneyness_pct=0.30, expiry_types=["monthly", "quarterly"], expiry_months_ahead=12
    ),
        rate_limits=RateLimitsConfig(
            discovery=RateLimitClassConfig(per_minute=1000, burst=1000),
            snapshot=RateLimitClassConfig(per_minute=1000, burst=1000, max_concurrent=10),
            historical=RateLimitClassConfig(per_minute=1000, burst=1000),
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
        observability=ObservabilityConfig(metrics_db_path=tmp_path / "data/metrics.db"),
        cli=CLIConfig(
            default_generic_ticks="100,101,104,105,106,165,221,225,233,293,294,295",
            snapshot_grace_seconds=120,
            rollup_close_slot=13,
            rollup_fallback_slot=12,
        ),
        snapshot=SnapshotConfig(
            exchange="SMART",
            fallback_exchanges=["CBOE", "CBOEOPT"],
            generic_ticks="100,101,104,105,106,165,221,225,233,293,294,295",
            strikes_per_side=3,
            subscription_timeout=12.0,
            subscription_poll_interval=0.25,
            require_greeks=True,
        ),
        enrichment=EnrichmentConfig(
            fields=["open_interest"],
            oi_duration="7 D",
            oi_use_rth=False,
        ),
        qa=QAConfig(
            slot_coverage_threshold=0.9,
            delayed_ratio_threshold=0.1,
            rollup_fallback_threshold=0.05,
            oi_enrichment_threshold=0.95,
        ),
        acquisition=AcquisitionConfig(
            mode="snapshot",
            duration="1 D",
            bar_size="1 day",
            what_to_show="TRADES",
            use_rth=True,
            max_strikes_per_expiry=4,
            fill_missing_greeks_with_zero=False,
            historical_timeout=30.0,
        ),
        rollup=RollupConfig(),
    )
