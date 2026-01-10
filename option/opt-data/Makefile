.PHONY: install fmt lint test qa lock backfill update compact clean clean-compare mcp-smoke

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
ROOT_DIR=$(abspath $(CURDIR)/../..)
LOCK=$(ROOT_DIR)/requirements.lock
LOCK_DEV=$(ROOT_DIR)/requirements-dev.lock

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	@test -f $(LOCK_DEV) || (echo "Missing $(LOCK_DEV). Run 'make lock' first." && exit 1)
	$(PIP) install -r $(LOCK_DEV)
	$(PIP) install -e . --no-deps

fmt:
	$(PYTHON) -m ruff format src tests

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest
	$(PYTHON) scripts/mcp_smoke_test.py --config config/opt-data.test.toml

qa: fmt lint test

lock:
	$(MAKE) -C $(ROOT_DIR) lock

backfill:
	$(if $(START),,$(error 请提供 START=YYYY-MM-DD))
	$(PYTHON) -m opt_data.cli backfill --start $(START) $(if $(SYMBOLS),--symbols $(SYMBOLS),)

update:
	$(PYTHON) -m opt_data.cli update --date $(if $(DATE),$(DATE),today)

compact:
	$(PYTHON) -m opt_data.cli compact --older-than $(if $(DAYS),$(DAYS),14)

mcp-smoke:
	$(PYTHON) scripts/mcp_smoke_test.py --config config/opt-data.test.toml

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .mypy_cache __pycache__ src/opt_data/__pycache__ tests/__pycache__
	rm -f .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	find . -type f -name '.DS_Store' -delete

clean-compare:
	rm -rf data_test_compare state_test_compare
