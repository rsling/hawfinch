.PHONY: setup test lint format clean

setup:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

clean:
	rm -rf .venv .pytest_cache .ruff_cache extract/src/*.egg-info
