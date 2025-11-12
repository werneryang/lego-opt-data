from datetime import date
from pathlib import Path
from typing import Any, List, Dict

import pandas as pd

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
from opt_data.pipeline.backfill import BackfillRunner, BackfillPlanner


def _cfg(tmp_path: Path) -> AppConfig:
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
        reference=ReferenceConfig(corporate_actions=tmp_path / "actions.csv"),
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


class FakeSession:
    def __init__(self) -> None:
        self.connected = False
        self.ib = object()

    def __enter__(self) -> "FakeSession":
        self.connected = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.connected = False

    def ensure_connected(self) -> object:
        self.connected = True
        return self.ib

    def disconnect(self) -> None:  # pragma: no cover - safety net
        self.connected = False


def fake_contract_fetcher(
    session: Any, symbol: str, trade_date: date, underlying_close: float, cfg: AppConfig, **_: Any
) -> List[Dict[str, Any]]:
    return [
        {
            "symbol": symbol,
            "conid": 1001,
            "expiry": "2024-10-18",
            "right": "C",
            "strike": 150.0,
            "multiplier": 100.0,
            "exchange": "SMART",
            "tradingClass": symbol,
            "currency": "USD",
        },
        {
            "symbol": symbol,
            "conid": 1002,
            "expiry": "2024-10-18",
            "right": "P",
            "strike": 150.0,
            "multiplier": 100.0,
            "exchange": "SMART",
            "tradingClass": symbol,
            "currency": "USD",
        },
    ]


def fake_snapshot_fetcher(
    ib: Any, contracts: List[Dict[str, Any]], ticks: str, **kwargs: Any
) -> List[Dict[str, Any]]:
    acquire = kwargs.get("acquire_token")
    rows = []
    for c in contracts:
        if callable(acquire):
            acquire()
        r = dict(c)
        r.update(
            {
                "bid": 1.2,
                "ask": 1.3,
                "last": 1.25,
                "close": 1.22,
                "volume": 10,
                "open_interest": 100,
                "iv": 0.25,
                "delta": 0.5 if c["right"] == "C" else -0.5,
                "gamma": 0.1,
                "theta": -0.05,
                "vega": 0.2,
                "market_data_type": 2,
                "asof": None,
            }
        )
        rows.append(r)
    return rows


def fake_underlying_fetcher(ib: Any, symbol: str, trade_date: date, conid: int | None) -> float:
    return 150.0


def test_backfill_runner_persists_raw_data(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    cfg.paths.state.mkdir(parents=True)
    cfg.paths.raw.mkdir(parents=True)
    cfg.paths.clean.mkdir(parents=True)
    cfg.universe.file.write_text("symbol\nAAPL\n", encoding="utf-8")

    planner = BackfillPlanner(cfg)
    planner.plan(date(2024, 10, 1), symbols=["AAPL"])

    runner = BackfillRunner(
        cfg,
        session_factory=lambda: FakeSession(),
        contract_fetcher=fake_contract_fetcher,
        snapshot_fetcher=fake_snapshot_fetcher,
        underlying_fetcher=fake_underlying_fetcher,
    )

    processed = runner.run(date(2024, 10, 1), symbols=["AAPL"], limit=1)
    assert processed == 1

    raw_files = list(cfg.paths.raw.glob("**/*.parquet"))
    assert raw_files, "expected parquet output"

    df_raw = pd.read_parquet(raw_files[0])
    assert {"bid", "ask", "trade_date", "underlying_close"}.issubset(df_raw.columns)
    trade_dates = pd.to_datetime(df_raw["trade_date"]).dt.date.unique().tolist()
    assert trade_dates == [date(2024, 10, 1)]

    clean_files = list((cfg.paths.clean / "view=clean").glob("**/*.parquet"))
    adjusted_files = list((cfg.paths.clean / "view=adjusted").glob("**/*.parquet"))
    assert clean_files and adjusted_files

    df_clean = pd.read_parquet(clean_files[0])
    assert "mid" in df_clean.columns
    df_adjusted = pd.read_parquet(adjusted_files[0])
    assert "underlying_close_adj" in df_adjusted.columns

    queue_file = cfg.paths.state / "backfill_2024-10-01.jsonl"
    assert queue_file.exists()
    assert queue_file.read_text(encoding="utf-8") == ""


def test_run_range_skips_non_trading(monkeypatch, tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    calls: List[date] = []

    def fake_run(self, dt: date, symbols=None, limit=None, force_refresh=False, **kwargs):  # type: ignore[override]
        calls.append(dt)
        return 1

    monkeypatch.setattr(BackfillRunner, "run", fake_run)

    runner = BackfillRunner(
        cfg,
        session_factory=lambda: FakeSession(),
        contract_fetcher=fake_contract_fetcher,
        snapshot_fetcher=fake_snapshot_fetcher,
        underlying_fetcher=fake_underlying_fetcher,
    )

    total = runner.run_range(date(2024, 10, 4), date(2024, 10, 7))

    # 2024-10-04 is Friday, 05/06 weekend skipped, 07 Monday processed
    assert total == 2
    assert calls == [date(2024, 10, 4), date(2024, 10, 7)]
