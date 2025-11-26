from __future__ import annotations

from pathlib import Path

from datetime import date
import pytest

from opt_data.cli import _precheck_contract_caches
from opt_data.universe import UniverseEntry
from opt_data.ib.discovery import cache_path


def _dummy_cfg(tmp_path: Path):
    class Dummy:
        pass

    cfg = Dummy()
    cfg.ib = Dummy()
    cfg.ib.host = "127.0.0.1"
    cfg.ib.port = 7496
    cfg.ib.client_id = 101
    cfg.ib.market_data_type = 1
    cfg.paths = Dummy()
    cfg.paths.contracts_cache = tmp_path / "state/contracts_cache"
    cfg.paths.contracts_cache.mkdir(parents=True, exist_ok=True)
    cfg.universe = Dummy()
    cfg.universe.file = tmp_path / "config/universe.csv"
    cfg.acquisition = Dummy()
    cfg.acquisition.max_strikes_per_expiry = 3
    cfg.paths.state = tmp_path / "state"
    cfg.paths.state.mkdir(parents=True, exist_ok=True)
    return cfg  # type: ignore[return-value]


def test_update_universe_file_on_resolve(monkeypatch, tmp_path):
    cfg = _dummy_cfg(tmp_path)
    cfg.universe.file.parent.mkdir(parents=True, exist_ok=True)
    cfg.universe.file.write_text("symbol,conid\nAAPL,\n", encoding="utf-8")

    # stub session/discovery to avoid IB calls
    class DummyIB:
        def qualifyContracts(self, contract):
            class C:
                conId = 999

            return [C()]

    class DummySession:
        def __init__(self):
            self.ib = DummyIB()

        def ensure_connected(self):
            return self.ib

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("opt_data.cli.IBSession", lambda **_: DummySession())
    monkeypatch.setattr("opt_data.cli.fetch_underlying_close", lambda *_, **__: 100.0)

    def fake_discover(session, sym, td, ref_price, cfg, **kwargs):
        cache_file = cache_path(Path(cfg.paths.contracts_cache), sym, td.isoformat())
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text('[{"conid":1}]', encoding="utf-8")

    monkeypatch.setattr("opt_data.cli.discover_contracts_for_symbol", fake_discover)

    entries = {"AAPL": UniverseEntry(symbol="AAPL", conid=None)}

    _precheck_contract_caches(
        cfg,
        trade_date=date(2025, 11, 24),
        symbols_for_run=["AAPL"],
        entries_by_symbol=entries,
        build_missing_cache=True,
        prefix="test",
    )

    updated = cfg.universe.file.read_text(encoding="utf-8")
    assert "AAPL,999" in updated


def test_conid_persist_even_on_failure(monkeypatch, tmp_path):
    cfg = _dummy_cfg(tmp_path)
    cfg.universe.file.parent.mkdir(parents=True, exist_ok=True)
    cfg.universe.file.write_text("symbol,conid\nAAPL,\n", encoding="utf-8")

    class DummyIB:
        def qualifyContracts(self, contract):
            class C:
                conId = 888

            return [C()]

    class DummySession:
        def __init__(self):
            self.ib = DummyIB()

        def ensure_connected(self):
            return self.ib

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("opt_data.cli.IBSession", lambda **_: DummySession())
    monkeypatch.setattr("opt_data.cli.fetch_underlying_close", lambda *_, **__: 100.0)

    def fake_discover(session, sym, td, ref_price, cfg, **kwargs):
        # Simulate failure to create cache to force missing/invalid exit
        raise RuntimeError("discovery failed")

    monkeypatch.setattr("opt_data.cli.discover_contracts_for_symbol", fake_discover)

    entries = {"AAPL": UniverseEntry(symbol="AAPL", conid=None)}

    import typer

    with pytest.raises(typer.Exit):
        _precheck_contract_caches(
            cfg,
            trade_date=date(2025, 11, 24),
            symbols_for_run=["AAPL"],
            entries_by_symbol=entries,
            build_missing_cache=True,
            prefix="test",
        )

    updated = cfg.universe.file.read_text(encoding="utf-8")
    assert "AAPL,888" in updated
