#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _iter_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(row for row in fh if not row.startswith("#"))
        return list(reader)


def _convert_symbols(rows: list[dict[str, str]]) -> list[str]:
    seen: set[str] = set()
    symbols: list[str] = []
    for row in rows:
        symbol = (row.get("symbol") or "").strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert underlyings CSV (with symbol column) to config/universe.csv format."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data_test/underlyings_202511.csv"),
        help="Input CSV path (must include a 'symbol' column)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("config/universe_history_202511.csv"),
        help="Output CSV path in universe format (symbol,conid)",
    )
    args = parser.parse_args()

    rows = _iter_rows(args.input)
    symbols = _convert_symbols(rows)
    if not symbols:
        raise SystemExit(f"No symbols found in {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["symbol", "conid"], lineterminator="\n")
        writer.writeheader()
        for symbol in symbols:
            writer.writerow({"symbol": symbol, "conid": ""})

    print(f"Wrote {len(symbols)} symbols to {args.output}")


if __name__ == "__main__":
    main()
