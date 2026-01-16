# Tech Stack Constraints (Stock Data)

- **Runtime**: Python 3.11+ (type hints required). Use project venv; Hatch/pyproject governs builds. Ruff line length 100; pytest roots in `tests/`.
- **IBKR Access**: Must go through `ib_insync`; do not import `ibapi.*` directly. Default connection `host=127.0.0.1`, `port=7496/7497`.
- **Core Libraries**: pandas/pyarrow for data processing; Typer for CLI; APScheduler for scheduling.
- **Storage Model**: Parquet only; partitions `date/symbol/exchange/view`. Standard codecs: Snappy for hot data, ZSTD for cold. 
- **Configuration**: TOML based configs in `config/`. Support `.local.toml` for local overrides. 
- **Observability**: Consistent logging under `state/run_logs/`.
