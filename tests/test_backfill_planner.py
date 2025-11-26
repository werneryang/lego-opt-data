from datetime import date
from pathlib import Path

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
    SnapshotConfig,
    EnrichmentConfig,
    QAConfig,
    ReferenceConfig,
    AcquisitionConfig,
)
from opt_data.pipeline.backfill import BackfillPlanner


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
        reference=ReferenceConfig(corporate_actions=tmp_path / "actions.csv"),
        filters=FiltersConfig(moneyness_pct=0.3, expiry_types=["monthly", "quarterly"], expiry_months_ahead=None),
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
        cli=CLIConfig(
            default_generic_ticks="100",
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
            max_strikes_per_expiry=21,
            fill_missing_greeks_with_zero=False,
            historical_timeout=30.0,
        ),
    )


def test_backfill_planner_creates_queue(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.paths.state.mkdir(parents=True)
    cfg.universe.file.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")

    planner = BackfillPlanner(cfg)
    queue = planner.plan(date(2024, 10, 1))
    assert len(queue) == 2
    path = cfg.paths.state / "backfill_2024-10-01.jsonl"
    assert path.exists()
    saved = path.read_text(encoding="utf-8").strip().splitlines()
    assert saved[0] == '{"symbol": "AAPL", "start_date": "2024-10-01", "underlying_conid": null}'


def test_backfill_planner_filters_symbols(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.paths.state.mkdir(parents=True)
    cfg.universe.file.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")

    planner = BackfillPlanner(cfg)
    queue = planner.plan(date(2024, 10, 1), symbols=["MSFT"])
    assert len(queue) == 1
    task = queue.pop()
    assert task == {"symbol": "MSFT", "start_date": "2024-10-01", "underlying_conid": None}
