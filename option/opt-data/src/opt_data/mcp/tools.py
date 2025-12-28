from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .datasource import DataAccess
from .limits import LimitConfig, clamp_days, clamp_int


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def _apply_limit(value: int | None, default: int, maximum: int) -> tuple[int, bool]:
    effective = clamp_int(value, default, maximum)
    return effective, value is not None and effective != value


def _apply_days(value: int | None, default: int, maximum: int) -> tuple[int, bool]:
    effective = clamp_days(value, default, maximum)
    return effective, value is not None and effective != value


def _build_meta(
    *,
    limit: int | None,
    days: int | None,
    clamped_limit: bool,
    clamped_days: bool,
    source: str,
) -> dict[str, Any]:
    return {
        "limit": limit,
        "days": days,
        "clamped": {"limit": clamped_limit, "days": clamped_days},
        "source": source,
    }


def _normalize_status(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text.upper() if text else None


def _derive_run_status(
    metrics_status: str | None,
    selfcheck_status: str | None,
    fatal_total: int | None,
    warn_total: int | None,
) -> str:
    if selfcheck_status and selfcheck_status != "PASS":
        return selfcheck_status
    if metrics_status and metrics_status != "PASS":
        return metrics_status
    if fatal_total is not None and fatal_total > 0:
        return "FAIL"
    if warn_total is not None and warn_total > 0:
        return "WARN"
    if selfcheck_status == "PASS" or metrics_status == "PASS":
        return "PASS"
    return "UNKNOWN"


def run_status_overview(
    data: DataAccess,
    limits: LimitConfig,
    *,
    days: int | None = None,
) -> dict[str, Any]:
    days, days_clamped = _apply_days(days, limits.default_days, limits.max_days)
    items: list[dict[str, Any]] = []
    for day in data.recent_dates(days):
        ymd = day.replace("-", "")
        metrics_path = data.run_logs / "metrics" / f"metrics_{ymd}.json"
        selfcheck_path = data.run_logs / "selfcheck" / f"selfcheck_{ymd}.json"
        error_path = data.run_logs / "errors" / f"summary_{ymd}.json"

        metrics_payload = data.read_json(metrics_path)
        selfcheck_payload = data.read_json(selfcheck_path)
        error_payload = data.read_json(error_path)

        metrics_status = _normalize_status(
            metrics_payload.get("status") if metrics_payload else None
        )
        selfcheck_status = _normalize_status(
            selfcheck_payload.get("status") if selfcheck_payload else None
        )

        fatal_total = None
        warn_total = None
        if error_payload:
            fatal_total = int(error_payload.get("fatal_total_matches", 0) or 0)
            warn_total = int(error_payload.get("warn_total_matches", 0) or 0)

        signals: list[str] = []
        if metrics_payload is None:
            signals.append("metrics_missing")
        elif metrics_status and metrics_status != "PASS":
            signals.append("qa_failed")

        if selfcheck_payload is None:
            signals.append("selfcheck_missing")
        elif selfcheck_status and selfcheck_status != "PASS":
            signals.append("selfcheck_failed")

        if error_payload is None:
            signals.append("errors_summary_missing")
        else:
            if fatal_total and fatal_total > 0:
                signals.append("logscan_fatal_hits")
            if warn_total and warn_total > 0:
                signals.append("logscan_warn_hits")

        items.append(
            {
                "date": day,
                "status": _derive_run_status(
                    metrics_status, selfcheck_status, fatal_total, warn_total
                ),
                "signals": signals,
                "metrics": {
                    "status": metrics_status,
                    "breaches": metrics_payload.get("breaches") if metrics_payload else None,
                    "path": str(metrics_path) if metrics_payload else None,
                },
                "selfcheck": {
                    "status": selfcheck_status,
                    "reasons": selfcheck_payload.get("reasons") if selfcheck_payload else None,
                    "path": str(selfcheck_path) if selfcheck_payload else None,
                },
                "errors": {
                    "fatal_total_matches": fatal_total,
                    "warn_total_matches": warn_total,
                    "path": str(error_path) if error_payload else None,
                },
            }
        )

    return {
        "days": days,
        "runs": items,
        "meta": _build_meta(
            limit=None,
            days=days,
            clamped_limit=False,
            clamped_days=days_clamped,
            source="run_logs",
        ),
    }


def health_overview(
    data: DataAccess,
    limits: LimitConfig,
    *,
    days: int | None = None,
) -> dict[str, Any]:
    days, days_clamped = _apply_days(
        days, limits.health_overview_days_default, limits.health_overview_days_max
    )
    metrics_files = data.list_run_log_files("metrics", "metrics_*.json")
    selfcheck_files = data.list_run_log_files("selfcheck", "selfcheck_*.json")
    error_summaries = data.list_run_log_files("errors", "summary_*.json")

    metrics_payload = data.read_json(metrics_files[0]) if metrics_files else None
    selfcheck_payload = data.read_json(selfcheck_files[0]) if selfcheck_files else None
    error_payload = data.read_json(error_summaries[0]) if error_summaries else None

    recent_metrics = data.recent_metrics_db(limit=20)

    return {
        "days": days,
        "paths": {
            "raw": str(data.raw_root),
            "clean": str(data.clean_root),
            "run_logs": str(data.run_logs),
            "metrics_db": str(data.metrics_db),
        },
        "latest": {
            "metrics_file": str(metrics_files[0]) if metrics_files else None,
            "selfcheck_file": str(selfcheck_files[0]) if selfcheck_files else None,
            "error_summary": str(error_summaries[0]) if error_summaries else None,
        },
        "recent_metrics": recent_metrics,
        "latest_payloads": {
            "metrics": metrics_payload,
            "selfcheck": selfcheck_payload,
            "errors": error_payload,
        },
        "meta": _build_meta(
            limit=None,
            days=days,
            clamped_limit=False,
            clamped_days=days_clamped,
            source="run_logs",
        ),
    }


def list_recent_runs(
    data: DataAccess, limits: LimitConfig, *, limit: int | None = None
) -> dict[str, Any]:
    limit, limit_clamped = _apply_limit(
        limit, limits.list_recent_runs_default, limits.list_recent_runs_max
    )
    metrics_files = data.list_run_log_files("metrics", "metrics_*.json")[:limit]
    runs: list[dict[str, Any]] = []
    for path in metrics_files:
        payload = data.read_json(path) or {}
        runs.append(
            {
                "date": payload.get("trade_date"),
                "status": payload.get("status"),
                "path": str(path),
                "metrics": payload.get("metrics"),
            }
        )
    return {
        "limit": limit,
        "runs": runs,
        "meta": _build_meta(
            limit=limit,
            days=None,
            clamped_limit=limit_clamped,
            clamped_days=False,
            source="run_logs",
        ),
    }


def get_partition_issues(
    data: DataAccess,
    limits: LimitConfig,
    *,
    days: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    days, days_clamped = _apply_days(days, limits.default_days, limits.max_days)
    limit, limit_clamped = _apply_limit(
        limit, limits.get_partition_issues_default, limits.get_partition_issues_max
    )

    selfcheck_files = data.list_run_log_files("selfcheck", "selfcheck_*.json")
    issues: list[dict[str, Any]] = []
    for path in selfcheck_files:
        report = data.read_json(path)
        if not report:
            continue
        if report.get("status") == "PASS":
            continue
        issues.append(
            {
                "date": report.get("trade_date"),
                "status": report.get("status"),
                "reasons": report.get("reasons", []),
                "path": str(path),
                "qa": report.get("qa"),
            }
        )
        if len(issues) >= limit:
            break

    return {
        "days": days,
        "limit": limit,
        "issues": issues,
        "meta": _build_meta(
            limit=limit,
            days=days,
            clamped_limit=limit_clamped,
            clamped_days=days_clamped,
            source="run_logs",
        ),
    }


def get_chain_sample(
    data: DataAccess,
    limits: LimitConfig,
    *,
    symbol: str,
    source: str = "clean",
    view: str = "intraday",
    days: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    if source not in {"clean", "raw"}:
        raise ValueError("source must be 'clean' or 'raw'")
    if source == "clean" and not data.allow_clean:
        raise ValueError("clean data access is disabled")
    if source == "raw" and not data.allow_raw:
        raise ValueError("raw data access is disabled")

    days, days_clamped = _apply_days(days, limits.default_days, limits.max_days)
    limit, limit_clamped = _apply_limit(
        limit, limits.get_chain_sample_default, limits.get_chain_sample_max
    )

    root = data.clean_root if source == "clean" else data.raw_root
    files = data.find_parquet_files(root, view=view, symbol=symbol, days=days)
    rows = data.read_parquet_sample(files, limit=limit)

    return {
        "symbol": symbol.upper(),
        "source": source,
        "view": view,
        "days": days,
        "limit": limit,
        "files_scanned": len(files),
        "rows": rows,
        "meta": _build_meta(
            limit=limit,
            days=days,
            clamped_limit=limit_clamped,
            clamped_days=days_clamped,
            source=source,
        ),
    }


def tool_specs() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="health_overview",
            description="Summarize recent pipeline health and metrics.",
            input_schema={
                "type": "object",
                "properties": {"days": {"type": "integer", "minimum": 1}},
                "required": [],
            },
        ),
        ToolSpec(
            name="run_status_overview",
            description="Summarize run_logs status signals for recent days.",
            input_schema={
                "type": "object",
                "properties": {"days": {"type": "integer", "minimum": 1}},
                "required": [],
            },
        ),
        ToolSpec(
            name="list_recent_runs",
            description="List recent QA metric runs from run_logs.",
            input_schema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1}},
                "required": [],
            },
        ),
        ToolSpec(
            name="get_partition_issues",
            description="Return recent selfcheck failures and reasons.",
            input_schema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1},
                },
                "required": [],
            },
        ),
        ToolSpec(
            name="get_chain_sample",
            description="Sample option chain rows from Parquet partitions.",
            input_schema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "source": {"type": "string", "enum": ["clean", "raw"]},
                    "view": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1},
                },
                "required": ["symbol"],
            },
        ),
    ]


def tool_handlers(data: DataAccess, limits: LimitConfig) -> dict[str, ToolHandler]:
    return {
        "health_overview": lambda args: health_overview(data, limits, days=args.get("days")),
        "run_status_overview": lambda args: run_status_overview(
            data, limits, days=args.get("days")
        ),
        "list_recent_runs": lambda args: list_recent_runs(data, limits, limit=args.get("limit")),
        "get_partition_issues": lambda args: get_partition_issues(
            data,
            limits,
            days=args.get("days"),
            limit=args.get("limit"),
        ),
        "get_chain_sample": lambda args: get_chain_sample(
            data,
            limits,
            symbol=args.get("symbol", ""),
            source=args.get("source", "clean"),
            view=args.get("view", "intraday"),
            days=args.get("days"),
            limit=args.get("limit"),
        ),
    }
