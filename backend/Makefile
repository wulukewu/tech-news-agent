.PHONY: lint format format-check type-check test

PYTHON := $(shell if [ -x venv/bin/python ]; then echo venv/bin/python; else echo python3; fi)

lint:
	$(PYTHON) -m black --check app/ tests/
	$(PYTHON) -m ruff check app/ tests/
	MYPYPATH=. $(PYTHON) -m mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11 --explicit-package-bases || true

format:
	$(PYTHON) -m black app/ tests/
	$(PYTHON) -m ruff check --fix app/ tests/

format-check:
	$(PYTHON) -m black --check app/ tests/

type-check:
	MYPYPATH=. $(PYTHON) -m mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11 --explicit-package-bases || true

test:
	$(PYTHON) -m pytest -v --tb=short -n auto
