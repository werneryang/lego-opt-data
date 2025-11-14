from datetime import date
from pathlib import Path

import sys
import types

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
from opt_data.ib.discovery import discover_contracts_for_symbol


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
    def __init__(self, ib: object) -> None:
        self._ib = ib

    def ensure_connected(self) -> object:
        return self._ib

    def __enter__(self):  # pragma: no cover - unused
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - unused
        return False


class FakeContract:
    def __init__(
        self, con_id: int, symbol: str, expiry: str, right: str, strike: float, exchange: str
    ) -> None:
        self.conId = con_id
        self.symbol = symbol
        self.lastTradeDateOrContractMonth = expiry
        self.right = right
        self.strike = strike
        self.multiplier = "100"
        self.exchange = exchange
        self.tradingClass = symbol
        self.currency = "USD"



class FakeParam:
    def __init__(self) -> None:
        self.exchange = "SMART"
        self.tradingClass = "AAPL"
        self.multiplier = "100"
        self.strikes = {120.0, 150.0}
        self.expirations = {"20241018"}


class FakeIB:
    def __init__(self) -> None:
        self.secdef_calls = 0
        self.qualify_calls = 0
        self._con_seq = 1000

    def reqSecDefOptParams(self, *args, **kwargs):
        self.secdef_calls += 1
        return [FakeParam()]

    def qualifyContracts(self, *contracts):
        self.qualify_calls += 1
        out = []
        for option in contracts:
            self._con_seq += 1
            out.append(
                FakeContract(
                    con_id=self._con_seq,
                    symbol=option.symbol,
                    expiry=option.lastTradeDateOrContractMonth,
                    right=option.right,
                    strike=option.strike,
                    exchange=option.exchange,
                )
            )
        return out


def test_discover_contracts_for_symbol_caches(monkeypatch, tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    session = FakeSession(FakeIB())

    class FakeOption:
        def __init__(
            self,
            symbol,
            lastTradeDateOrContractMonth,
            strike,
            right,
            exchange,
            currency,
            tradingClass,
        ):
            self.symbol = symbol
            self.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
            self.strike = strike
            self.right = right
            self.exchange = exchange
            self.currency = currency
            self.tradingClass = tradingClass

    monkeypatch.setitem(sys.modules, "ib_insync", types.SimpleNamespace(Option=FakeOption))

    trade_date = date(2024, 10, 1)
    results = discover_contracts_for_symbol(
        session,
        symbol="AAPL",
        trade_date=trade_date,
        underlying_close=150.0,
        cfg=cfg,
    )

    assert len(results) == 4  # two strikes x two rights
    cache_file = cfg.paths.contracts_cache / "AAPL_2024-10-01.json"
    assert cache_file.exists()

    # Second call should hit cache (no additional secdef calls)
    ib = session.ensure_connected()
    before_calls = ib.secdef_calls
    cached = discover_contracts_for_symbol(
        session,
        symbol="AAPL",
        trade_date=trade_date,
        underlying_close=150.0,
        cfg=cfg,
    )
    assert cached == results
    assert ib.secdef_calls == before_calls
