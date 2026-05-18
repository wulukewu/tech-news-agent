.PHONY: lint format format-check type-check test

PYTHON := $(shell if [ -x venv/bin/python ]; then echo venv/bin/python; else echo python3; fi)

lint:
	$(PYTHON) -m black --check app/ tests/
	$(PYTHON) -m ruff check app/ tests/
	$(PYTHON) -m mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11

format:
	$(PYTHON) -m black app/ tests/
	$(PYTHON) -m ruff check --fix app/ tests/

format-check:
	$(PYTHON) -m black --check app/ tests/

type-check:
	$(PYTHON) -m mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11

test:
	$(PYTHON) -m pytest -v --tb=short -n auto
