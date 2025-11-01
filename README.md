# opt-data

A lightweight Python toolkit for loading, inspecting, and transforming options market datasets. The project starts with a clean scaffolding so you can plug in your data sources and analysis workflows quickly.

## Getting started

1. Create a Python 3.11 virtual environment: `python3.11 -m venv .venv`
2. Activate it and install dependencies: `source .venv/bin/activate` then `pip install -e .[dev]`
3. Run the test suite: `pytest`
4. Plan and execute a smoke backfill (using your isolated config): `python -m opt_data.cli backfill --start 2024-10-01 --symbols AAPL,MSFT --execute --config config/opt-data.test.toml`

If you prefer `uv` or another package manager, adapt the commands accordingly; the project is configured via `pyproject.toml` and uses Hatch for builds.

### Environment notes (recommended)

- Use a dedicated virtualenv for this project. Installing into a global/base Conda environment may cause dependency solver upgrades (e.g., NumPy 2.x) that conflict with other scientific packages (scipy/numba/astropy). The safest path is a local venv:
  - `python3.11 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -e .[dev]`
- If you prefer Conda, create an isolated env first, then use pip inside it for this project’s extras:
  - `conda create -n opt-data python=3.11 && conda activate opt-data && pip install -e .[dev]`
- CLI dependencies (Typer/APScheduler) are included via the `[dev]` extra. If they’re missing, some CLI tests may be skipped; installing with `-e .[dev]` ensures they’re present.

## Project layout

- `pyproject.toml` – project metadata, dependencies, and tool configuration
- `src/opt_data/` – primary Python package with runtime code
- `tests/` – pytest-based test suite and fixtures
- `data/` – optional folder (ignored by git) for local/raw datasets

## Next steps

- Implement data loaders or adapters under `src/opt_data`
- Populate the `data/` directory with your local datasets (kept out of version control)
- Extend the test suite to cover your transformations and calculations
- Before running large backfills, create a copy of `config/opt-data.toml` (for example `config/opt-data.test.toml`) that points to isolated directories such as `data_test/` and `state_test/`, then run `python -m opt_data.cli backfill --start 2024-10-01 --symbols AAPL,MSFT --execute --config config/opt-data.test.toml` to perform a smoke validation.
- The `[acquisition]` section of the config controls how data is fetched. Set `mode = "historical"` (default) to use `reqHistoricalData` bars for option chains, or switch to `mode = "snapshot"` if you have real-time permissions. `max_strikes_per_expiry` and other knobs allow you to tune request volume.
