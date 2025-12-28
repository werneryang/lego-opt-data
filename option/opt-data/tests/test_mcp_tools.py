from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from opt_data.config import load_config
from opt_data.mcp.datasource import DataAccess
from opt_data.mcp.limits import LimitConfig
from opt_data.mcp.tools import (
    get_chain_sample,
    get_partition_issues,
    health_overview,
    list_recent_runs,
    run_status_overview,
)


def _write_config(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    clean = tmp_path / "clean"
    state = tmp_path / "state"
    run_logs = state / "run_logs"
    metrics_db = tmp_path / "metrics.db"

    content = """
[paths]
raw = "{raw}"
clean = "{clean}"
state = "{state}"
contracts_cache = "{state}/contracts_cache"
run_logs = "{run_logs}"

[observability]
metrics_db_path = "{metrics_db}"
""".format(
        raw=raw.as_posix(),
        clean=clean.as_posix(),
        state=state.as_posix(),
        run_logs=run_logs.as_posix(),
        metrics_db=metrics_db.as_posix(),
    )

    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(content, encoding="utf-8")
    return cfg_path


def _write_metrics_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                type TEXT NOT NULL,
                tags TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO metrics (name, value, type, tags) VALUES (?, ?, ?, ?)",
            ("snapshot.fetch.total", 1.0, "counter", json.dumps({"symbol": "AAPL"})),
        )


def _write_run_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_health_overview_reads_latest_logs(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path)
    cfg = load_config(cfg_path)

    metrics_db = Path(cfg.observability.metrics_db_path)
    _write_metrics_db(metrics_db)

    _write_run_log(
        Path(cfg.paths.run_logs) / "metrics" / "metrics_20250101.json",
        {"trade_date": "2025-01-01", "status": "PASS", "metrics": []},
    )
    _write_run_log(
        Path(cfg.paths.run_logs) / "metrics" / "metrics_20250102.json",
        {"trade_date": "2025-01-02", "status": "PASS", "metrics": []},
    )
    _write_run_log(
        Path(cfg.paths.run_logs) / "selfcheck" / "selfcheck_20250102.json",
        {"trade_date": "2025-01-02", "status": "PASS", "reasons": []},
    )
    _write_run_log(
        Path(cfg.paths.run_logs) / "errors" / "summary_20250102.json",
        {"date": "2025-01-02", "fatal_total_matches": 0},
    )

    data = DataAccess(cfg)
    limits = LimitConfig()
    result = health_overview(data, limits, days=1)

    assert result["latest"]["metrics_file"].endswith("metrics_20250102.json")
    assert result["latest_payloads"]["metrics"]["trade_date"] == "2025-01-02"
    assert result["recent_metrics"]
    assert result["meta"]["source"] == "run_logs"
    assert result["meta"]["limit"] is None
    assert result["meta"]["clamped"]["days"] is False


def test_list_recent_runs_applies_limit(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path)
    cfg = load_config(cfg_path)

    for day in ("20250101", "20250102", "20250103"):
        _write_run_log(
            Path(cfg.paths.run_logs) / "metrics" / f"metrics_{day}.json",
            {"trade_date": f"2025-01-{day[-2:]}", "status": "PASS", "metrics": []},
        )

    data = DataAccess(cfg)
    limits = LimitConfig()
    result = list_recent_runs(data, limits, limit=2)

    assert result["limit"] == 2
    assert len(result["runs"]) == 2
    assert result["runs"][0]["date"] == "2025-01-03"
    assert result["meta"]["limit"] == 2
    assert result["meta"]["clamped"]["limit"] is False
    assert result["meta"]["source"] == "run_logs"


def test_get_partition_issues_filters_pass(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path)
    cfg = load_config(cfg_path)

    _write_run_log(
        Path(cfg.paths.run_logs) / "selfcheck" / "selfcheck_20250101.json",
        {"trade_date": "2025-01-01", "status": "PASS", "reasons": []},
    )
    _write_run_log(
        Path(cfg.paths.run_logs) / "selfcheck" / "selfcheck_20250102.json",
        {"trade_date": "2025-01-02", "status": "FAIL", "reasons": ["slot_coverage_min"]},
    )

    data = DataAccess(cfg)
    limits = LimitConfig()
    result = get_partition_issues(data, limits, days=0, limit=10)

    assert result["days"] == limits.default_days
    assert len(result["issues"]) == 1
    assert result["issues"][0]["date"] == "2025-01-02"
    assert result["meta"]["clamped"]["days"] is True
    assert result["meta"]["clamped"]["limit"] is False
    assert result["meta"]["source"] == "run_logs"


def test_get_chain_sample_reads_parquet(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path)
    cfg = load_config(cfg_path)

    today = datetime.now(ZoneInfo(cfg.timezone.name)).date().isoformat()
    parquet_root = Path(cfg.paths.clean) / "view=intraday" / f"date={today}"
    parquet_path = parquet_root / "underlying=AAPL" / "exchange=SMART" / "part-000.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        [
            {"underlying": "AAPL", "bid": 1.0, "ask": 1.1},
            {"underlying": "AAPL", "bid": 1.1, "ask": 1.2},
        ]
    )
    df.to_parquet(parquet_path, index=False)

    data = DataAccess(cfg)
    limits = LimitConfig()
    result = get_chain_sample(
        data,
        limits,
        symbol="aapl",
        source="clean",
        view="intraday",
        days=1,
        limit=1,
    )

    assert result["symbol"] == "AAPL"
    assert result["rows"]
    assert len(result["rows"]) == 1
    assert result["meta"]["source"] == "clean"
    assert result["meta"]["clamped"]["limit"] is False
    assert result["meta"]["clamped"]["days"] is False


def test_run_status_overview_summarizes_recent_day(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path)
    cfg = load_config(cfg_path)

    today = datetime.now(ZoneInfo(cfg.timezone.name)).date()
    ymd = today.strftime("%Y%m%d")

    _write_run_log(
        Path(cfg.paths.run_logs) / "metrics" / f"metrics_{ymd}.json",
        {"trade_date": today.isoformat(), "status": "PASS", "metrics": []},
    )
    _write_run_log(
        Path(cfg.paths.run_logs) / "selfcheck" / f"selfcheck_{ymd}.json",
        {"trade_date": today.isoformat(), "status": "PASS", "reasons": []},
    )
    _write_run_log(
        Path(cfg.paths.run_logs) / "errors" / f"summary_{ymd}.json",
        {"date": today.isoformat(), "fatal_total_matches": 0, "warn_total_matches": 0},
    )

    data = DataAccess(cfg)
    limits = LimitConfig()
    result = run_status_overview(data, limits, days=1)

    assert result["runs"][0]["date"] == today.isoformat()
    assert result["runs"][0]["status"] == "PASS"
    assert result["meta"]["source"] == "run_logs"
