# Tech Stack Constraints

- **Runtime**: Python 3.11 (type hints on; `from __future__ import annotations` expected). Use project venv + `pip install -e .[dev]`; Hatch/pyproject governs builds. Ruff line length 100; pytest roots in `tests/` with `pythonpath=src`.
- **IBKR Access**: Must go through `ib_insync`; do not import `ibapi.*` directly. Default connection `host=127.0.0.1`, `port=7496`, `clientId=101`; deeper client calls should be wrapped/exposed via `IB.client`.
- **Core Libraries**: pandas/pyarrow for dataframes & Parquet; pandera for schema checks; Typer for CLI; APScheduler for scheduling; requests + python-dotenv + pandas-market-calendars. Optional dev deps: pytest, ruff.
- **Storage Model**: Parquet only; partitions `date/underlying/exchange/view=<intraday|daily_clean|daily_adjusted|enrichment>` with Snappy (hot ≤14 days) and ZSTD (cold) per ADR-0001. Atomic write via temp + rename; weekly compaction and retention configured.
- **Configuration & Secrets**: Templates under `config/`; local/test copies suffixed `.local.toml`/`.test.toml` and ignored by git. Environment variables `IB_HOST/PORT/CLIENT_ID`, `IB_MARKET_DATA_TYPE`, `TZ=America/New_York`. Never commit credentials or raw sensitive data.
- **Observability & UI**: Metrics persisted in SQLite; logs under `state/run_logs/`. Streamlit dashboard `src/opt_data/dashboard/app.py` (Altair charts) uses `OPT_DATA_METRICS_DB`/`OPT_DATA_CONFIG`.

