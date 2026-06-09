.PHONY: check test lint

check: lint test

lint:
	uv run ruff check

test:
	uv run pytest -q
