# Shortcuts for common tasks, run from the repo root: make install / dev / test / lint / format / ingest YEAR=2026
.PHONY: install dev test lint format ingest

install:
	@cd backend && uv sync

dev:
	@cd backend && uv run uvicorn sage.main:app --reload

test:
	@cd backend && uv run pytest -m "not integration"

lint:
	@cd backend && uv run ruff check && uv run ruff format --check

format:
	@cd backend && uv run ruff check --fix && uv run ruff format

ingest:
	@cd backend && uv run sage ingest --year $(YEAR)
