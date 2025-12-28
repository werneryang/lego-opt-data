from pathlib import Path

import pytest

from opt_data import DataCatalog


def test_register_and_resolve(tmp_path: Path) -> None:
    root = tmp_path
    catalog = DataCatalog(root=root)

    stored_path = catalog.register("chains", "chains/2024-01.csv")

    assert stored_path == root / "chains/2024-01.csv"
    assert catalog.resolve("chains") == stored_path


def test_register_many(tmp_path: Path) -> None:
    root = tmp_path
    catalog = DataCatalog(root=root)

    catalog.register_many(
        [
            ("chains", "chains.csv"),
            ("greeks", "metrics/greeks.parquet"),
        ]
    )

    assert catalog.resolve("chains") == root / "chains.csv"
    assert catalog.resolve("greeks") == root / "metrics/greeks.parquet"


def test_resolve_missing_key(tmp_path: Path) -> None:
    catalog = DataCatalog(root=tmp_path)

    with pytest.raises(KeyError):
        catalog.resolve("missing")


def test_rejects_paths_outside_root(tmp_path: Path) -> None:
    catalog = DataCatalog(root=tmp_path)

    with pytest.raises(ValueError):
        catalog.register("unsafe", "../outside.csv")
