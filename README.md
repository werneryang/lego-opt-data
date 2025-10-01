# opt-data

A lightweight Python toolkit for loading, inspecting, and transforming options market datasets. The project starts with a clean scaffolding so you can plug in your data sources and analysis workflows quickly.

## Getting started

1. Create a Python 3.11 virtual environment: `python3.11 -m venv .venv`
2. Activate it and install dependencies: `source .venv/bin/activate` then `pip install -e .[dev]`
3. Run the test suite: `pytest`
4. Plan and execute a smoke backfill: `python -m opt_data.cli backfill --start 2024-10-01 --symbols AAPL,MSFT --execute`

If you prefer `uv` or another package manager, adapt the commands accordingly; the project is configured via `pyproject.toml` and uses Hatch for builds.

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
