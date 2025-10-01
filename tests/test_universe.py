from pathlib import Path

from opt_data.universe import load_universe, UniverseEntry


def test_load_universe_parses_symbols(tmp_path: Path) -> None:
    file = tmp_path / "universe.csv"
    file.write_text("symbol,conid\nAAPL,111\nmsft,222\n,\n", encoding="utf-8")

    entries = load_universe(file)
    assert entries == [
        UniverseEntry(symbol="AAPL", conid=111),
        UniverseEntry(symbol="MSFT", conid=222),
    ]


def test_load_universe_missing_file_returns_empty(tmp_path: Path) -> None:
    file = tmp_path / "missing.csv"
    assert load_universe(file) == []
