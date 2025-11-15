#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set

import pandas as pd

from opt_data.config import load_config
from opt_data.pipeline.snapshot import SnapshotRunner


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - arg validation
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc


def _parse_symbols(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {token.strip().upper() for token in value.split(",") if token.strip()}


def _load_json_lines(path: Path, *, symbols: set[str] | None = None) -> list[dict]:
    if not path.exists():
        return []
    results: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            symbol = (payload.get("symbol") or payload.get("underlying") or "").strip().upper()
            if symbols and symbol and symbol not in symbols:
                continue
            results.append(payload)
    return results


@dataclass
class SnapshotLogSummary:
    slot: str
    symbol: str
    statuses: list[str]
    row_count: int | None
    reference_price: float | None
    path: Path


def _summarize_snapshot_logs(
    snapshot_dir: Path, trade_date: date, symbols: set[str] | None = None
) -> list[SnapshotLogSummary]:
    pattern = f"snapshot_{trade_date.isoformat()}_*.log"
    summaries: list[SnapshotLogSummary] = []
    for log_path in sorted(snapshot_dir.glob(pattern)):
        entries = _load_json_lines(log_path, symbols=symbols)
        if not entries:
            continue
        slot = str(entries[0].get("slot", "unknown"))
        symbol = str(entries[0].get("symbol", "")).upper()
        statuses = [str(entry.get("status", "")).lower() for entry in entries]
        row_count = None
        reference_price = None
        for entry in reversed(entries):
            if row_count is None and entry.get("status") == "rows":
                row_count = int(entry.get("count", 0))
            if reference_price is None and entry.get("status") == "reference_price":
                reference_price = float(entry.get("price", 0.0))
        summaries.append(
            SnapshotLogSummary(
                slot=slot,
                symbol=symbol,
                statuses=statuses,
                row_count=row_count,
                reference_price=reference_price,
                path=log_path,
            )
        )
    return summaries


@dataclass
class PartitionSummary:
    symbol: str
    exchange: str
    path: Path
    rows: int
    slots: list[int]
    slot_times: list[str]
    slot_counts: Dict[int, int]
    duplicates: int


@dataclass
class DailySummary:
    symbol: str
    exchange: str
    path: Path
    rows: int
    strategies: Dict[str, int]
    source_slots: Dict[int, int]
    oi_present: int
    oi_missing_flag: int


def _summarize_partitions(
    root: Path, trade_date: date, symbols: set[str] | None = None
) -> list[PartitionSummary]:
    summaries: list[PartitionSummary] = []
    date_dir = root / f"view=intraday/date={trade_date.isoformat()}"
    if not date_dir.exists():
        return summaries

    for underlying_dir in sorted(date_dir.glob("underlying=*")):
        symbol = underlying_dir.name.split("=", 1)[1].upper()
        if symbols and symbol not in symbols:
            continue
        for exchange_dir in sorted(underlying_dir.glob("exchange=*")):
            exchange = exchange_dir.name.split("=", 1)[1].upper()
            parquet_path = exchange_dir / "part-000.parquet"
            if not parquet_path.exists():
                continue
            df = pd.read_parquet(
                parquet_path,
                columns=["slot_30m", "sample_time_et", "conid"],
            )
            if df.empty:
                rows = 0
                slots: list[int] = []
                slot_times: list[str] = []
                slot_counts: dict[int, int] = {}
                duplicates = 0
            else:
                df = df.dropna(subset=["slot_30m"])
                rows = len(df)
                df["slot_30m"] = df["slot_30m"].astype("int64")
                grouped = (
                    df.groupby("slot_30m")["sample_time_et"]
                    .min()
                    .reset_index()
                    .sort_values("slot_30m")
                )
                slots = [int(row.slot_30m) for row in grouped.itertuples()]
                slot_times = [str(row.sample_time_et) for row in grouped.itertuples()]
                slot_counts = (
                    df.groupby("slot_30m")["conid"].count().astype(int).to_dict()
                    if "conid" in df.columns
                    else {}
                )
                dedup = df.drop_duplicates(subset=["slot_30m", "conid"], keep="last")
                duplicates = max(rows - len(dedup), 0)
            summaries.append(
                PartitionSummary(
                    symbol=symbol,
                    exchange=exchange,
                    path=parquet_path,
                    rows=rows,
                    slots=slots,
                    slot_times=slot_times,
                    slot_counts=slot_counts,
                    duplicates=duplicates,
                )
            )
    return summaries


def _summarize_daily_view(
    root: Path, trade_date: date, symbols: set[str] | None = None
) -> list[DailySummary]:
    summaries: list[DailySummary] = []
    date_dir = root / f"date={trade_date.isoformat()}"
    if not date_dir.exists():
        return summaries
    for underlying_dir in sorted(date_dir.glob("underlying=*")):
        symbol = underlying_dir.name.split("=", 1)[1].upper()
        if symbols and symbol not in symbols:
            continue
        for exchange_dir in sorted(underlying_dir.glob("exchange=*")):
            exchange = exchange_dir.name.split("=", 1)[1].upper()
            parquet_path = exchange_dir / "part-000.parquet"
            if not parquet_path.exists():
                continue
            df = pd.read_parquet(parquet_path)
            if df.empty:
                summaries.append(
                    DailySummary(
                        symbol=symbol,
                        exchange=exchange,
                        path=parquet_path,
                        rows=0,
                        strategies={},
                        source_slots={},
                        oi_present=0,
                        oi_missing_flag=0,
                    )
                )
                continue
            rows = len(df)
            strategies = (
                df.get("rollup_strategy", pd.Series(dtype="str"))
                .astype(str)
                .str.lower()
                .value_counts()
                .to_dict()
                if "rollup_strategy" in df.columns
                else {}
            )
            source_slots = (
                df.get("rollup_source_slot", pd.Series(dtype="float"))
                .dropna()
                .astype("int64")
                .value_counts()
                .sort_index()
                .to_dict()
                if "rollup_source_slot" in df.columns
                else {}
            )
            oi_series = df.get("open_interest", pd.Series(dtype="float"))
            oi_present = int((~oi_series.isna()).sum())
            flags_series = df.get("data_quality_flag")
            if flags_series is not None:
                normalized = flags_series.apply(_normalize_flags)
                oi_missing_flag = int(
                    normalized.apply(lambda flg: "missing_oi" in flg if isinstance(flg, list) else False).sum()
                )
            else:
                oi_missing_flag = 0
            summaries.append(
                DailySummary(
                    symbol=symbol,
                    exchange=exchange,
                    path=parquet_path,
                    rows=rows,
                    strategies=strategies,
                    source_slots=source_slots,
                    oi_present=oi_present,
                    oi_missing_flag=oi_missing_flag,
                )
            )
    return summaries


def _print_header(trade_date: date, symbols: set[str] | None, interval: int) -> None:
    print(f"=== Schedule run inspection for {trade_date.isoformat()} ===")
    if symbols:
        print(f"Symbols filter: {', '.join(sorted(symbols))}")
    else:
        print("Symbols filter: ALL")
    print(f"Configured snapshot interval: {interval} minutes")


def _print_expected_slots(slots: Sequence) -> None:
    labels = [slot.label for slot in slots]
    print(f"Expected snapshot slots: {len(labels)} slots")
    if labels:
        print("  " + ", ".join(labels))


def _print_log_summary(summaries: Sequence[SnapshotLogSummary]) -> None:
    print("\n-- Snapshot logs --")
    if not summaries:
        print("  No snapshot logs found for the specified date/symbols.")
        return
    for summary in summaries:
        status_chain = " -> ".join(summary.statuses)
        extra: list[str] = []
        if summary.row_count is not None:
            extra.append(f"rows={summary.row_count}")
        if summary.reference_price is not None:
            extra.append(f"px={summary.reference_price}")
        info = f"slot={summary.slot} symbol={summary.symbol}"
        if extra:
            info += " (" + ", ".join(extra) + ")"
        print(f"  {info}")
        print(f"    statuses: {status_chain}")
        print(f"    file: {summary.path}")


def _print_partition_summary(
    partitions: Sequence[PartitionSummary], slot_label_lookup: Dict[int, str]
) -> None:
    print("\n-- Intraday partitions (raw) --")
    if not partitions:
        print("  No intraday parquet partitions were found for the date/symbol filter.")
        return
    for part in partitions:
        slot_details = []
        for slot in part.slots:
            label = slot_label_lookup.get(slot, f"idx={slot}")
            count = part.slot_counts.get(slot, 0)
            slot_details.append(f"{label}:{count}")
        slot_info = ", ".join(slot_details) or "none"
        time_info = ", ".join(part.slot_times) or "n/a"
        print(
            f"  symbol={part.symbol} exchange={part.exchange} rows={part.rows} "
            f"slots=[{slot_info}]"
        )
        print(f"    first sample per slot: {time_info}")
        print(f"    file: {part.path}")
        if part.duplicates:
            print(f"    duplicates detected: {part.duplicates} rows with same slot+conid")


def _print_errors(errors: Sequence[dict], limit: int) -> None:
    print("\n-- Errors --")
    if not errors:
        print("  No errors recorded.")
        return
    print(f"  showing up to {limit} error entries (total={len(errors)})")
    for payload in errors[:limit]:
        serialized = json.dumps(payload, ensure_ascii=False)
        print(f"    {serialized}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect artifacts produced by `python -m opt_data.cli schedule`."
    )
    parser.add_argument("--date", required=True, type=_parse_date, help="Trade date YYYY-MM-DD")
    parser.add_argument("--config", default=None, help="Path to config TOML (defaults to project)")
    parser.add_argument(
        "--symbols",
        default=None,
        help="Comma separated symbol filter (default: ALL)",
    )
    parser.add_argument(
        "--snapshot-interval-minutes",
        type=int,
        default=30,
        help="Snapshot cadence used when scheduling (minutes).",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=5,
        help="Maximum number of error entries to display.",
    )
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if args.snapshot_interval_minutes <= 0:
        parser.error("--snapshot-interval-minutes must be positive")

    cfg = load_config(Path(args.config) if args.config else None)
    snapshot_runner = SnapshotRunner(cfg, slot_minutes=args.snapshot_interval_minutes)
    expected_slots = snapshot_runner.available_slots(args.date)
    _print_header(args.date, symbols, args.snapshot_interval_minutes)
    _print_expected_slots(expected_slots)

    snapshot_dir = Path(cfg.paths.run_logs) / "snapshot"
    summaries = _summarize_snapshot_logs(snapshot_dir, args.date, symbols)
    _print_log_summary(summaries)

    index_to_label = {slot.index: slot.label for slot in expected_slots}
    executed = {summary.slot for summary in summaries}
    missing = [slot.label for slot in expected_slots if slot.label not in executed]
    if missing:
        print("\nMissing snapshot logs for slots:")
        print("  " + ", ".join(missing))

    raw_root = Path(cfg.paths.raw)
    raw_partitions = _summarize_partitions(raw_root, args.date, symbols)
    _print_partition_summary(raw_partitions, index_to_label)

    _print_slot_analysis(expected_slots, summaries, raw_partitions)

    error_path = Path(cfg.paths.run_logs) / "errors" / f"errors_{args.date:%Y%m%d}.log"
    errors = _load_json_lines(error_path, symbols=symbols)
    _print_errors(errors, args.max_errors)

    daily_clean_root = Path(cfg.paths.clean) / "view=daily_clean"
    daily_adjusted_root = Path(cfg.paths.clean) / "view=daily_adjusted"
    daily_clean = _summarize_daily_view(daily_clean_root, args.date, symbols)
    daily_adjusted = _summarize_daily_view(daily_adjusted_root, args.date, symbols)
    _print_daily_summary("Daily clean", daily_clean, index_to_label)
    _print_daily_summary("Daily adjusted", daily_adjusted, index_to_label)
    _print_enrichment_stats(daily_clean)


def _print_slot_analysis(
    expected_slots: Sequence, log_summaries: Sequence[SnapshotLogSummary], partitions: Sequence[PartitionSummary]
) -> None:
    expected_labels = [slot.label for slot in expected_slots]
    label_count = len(expected_labels) or 1
    log_labels: Set[str] = {summary.slot for summary in log_summaries}
    stored_indexes: Set[int] = {slot for part in partitions for slot in part.slots}
    index_to_label = {slot.index: slot.label for slot in expected_slots}
    stored_labels = {index_to_label.get(idx, f"idx={idx}") for idx in stored_indexes}

    missing_storage = [label for label in expected_labels if label not in stored_labels]
    orphaned_storage = sorted(stored_labels - set(expected_labels))

    print("\n-- Slot coverage --")
    print(f"  logged slots: {len(log_labels)}/{label_count}")
    print(f"  stored slots: {len(stored_labels)}/{label_count}")
    if missing_storage:
        print("  slots missing in storage: " + ", ".join(missing_storage))
    if orphaned_storage:
        print("  slots stored but unexpected: " + ", ".join(orphaned_storage))
    if partitions:
        total_rows = sum(part.rows for part in partitions)
        duplicates = sum(part.duplicates for part in partitions)
        print(f"  total rows stored: {total_rows}")
        if duplicates:
            print(f"  duplicates detected: {duplicates} rows (slot+conid)")
    else:
        print("  no stored data to analyze.")


def _print_daily_summary(label: str, summaries: Sequence[DailySummary], slot_label_lookup: Dict[int, str]) -> None:
    print(f"\n-- {label} --")
    if not summaries:
        print("  No data found.")
        return
    for summary in summaries:
        slot_info = ", ".join(
            f"{slot_label_lookup.get(idx, f'idx={idx}')}:{count}"
            for idx, count in summary.source_slots.items()
        ) or "none"
        strategy_info = ", ".join(f"{name}:{count}" for name, count in summary.strategies.items()) or "n/a"
        print(
            f"  symbol={summary.symbol} exchange={summary.exchange} rows={summary.rows} "
            f"source_slots=[{slot_info}] strategies=[{strategy_info}]"
        )
        print(f"    file: {summary.path}")


def _print_enrichment_stats(summaries: Sequence[DailySummary]) -> None:
    print("\n-- Enrichment (open_interest) --")
    if not summaries:
        print("  No daily clean data to inspect.")
        return
    total_rows = sum(summary.rows for summary in summaries)
    oi_present = sum(summary.oi_present for summary in summaries)
    missing_flag = sum(summary.oi_missing_flag for summary in summaries)
    ratio = oi_present / total_rows if total_rows else 0.0
    print(f"  rows={total_rows} oi_present={oi_present} ratio={ratio:.3f} missing_flag={missing_flag}")


def _normalize_flags(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if value is None:
        return []
    if isinstance(value, (tuple, set)):
        return [str(v) for v in value]
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        try:
            return [str(v) for v in list(value)]
        except TypeError:
            pass
    try:
        if pd.isna(value):
            return []
    except Exception:
        pass
    return [str(value)]


if __name__ == "__main__":
    main()
