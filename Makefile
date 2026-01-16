.PHONY: install lock lint test

PYTHON_BIN ?= python3.11
VENV ?= .venv
ROOT_DIR := $(abspath $(CURDIR))
VENV_PATH := $(if $(filter /%,$(VENV)),$(VENV),$(ROOT_DIR)/$(VENV))
PYTHON=$(VENV_PATH)/bin/python
ALLOW_EMPTY_STOCK_TESTS ?= 1
PIP=$(VENV_PATH)/bin/pip
PIP_COMPILE=$(VENV_PATH)/bin/pip-compile
LOCK=requirements.lock
LOCK_DEV=requirements-dev.lock
LOCK_INPUTS=option/opt-data/pyproject.toml stock/stock-data/pyproject.toml
EDITABLES=-e option/opt-data -e stock/stock-data

install:
	$(PYTHON_BIN) -m venv $(VENV_PATH)
	$(PIP) install --upgrade pip
	@test -f $(LOCK_DEV) || (echo "Missing $(LOCK_DEV). Run 'make lock' first." && exit 1)
	$(PIP) install -r $(LOCK_DEV)
	$(PIP) install $(EDITABLES) --no-deps

lock:
	$(PYTHON_BIN) -m venv $(VENV_PATH)
	$(PIP) install --upgrade pip pip-tools
	$(PIP_COMPILE) --resolver=backtracking --no-strip-extras --output-file $(LOCK) $(LOCK_INPUTS)
	$(PIP_COMPILE) --resolver=backtracking --no-strip-extras --extra dev --output-file $(LOCK_DEV) $(LOCK_INPUTS)

lint:
	@test -x $(PYTHON) || (echo "Missing $(PYTHON). Run 'make install' first." && exit 1)
	cd option/opt-data && $(PYTHON) -m ruff format --check src tests
	cd option/opt-data && $(PYTHON) -m ruff check src tests
	cd stock/stock-data && $(PYTHON) -m ruff format --check src
	cd stock/stock-data && $(PYTHON) -m ruff check src

test:
	@test -x $(PYTHON) || (echo "Missing $(PYTHON). Run 'make install' first." && exit 1)
	cd option/opt-data && $(PYTHON) -m pytest --maxfail=1 --disable-warnings -q
	@if test -d stock/stock-data/tests && find stock/stock-data/tests -type f \( -name 'test_*.py' -o -name '*_test.py' \) -print -quit | grep -q .; then \
		cd stock/stock-data && $(PYTHON) -m pytest --maxfail=1 --disable-warnings -q; \
	elif [ "$(ALLOW_EMPTY_STOCK_TESTS)" = "1" ]; then \
		echo "No stock tests found; skipping stock/stock-data pytest."; \
	else \
		echo "No stock tests found; failing stock/stock-data pytest."; \
		exit 1; \
	fi
