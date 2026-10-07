# Shortcuts for common tasks, run from the repo root: make install / dev / dev-web / dev-all / test / lint / format / ingest YEAR=2026
.PHONY: install dev dev-web dev-all test lint format ingest

install:
	@cd backend && uv sync

dev:
	@cd backend && uv run uvicorn sage.main:app --reload

dev-web:
	@cd frontend && npm run dev

# Backend and frontend together in one terminal: -j2 runs both targets at once. Ctrl + C stops both.
dev-all:
	@$(MAKE) --no-print-directory -j2 dev dev-web

test:
	@cd backend && uv run pytest -m "not integration"

lint:
	@cd backend && uv run ruff check && uv run ruff format --check

format:
	@cd backend && uv run ruff check --fix && uv run ruff format

ingest:
	@cd backend && uv run sage ingest --year $(YEAR)
