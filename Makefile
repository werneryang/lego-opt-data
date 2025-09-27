.PHONY: install fmt lint test qa backfill update compact clean

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

fmt:
	$(PYTHON) -m ruff format src tests

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest

qa: fmt lint test

backfill:
	$(if $(START),,$(error 请提供 START=YYYY-MM-DD))
	$(PYTHON) -m opt_data.cli backfill --start $(START) $(if $(SYMBOLS),--symbols $(SYMBOLS),)

update:
	$(PYTHON) -m opt_data.cli update --date $(if $(DATE),$(DATE),today)

compact:
	$(PYTHON) -m opt_data.cli compact --older-than $(if $(DAYS),$(DAYS),14)

clean:
	rm -rf $(VENV) __pycache__ src/opt_data/__pycache__ tests/__pycache__
