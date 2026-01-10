# opt-data

A lightweight Python toolkit for loading, inspecting, and transforming options market datasets. The project uses a **Snapshot + Rollup** architecture to collect real-time option chains and archive them into daily views.

## Getting started

1. Create a Python 3.11 virtual environment (from repo root): `python3.11 -m venv .venv`
2. Activate it and install locked dependencies:
   - `source .venv/bin/activate`
   - `pip install -r requirements-dev.lock`
   - `pip install -e option/opt-data --no-deps`
3. Run the test suite: `pytest`

If you prefer a per-subproject venv, keep the same lockfile but reference it from this folder:
`pip install -r ../../requirements-dev.lock && pip install -e . --no-deps`
4. **Smoke Test (Snapshot + Rollup)**:
   ```bash
   # 1. Take a snapshot (using test config)
   python -m opt_data.cli snapshot --date today --slot now --symbols AAPL --config config/opt-data.test.toml

   # 2. Run end-of-day rollup (archives snapshots to daily view)
   python -m opt_data.cli rollup --date today --symbols AAPL --config config/opt-data.test.toml
   
   # 3. Run enrichment (fills T+1 data like Open Interest)
   python -m opt_data.cli enrichment --date today --symbols AAPL --config config/opt-data.test.toml
   ```

If you prefer `uv` or another package manager, adapt the commands accordingly; the project is configured via `pyproject.toml` and uses Hatch for builds.

### Environment notes (recommended)

- Use a dedicated virtualenv for this project. Installing into a global/base Conda environment may cause dependency solver upgrades (e.g., NumPy 2.x) that conflict with other scientific packages (scipy/numba/astropy). The safest path is a local venv (repo root):
  - `python3.11 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -r requirements-dev.lock && pip install -e option/opt-data --no-deps`
- If you prefer Conda, create an isolated env first, then use pip inside it for the monorepo lockfile:
  - `conda create -n opt-data python=3.11 && conda activate opt-data && pip install -r requirements-dev.lock && pip install -e option/opt-data --no-deps`
- CLI dependencies (Typer/APScheduler) are included in the repo-root `requirements-dev.lock`. If they’re missing, some CLI tests may be skipped.
- If you change `pyproject.toml`, regenerate lock files with root `make lock` and commit them.

## Project layout

- `pyproject.toml` – project metadata, dependencies, and tool configuration
- repo-root `requirements.lock` – pinned runtime dependencies (shared across subprojects)
- repo-root `requirements-dev.lock` – pinned runtime + dev/test dependencies (shared across subprojects)
- `src/opt_data/` – primary Python package with runtime code
- `tests/` – pytest-based test suite and fixtures
- `data/` – optional folder (ignored by git) for local/raw datasets
- `state/` – runtime state, logs, and checkpoints
- `docs/` – documentation including developer guides and troubleshooting

## Documentation

- Docs index: `docs/README.md`
- Project summary: `docs/ops/project-summary.md`
- Production ops & scheduling: `docs/ops/ops-runbook.md`
- QA & smoke tests: `docs/dev/qa.md`
- Data contract: `docs/architecture/data-contract.md`
- Dev docs: `docs/dev/README.md`

## Features

### Robust Error Handling
- **Automatic Retry**: Network errors and connection issues are automatically retried with exponential backoff
- **Error Tracking**: All errors are flagged with `snapshot_error=True` and detailed error messages
- **Graceful Degradation**: Rollup pipeline filters out error rows automatically

### Performance Monitoring
- **Operation Timing**: Key operations are automatically timed and logged
- **Performance Logs**: Check `state/run_logs/` for detailed performance metrics
- **Resource Tracking**: Monitor data collection efficiency

### Enhanced Logging
- **Structured Logging**: Consistent log format across all modules
- **Context Tracking**: Trade dates, symbols, and operation IDs in all logs
- **Debug Support**: Enable detailed logging for troubleshooting

See [docs/ops/troubleshooting.md](docs/ops/troubleshooting.md) for common issues and solutions.

## Next steps

- **Configuration**: Review `config/opt-data.toml` to adjust universe, rate limits, and storage paths.
- **Scheduling**: Use `python -m opt_data.cli schedule` to generate or run daily jobs (Snapshot -> Rollup -> Enrichment).
- **Current scope**: Production runs the full `config/universe.csv` universe; higher-concurrency “Stage 3” style tuning is tracked in `PLAN.md` and currently on hold.
- **Monitoring**: Check `state/run_logs/errors/` for error summaries and `state/run_logs/metrics/` for QA reports.
