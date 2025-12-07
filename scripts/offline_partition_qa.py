from __future__ import annotations

"""
Offline QA for close vs intraday partitions.

Checks:
- Primary key duplicates
- Missing required columns
- Row alignment between close (or daily_clean fallback) and intraday
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence
import warnings

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opt_data.config import load_config  # noqa: E402

INTRADAY_PK = ["trade_date", "sample_time", "conid"]
CLOSE_PK = ["trade_date", "conid"]

INTRADAY_REQUIRED = {
    "trade_date",
    "sample_time",
    "slot_30m",
    "underlying",
    "conid",
    "symbol",
    "expiry",
    "right",
    "strike",
    "multiplier",
    "exchange",
    "tradingClass",
    "bid",
    "ask",
    "volume",
    "iv",
    "delta",
    "gamma",
    "theta",
    "vega",
    "market_data_type",
    "asof_ts",
    "ingest_id",
    "ingest_run_type",
    "source",
}

CLOSE_REQUIRED = {
    "trade_date",
    "underlying",
    "conid",
    "symbol",
    "expiry",
    "right",
    "strike",
    "multiplier",
    "exchange",
    "tradingClass",
    "bid",
    "ask",
    "volume",
    "iv",
    "delta",
    "gamma",
    "theta",
    "vega",
    "market_data_type",
    "asof_ts",
    "underlying_close",
    "rollup_strategy",
    "rollup_source_slot",
    "rollup_source_time",
    "ingest_id",
    "ingest_run_type",
    "source",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline QA for close/intraday partitions")
    parser.add_argument(
        "--config",
        default="config/opt-data.toml",
        help="Config file (default: config/opt-data.toml)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write QA report (defaults to <clean_path>/reports/offline_qa)",
    )
    parser.add_argument(
        "--close-view",
        default=None,
        help="Override close view path (defaults to view=close, falling back to view=daily_clean)",
    )
    return parser.parse_args()


def list_trade_dates(view_root: Path) -> list[date]:
    if not view_root.exists():
        return []
    dates: list[date] = []
    for path in view_root.glob("date=*"):
        try:
            d = date.fromisoformat(path.name.split("=", 1)[1])
        except ValueError:
            continue
        dates.append(d)
    return sorted(dates)


def read_parquet_tree(root: Path) -> pd.DataFrame | None:
    if not root.exists():
        return None
    frames: list[pd.DataFrame] = []
    for path in sorted(root.rglob("*.parquet")):
        try:
            df = pd.read_parquet(path)
        except Exception:
            continue
        if df is not None:
            frames.append(df)
    frames = [
        f for f in frames if not f.empty and not f.isna().all(axis=None)
    ]
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        return frames[0]
    all_columns = sorted({col for frame in frames for col in frame.columns})
    normalized = [frame.reindex(columns=all_columns) for frame in frames]
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=(
                "The behavior of DataFrame concatenation with empty or all-NA entries "
                "is deprecated"
            ),
            category=FutureWarning,
        )
        return pd.concat(normalized, ignore_index=True, sort=False)


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.date
    if "sample_time" in df.columns:
        df["sample_time"] = pd.to_datetime(df["sample_time"], errors="coerce")
    if "underlying" in df.columns:
        df["underlying"] = df["underlying"].astype(str).str.upper()
    return df


def check_view(df: pd.DataFrame | None, pk_cols: Sequence[str], required_cols: set[str]) -> dict:
    if df is None:
        return {"status": "missing"}
    df = normalize_frame(df)
    row_count = len(df)
    missing_cols = sorted(required_cols - set(df.columns))

    pk_nulls: dict[str, int | None] = {}
    for col in pk_cols:
        pk_nulls[col] = int(df[col].isna().sum()) if col in df.columns else None

    pk_duplicates = None
    duplicate_examples: list[dict] = []
    if all(col in df.columns for col in pk_cols):
        dup_mask = df.duplicated(subset=pk_cols, keep=False)
        pk_duplicates = int(dup_mask.sum())
        if pk_duplicates:
            duplicate_examples = (
                df.loc[dup_mask, pk_cols].drop_duplicates().head(5).to_dict("records")
            )

    return {
        "status": "ok" if df is not None else "missing",
        "rows": row_count,
        "missing_columns": missing_cols,
        "pk_nulls": pk_nulls,
        "pk_duplicates": pk_duplicates,
        "duplicate_examples": duplicate_examples,
    }


def latest_intraday_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "sample_time" in df.columns:
        ordered = df.sort_values("sample_time")
    else:
        ordered = df
    return ordered.drop_duplicates(subset=["conid"], keep="last")


def compute_alignment(
    intraday_df: pd.DataFrame | None, close_df: pd.DataFrame | None
) -> dict:
    if intraday_df is None or intraday_df.empty:
        return {"status": "skipped", "reason": "intraday missing or empty"}
    if close_df is None or close_df.empty:
        return {"status": "skipped", "reason": "close missing or empty"}
    if "conid" not in intraday_df.columns or "conid" not in close_df.columns:
        return {"status": "skipped", "reason": "conid column missing"}
    if "underlying" not in intraday_df.columns or "underlying" not in close_df.columns:
        return {"status": "skipped", "reason": "underlying column missing"}

    intraday_latest = latest_intraday_rows(intraday_df)
    close_unique = close_df.drop_duplicates(subset=["conid"], keep="last")

    intra_conids = set(intraday_latest["conid"].tolist())
    close_conids = set(close_unique["conid"].tolist())

    missing = sorted(intra_conids - close_conids)
    extra = sorted(close_conids - intra_conids)

    intra_counts = (
        intraday_latest.groupby("underlying")["conid"].nunique().rename("intraday")
    )
    close_counts = close_unique.groupby("underlying")["conid"].nunique().rename("close")
    combined = (
        pd.concat([intra_counts, close_counts], axis=1)
        .fillna(0)
        .astype(int)
        .sort_index()
    )
    mismatches = []
    for idx, row in combined.iterrows():
        if row["intraday"] != row["close"]:
            mismatches.append(
                {"underlying": idx, "intraday": int(row["intraday"]), "close": int(row["close"])}
            )

    return {
        "status": "ok",
        "intraday_conids": len(intra_conids),
        "close_conids": len(close_conids),
        "missing_in_close": len(missing),
        "extra_in_close": len(extra),
        "missing_examples": missing[:10],
        "extra_examples": extra[:10],
        "underlying_mismatches": mismatches,
    }


def render_markdown(report: dict) -> str:
    lines = []
    lines.append("# Offline QA Report (close vs intraday)")
    lines.append("")
    lines.append(f"- Generated at: {report['generated_at']}")
    lines.append(f"- Config: {report['config_path']}")
    lines.append(f"- Intraday view: {report['intraday_root']}")
    lines.append(f"- Close view used: {report['close_root']}")
    if report.get("close_view_note"):
        lines.append(f"- Close note: {report['close_view_note']}")
    lines.append("")

    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Intraday dates: {', '.join(report['intraday_dates']) or 'None'}")
    lines.append(f"- Close dates: {', '.join(report['close_dates']) or 'None'}")
    lines.append("")

    lines.append("## View Checks")
    lines.append("")
    lines.append("| Date | View | Rows | PK Duplicates | Missing Columns |")
    lines.append("|------|------|------|---------------|-----------------|")
    for entry in report["per_date"]:
        for view_name in ["intraday", "close"]:
            view = entry.get(view_name, {})
            status = view.get("status", "missing")
            rows = view.get("rows", 0) if status == "ok" else "-"
            pk_dups = view.get("pk_duplicates", "-") if status == "ok" else "-"
            missing_cols = ", ".join(view.get("missing_columns", [])) if status == "ok" else status
            lines.append(
                f"| {entry['date']} | {view_name} | {rows} | {pk_dups} | {missing_cols or '-'} |"
            )
    lines.append("")

    lines.append("## Row Alignment (unique conid per date)")
    lines.append("")
    lines.append(
        "| Date | Intraday Conids | Close Conids | Missing in Close | Extra in Close | Underlying mismatches |"
    )
    lines.append("|------|-----------------|--------------|------------------|----------------|-----------------------|")
    for entry in report["per_date"]:
        align = entry.get("alignment", {})
        if align.get("status") == "ok":
            mismatch_text = (
                "; ".join(
                    f"{m['underlying']}: {m['intraday']} vs {m['close']}"
                    for m in align.get("underlying_mismatches", [])
                )
                or "-"
            )
            lines.append(
                f"| {entry['date']} | {align['intraday_conids']} | {align['close_conids']} | "
                f"{align['missing_in_close']} | {align['extra_in_close']} | {mismatch_text} |"
            )
        else:
            reason = align.get("reason", align.get("status", "n/a"))
            lines.append(f"| {entry['date']} | - | - | - | - | {reason} |")
    lines.append("")

    if report.get("issues"):
        lines.append("## Issues")
        lines.append("")
        for item in report["issues"]:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    cfg = load_config(Path(args.config))

    intraday_root = Path(cfg.paths.clean) / "view=intraday"
    close_root = Path(args.close_view) if args.close_view else Path(cfg.paths.clean) / "view=close"
    close_view_note = ""
    if not close_root.exists():
        close_root = Path(cfg.paths.clean) / "view=daily_clean"
        close_view_note = "view=close not found; using view=daily_clean as fallback"

    intraday_dates = list_trade_dates(intraday_root)
    close_dates = list_trade_dates(close_root)
    all_dates = sorted(set(intraday_dates) | set(close_dates))

    per_date: list[dict] = []
    issues: list[str] = []

    for trade_date in all_dates:
        entry: dict[str, object] = {"date": trade_date.isoformat()}
        intraday_path = intraday_root / f"date={trade_date.isoformat()}"
        close_path = close_root / f"date={trade_date.isoformat()}"

        intraday_df = read_parquet_tree(intraday_path)
        close_df = read_parquet_tree(close_path)

        intra_stats = check_view(intraday_df, INTRADAY_PK, INTRADAY_REQUIRED)
        close_stats = check_view(close_df, CLOSE_PK, CLOSE_REQUIRED)

        entry["intraday"] = intra_stats
        entry["close"] = close_stats

        alignment = compute_alignment(
            normalize_frame(intraday_df) if intraday_df is not None else None,
            normalize_frame(close_df) if close_df is not None else None,
        )
        entry["alignment"] = alignment

        if intra_stats.get("status") != "ok":
            issues.append(f"{trade_date}: intraday partition missing or unreadable")
        if close_stats.get("status") != "ok":
            issues.append(f"{trade_date}: close partition missing or unreadable")
        if intra_stats.get("pk_duplicates"):
            issues.append(f"{trade_date}: intraday primary-key duplicates={intra_stats['pk_duplicates']}")
        if close_stats.get("pk_duplicates"):
            issues.append(f"{trade_date}: close primary-key duplicates={close_stats['pk_duplicates']}")
        if intra_stats.get("missing_columns"):
            issues.append(f"{trade_date}: intraday missing columns {intra_stats['missing_columns']}")
        if close_stats.get("missing_columns"):
            issues.append(f"{trade_date}: close missing columns {close_stats['missing_columns']}")
        if alignment.get("status") != "ok":
            issues.append(f"{trade_date}: alignment skipped ({alignment.get('reason', 'unknown')})")
        elif alignment.get("missing_in_close") or alignment.get("extra_in_close"):
            issues.append(
                f"{trade_date}: alignment mismatch missing={alignment.get('missing_in_close')} "
                f"extra={alignment.get('extra_in_close')}"
            )
        per_date.append(entry)

    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "config_path": str(Path(args.config).resolve()),
        "intraday_root": str(intraday_root),
        "close_root": str(close_root),
        "close_view_note": close_view_note,
        "intraday_dates": [d.isoformat() for d in intraday_dates],
        "close_dates": [d.isoformat() for d in close_dates],
        "per_date": per_date,
        "issues": issues,
    }

    output_dir = Path(args.output_dir) if args.output_dir else Path(cfg.paths.clean) / "reports/offline_qa"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base = output_dir / f"offline_qa_{timestamp}"

    json_path = base.with_suffix(".json")
    json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = base.with_suffix(".md")
    md_path.write_text(render_markdown(report_data), encoding="utf-8")

    print(f"Wrote JSON: {json_path}")
    print(f"Wrote Markdown: {md_path}")
    if issues:
        print("Issues detected:")
        for item in issues:
            print(f"- {item}")


if __name__ == "__main__":
    main()
