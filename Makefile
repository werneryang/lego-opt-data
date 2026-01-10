.PHONY: install lock

VENV ?= .venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
PIP_COMPILE=$(VENV)/bin/pip-compile
LOCK=requirements.lock
LOCK_DEV=requirements-dev.lock
LOCK_INPUTS=option/opt-data/pyproject.toml stock/stock-data/pyproject.toml
EDITABLES=-e option/opt-data -e stock/stock-data

install:
	python3.11 -m venv $(VENV)
	$(PIP) install --upgrade pip
	@test -f $(LOCK_DEV) || (echo "Missing $(LOCK_DEV). Run 'make lock' first." && exit 1)
	$(PIP) install -r $(LOCK_DEV)
	$(PIP) install $(EDITABLES) --no-deps

lock:
	python3.11 -m venv $(VENV)
	$(PIP) install --upgrade pip pip-tools
	$(PIP_COMPILE) --resolver=backtracking --no-strip-extras --output-file $(LOCK) $(LOCK_INPUTS)
	$(PIP_COMPILE) --resolver=backtracking --no-strip-extras --extra dev --output-file $(LOCK_DEV) $(LOCK_INPUTS)
