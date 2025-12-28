from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from typer.testing import CliRunner

from opt_data.cli import app
from .helpers import build_config


RUNNER = CliRunner()


def test_close_snapshot_uses_last_slot(monkeypatch, tmp_path):
    trade_date = date(2025, 11, 24)
    config = build_config(tmp_path)
    captured: dict[str, object] = {}
    precheck_calls: list[dict[str, object]] = []

    class DummySlot:
        def __init__(self, label: str) -> None:
            self.label = label

    class DummyRunner:
        def __init__(self, cfg, snapshot_grace_seconds=None, session_factory=None, **_) -> None:  # type: ignore[no-untyped-def]
            captured["cfg"] = cfg
            captured["grace"] = snapshot_grace_seconds
            captured["session_factory"] = session_factory

        def available_slots(self, td):  # type: ignore[no-untyped-def]
            captured["requested_date"] = td
            return [DummySlot("15:30"), DummySlot("16:00")]

        def run(
            self,
            trade_date,
            slot,
            symbols,
            *,
            universe_path=None,
            ingest_run_type="intraday",
            view="intraday",
            force_refresh=False,
            progress=None,
        ):  # type: ignore[no-untyped-def]
            captured["run"] = {
                "trade_date": trade_date,
                "slot_label": slot.label,
                "symbols": symbols,
                "universe_path": universe_path,
                "ingest_run_type": ingest_run_type,
                "view": view,
            }
            if progress:
                progress("AAPL", "start", {"rows": 1})
            return SimpleNamespace(
                ingest_id="ingest-123",
                rows_written=42,
                raw_paths=[tmp_path / "raw.parquet"],
                clean_paths=[tmp_path / "clean.parquet"],
                errors=[],
            )

    monkeypatch.setattr("opt_data.cli.load_config", lambda path=None: config)
    monkeypatch.setattr("opt_data.cli.SnapshotRunner", DummyRunner)

    def fake_precheck(
        cfg, td, symbols, entries_by_symbol, *, universe_path=None, build_missing_cache, prefix
    ):
        precheck_calls.append(
            {
                "cfg": cfg,
                "td": td,
                "symbols": symbols,
                "entries": entries_by_symbol,
                "universe_path": universe_path,
                "build": build_missing_cache,
                "prefix": prefix,
            }
        )
        return None

    monkeypatch.setattr("opt_data.cli._precheck_contract_caches", fake_precheck)

    result = RUNNER.invoke(
        app,
        [
            "close-snapshot",
            "--date",
            trade_date.isoformat(),
            "--symbols",
            "AAPL,MSFT",
            "--config",
            "ignored",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "slot=16:00" in result.output
    assert "[close-snapshot:start] slot=16:00 AAPL rows=1" in result.output
    assert captured["run"]["slot_label"] == "16:00"
    assert captured["run"]["symbols"] == ["AAPL", "MSFT"]
    assert precheck_calls and precheck_calls[0]["symbols"] == ["AAPL", "MSFT"]
    assert precheck_calls[0]["prefix"] == "close-snapshot"
    assert captured["session_factory"] is not None
