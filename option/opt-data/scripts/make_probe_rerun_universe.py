#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUMMARY_DIR = Path("state/run_logs/historical_probe_universe")


@dataclass(frozen=True)
class SymbolResult:
    symbol: str
    status: str  # OK / EMPTY / ERR / SKIP
    error_code: int | None
    error_message: str | None


def _infer_status(row: dict[str, Any]) -> str:
    if bool(row.get("skipped")):
        return "SKIP"
    if row.get("error_code") is not None or row.get("error_message"):
        return "ERR"
    bars = int(row.get("bars") or 0)
    first = row.get("first")
    last = row.get("last")
    if bars <= 0 or not first or not last:
        return "EMPTY"
    return "OK"


def _read_results(path: Path) -> tuple[dict[str, Any] | None, list[SymbolResult]]:
    meta: dict[str, Any] | None = None
    results: list[SymbolResult] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict) and "meta" in obj:
                meta = obj.get("meta")
                continue
            if not isinstance(obj, dict) or "symbol" not in obj:
                continue
            sym = str(obj["symbol"]).strip().upper()
            results.append(
                SymbolResult(
                    symbol=sym,
                    status=_infer_status(obj),
                    error_code=int(obj["error_code"]) if obj.get("error_code") is not None else None,
                    error_message=str(obj["error_message"]) if obj.get("error_message") else None,
                )
            )
    return meta, results


def _latest_summaries(*, stage: str, batch_count: int, summary_dir: Path) -> list[Path]:
    # Filename pattern:
    #   summary_quarterly_{stage}_b{idx}of{batch_count}_{runid}.jsonl
    glob_pat = str(summary_dir / f"summary_quarterly_{stage}_b*of{batch_count}_*.jsonl")
    files = [Path(p) for p in glob.glob(glob_pat)]
    tag_re = re.compile(rf"summary_quarterly_{re.escape(stage)}_(b\d+of{batch_count})_")

    by_tag: dict[str, list[Path]] = {}
    for p in files:
        m = tag_re.search(p.name)
        if not m:
            continue
        by_tag.setdefault(m.group(1), []).append(p)

    latest: list[Path] = []
    missing: list[str] = []
    for i in range(batch_count):
        tag = f"b{i}of{batch_count}"
        candidates = sorted(by_tag.get(tag, []), key=lambda x: x.name)
        if not candidates:
            missing.append(tag)
            continue
        latest.append(candidates[-1])

    if missing:
        missing_s = ", ".join(missing)
        raise SystemExit(
            f"Missing summary batches for stage={stage}: {missing_s}\n"
            f"Looked under: {summary_dir}"
        )
    return latest


