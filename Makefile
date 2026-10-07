# Shortcuts for common tasks, run from the repo root. CI runs the check targets too,
# so `make check` passing on your laptop means CI's backend and frontend jobs will pass.
.PHONY: install dev dev-web dev-all test lint format check check-backend check-frontend check-db ingest

# The Supabase CLI, pinned. CI sets SUPABASE=supabase, the copy its setup step installs.
SUPABASE ?= npx supabase@2.120.0

install:
	@cd backend && uv sync
	@cd frontend && npm ci

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

# Everything CI's backend and frontend jobs check. The database check is separate because it needs Docker.
check: check-backend check-frontend

check-backend: lint test

check-frontend:
	@cd frontend && npm run lint && npm test --if-present && npm run build

# What CI's database job runs: start Postgres with every migration applied, then lint and security-check them.
# Docker must be running.
check-db:
	@$(SUPABASE) db start
	@$(SUPABASE) db lint --local --fail-on error
	@$(SUPABASE) db advisors --local --type security --fail-on error

ingest:
	@cd backend && uv run sage ingest --year $(YEAR)
