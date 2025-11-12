from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from typer.testing import CliRunner

from opt_data.cli import app


RUNNER = CliRunner()


def _write_parquet(df: pd.DataFrame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _make_config(tmp_path, trade_date: date) -> str:
    cfg_path = tmp_path / "opt-data.toml"
    text = f"""
    [ib]
    host = "127.0.0.1"
    port = 7497
    client_id = 101
    market_data_type = 1

    [timezone]
    name = "America/New_York"
    update_time = "17:00"

    [paths]
    raw = "{tmp_path}/data/raw"
    clean = "{tmp_path}/data/clean"
    state = "{tmp_path}/state"
    contracts_cache = "{tmp_path}/state/contracts_cache"
    run_logs = "{tmp_path}/state/run_logs"

    [reference]
    corporate_actions = "{tmp_path}/config/corporate_actions.csv"

    [filters]
    moneyness_pct = 0.30
    expiry_types = ["monthly", "quarterly"]

    [rate_limits.discovery]
    per_minute = 100
    burst = 100

    [rate_limits.snapshot]
    per_minute = 100
    burst = 100
    max_concurrent = 10

    [rate_limits.historical]
    per_minute = 100
    burst = 100

    [storage]
    hot_days = 14
    cold_codec = "zstd"
    cold_codec_level = 7
    hot_codec = "snappy"

    [compaction]
    enabled = true
    schedule = "weekly"
    weekday = "sunday"
    start_time = "03:00"
    min_file_size_mb = 32
    max_file_size_mb = 256

    [logging]
    level = "INFO"
    format = "json"

    [cli]
    default_generic_ticks = "100,101,104,105,106,165,221,225,233,293,294,295"
    snapshot_grace_seconds = 120
    rollup_close_slot = 13
    rollup_fallback_slot = 12

    [enrichment]
    fields = ["open_interest"]
    oi_duration = "7 D"
    oi_use_rth = false

    [qa]
    slot_coverage_threshold = 0.90
    delayed_ratio_threshold = 0.10
    rollup_fallback_threshold = 0.05
    oi_enrichment_threshold = 0.95

    [acquisition]
    mode = "snapshot"
    duration = "1 D"
    bar_size = "1 day"
    what_to_show = "TRADES"
    use_rth = true
    max_strikes_per_expiry = 21
    fill_missing_greeks_with_zero = false
    historical_timeout = 30
    """.strip().format(tmp_path=tmp_path)
    cfg_path.write_text(text, encoding="utf-8")
    return str(cfg_path)


def _seed_pass_data(tmp_path, trade_date: date) -> str:
    cfg_file = _make_config(tmp_path, trade_date)
    day_str = trade_date.isoformat()
    base_clean = tmp_path / "data/clean"

    intraday_rows = []
    for symbol in ("AAPL", "MSFT"):
        for slot in range(14):
            intraday_rows.append(
                {
                    "underlying": symbol,
                    "slot_30m": slot,
                    "data_quality_flag": [],
                    "market_data_type": 1,
                    "sample_time": datetime(2025, 10, 6, 9, 30) + pd.Timedelta(minutes=30 * slot),
                }
            )
    intraday_df = pd.DataFrame(intraday_rows)
    for symbol in ("AAPL", "MSFT"):
        _write_parquet(
            intraday_df[intraday_df["underlying"] == symbol],
            base_clean
            / "view=intraday"
            / f"date={day_str}"
            / f"underlying={symbol}"
            / "exchange=SMART"
            / "part-000.parquet",
        )

    daily_rows = []
    for symbol in ("AAPL", "MSFT"):
        daily_rows.append(
            {
                "underlying": symbol,
                "rollup_strategy": "close",
                "open_interest": 111,
                "data_quality_flag": ["oi_enriched"],
            }
        )
    daily_df = pd.DataFrame(daily_rows)
    for symbol in ("AAPL", "MSFT"):
        _write_parquet(
            daily_df[daily_df["underlying"] == symbol],
            base_clean
            / "view=daily_clean"
            / f"date={day_str}"
            / f"underlying={symbol}"
            / "exchange=SMART"
            / "part-000.parquet",
        )

    return cfg_file


def test_selfcheck_pass(tmp_path):
    trade_date = date(2025, 10, 6)
    cfg_file = _seed_pass_data(tmp_path, trade_date)

    result = RUNNER.invoke(
        app,
        [
            "selfcheck",
            "--date",
            trade_date.isoformat(),
            "--config",
            cfg_file,
            "--log-max-total",
            "0",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "status=PASS" in result.output
    report_path = tmp_path / "state/run_logs/selfcheck" / "selfcheck_20251006.json"
    assert report_path.exists()


def test_selfcheck_fails_on_logs(tmp_path):
    trade_date = date(2025, 10, 6)
    cfg_file = _seed_pass_data(tmp_path, trade_date)

    log_dir = tmp_path / "state/run_logs/errors"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "errors_20251006.log").write_text("ERROR something bad\n", encoding="utf-8")

    result = RUNNER.invoke(
        app,
        [
            "selfcheck",
            "--date",
            trade_date.isoformat(),
            "--config",
            cfg_file,
            "--log-max-total",
            "0",
        ],
    )

    assert result.exit_code == 1
    assert "status=FAIL" in result.output
    assert "logs:total>0" in result.output