def _load_universe(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        out: dict[str, str] = {}
        for row in reader:
            sym = (row.get("symbol") or "").strip().upper()
            if not sym:
                continue
            out[sym] = (row.get("conid") or "").strip()
        return out


def _write_universe(path: Path, symbols: list[str], conid_map: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["symbol", "conid"], lineterminator="\n")
        writer.writeheader()
        for sym in symbols:
            writer.writerow({"symbol": sym, "conid": conid_map.get(sym, "")})


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a rerun universe CSV from historical probe summary JSONL files "
            "(e.g., EMPTY/ERR symbols)."
        )
    )
    parser.add_argument(
        "--stage",
        choices=["hours", "minutes"],
        required=True,
        help="Which probe stage to read summaries from.",
    )
    parser.add_argument(
        "--batch-count",
        type=int,
        default=8,
        help="Batch count used in the original run (default: 8).",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=SUMMARY_DIR,
        help="Directory containing summary JSONL files.",
    )
    parser.add_argument(
        "--include",
        action="append",
        choices=["ERR", "EMPTY", "SKIP", "OK"],
        default=["ERR", "EMPTY"],
        help="Statuses to include; can be passed multiple times (default: ERR and EMPTY).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output universe CSV path. Default: config/universe_rerun_{stage}.csv",
    )
    parser.add_argument(
        "--universe",
        type=Path,
        default=Path("config/universe_history_202511.csv"),
        help="Universe CSV to copy conid from (symbol,conid).",
    )
    parser.add_argument(
        "--filter-to-universe",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Only include symbols present in --universe (default: true). "
            "Use --no-filter-to-universe to keep all symbols from summaries."
        ),
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print a suggested rerun command for historical_probe_quarterly_universe_stage.py.",
    )
    args = parser.parse_args()

    latest = _latest_summaries(
        stage=str(args.stage), batch_count=int(args.batch_count), summary_dir=args.summary_dir
    )

    meta_first: dict[str, Any] | None = None
    results_by_symbol: dict[str, SymbolResult] = {}
    counts = Counter()
    error_kinds = Counter()

    for p in latest:
        meta, results = _read_results(p)
        if meta_first is None and meta:
            meta_first = meta
        for r in results:
            # One symbol should appear once per stage+barSize in these summaries.
            # If duplicates exist, keep the "worst" status: ERR > EMPTY > SKIP > OK.
            prev = results_by_symbol.get(r.symbol)
            if prev is not None:
                order = {"ERR": 3, "EMPTY": 2, "SKIP": 1, "OK": 0}
                if order[r.status] <= order[prev.status]:
                    continue
            results_by_symbol[r.symbol] = r

    for r in results_by_symbol.values():
        counts[r.status] += 1
        if r.status == "ERR" and r.error_message:
            kind = r.error_message.split(":", 1)[0].strip()
            error_kinds[kind] += 1

    include = set(args.include)
    selected = sorted([s for s, r in results_by_symbol.items() if r.status in include])

    out_path = args.out or Path(f"config/universe_rerun_{args.stage}.csv")
    conid_map = _load_universe(args.universe)
    if bool(args.filter_to_universe) and conid_map:
        universe_syms = set(conid_map.keys())
        selected = [s for s in selected if s in universe_syms]
    _write_universe(out_path, selected, conid_map)

    print(f"stage={args.stage} batches={args.batch_count} symbols_total={len(results_by_symbol)}")
    print("status_counts:", dict(sorted(counts.items())))
    if error_kinds:
        top = ", ".join([f"{k}={v}" for k, v in error_kinds.most_common(8)])
        print("top_error_kinds:", top)
    print(f"selected={len(selected)} include={sorted(include)} out={out_path}")

    if args.print_command:
        host = meta_first.get("host") if meta_first else None
        port = meta_first.get("port") if meta_first else None
        bar_sizes = meta_first.get("bar_sizes") if meta_first else None
        what_to_show = meta_first.get("what_to_show") if meta_first else None
        duration_minutes = meta_first.get("duration_minutes") if meta_first else None
        duration_hours = meta_first.get("duration_hours") if meta_first else None

        cmd: list[str] = [
            "python",
            "scripts/historical_probe_quarterly_universe_stage.py",
            "--universe",
            str(out_path),
            "--stage",
            str(args.stage),
            "--no-reuse-probe",
            "--no-skip-underlying-close",
            "--write-bars",
            "--no-resume",
        ]
        if bar_sizes:
            for bs in bar_sizes:
                cmd.extend(["--bar-size", str(bs)])
        if what_to_show:
            for w in what_to_show:
                cmd.extend(["--what", str(w)])
        if str(args.stage) == "minutes" and duration_minutes:
            cmd.extend(["--duration-minutes", str(duration_minutes)])
        if str(args.stage) == "hours" and duration_hours:
            cmd.extend(["--duration-hours", str(duration_hours)])
        if host:
            cmd.extend(["--host", str(host)])
        if port:
            cmd.extend(["--port", str(port)])
        cmd.extend(["--client-id", "999"])
        print("suggested_command:")
        print(" ".join(cmd))


if __name__ == "__main__":
    main()
