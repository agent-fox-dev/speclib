.PHONY: check test lint clean

check: lint test

lint:
	uv run ruff check
	uv run mypy packages/afspec/afspec/
	uv run mypy packages/speclib/speclib/
	uv run mypy packages/spec-cli/spec_cli/

test:
	uv run pytest -q

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.py[codz]' -delete 2>/dev/null || true
	find . -type f -name '*$$py.class' -delete 2>/dev/null || true
	rm -rf .pytest_cache .hypothesis .mypy_cache .ruff_cache
	rm -rf build dist *.egg-info .eggs
	rm -rf htmlcov .coverage .coverage.* coverage.xml
	rm -rf .tox .nox .cache
	rm -rf packages/*/.pytest_cache packages/*/.mypy_cache packages/*/.ruff_cache
	rm -rf packages/*/build packages/*/dist packages/*/*.egg-info
