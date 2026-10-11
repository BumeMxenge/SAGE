# Shortcuts for common tasks, run from the repo root. CI runs the check targets too, so `make check`
# passing on your laptop means CI's backend, frontend and contract jobs will pass.
.PHONY: install dev dev-web dev-all test lint format check check-backend check-frontend check-contract api-types check-db check-migrations test-integration seed

# The Supabase CLI, pinned. CI sets SUPABASE=supabase, the copy its setup step installs.
SUPABASE ?= npx supabase@2.120.0
# Services `start` skips. None on a laptop, so Studio runs; CI skips the ones its checks never use.
SUPABASE_START_FLAGS ?=

install:
	@cd backend && uv sync
	@cd frontend && npm ci

# The backend on port 8000, against the running local Supabase (make check-db or supabase start
# starts it). The URL and key come from supabase status, never from backend/.env.
dev:
	@env=$$($(SUPABASE) status -o env) && eval "$$env" && cd backend && \
		SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
		uv run uvicorn sage.main:app --reload

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

# Everything CI's backend, frontend and contract jobs check. The database check is separate because
# it needs Docker.
check: check-backend check-frontend check-contract

check-backend: lint test

check-frontend:
	@cd frontend && npm run lint && npm test --if-present && npm run build

# The frontend's types for every request and response, generated from the backend's OpenAPI schema.
# The schema goes to a temporary file, so only api-types.ts is ever committed.
api-types:
	@schema=$$(mktemp) && trap 'rm -f "$$schema"' EXIT && \
		(cd backend && uv run python -c \
			"import json; from sage.main import app; print(json.dumps(app.openapi()))") > "$$schema" && \
		cd frontend && npx openapi-typescript "$$schema" --output src/lib/api-types.ts

# Fails when api-types.ts doesn't match the backend, so a frontend built on an old contract never
# reaches main. It compares only that one file, so other uncommitted work never fails it.
check-contract: api-types
	@git ls-files --error-unmatch frontend/src/lib/api-types.ts > /dev/null 2>&1 && \
		git diff --quiet -- frontend/src/lib/api-types.ts || { \
		echo "frontend/src/lib/api-types.ts doesn't match the backend. Commit what make api-types wrote."; \
		exit 1; }

# What CI's database job runs, as its two steps: rebuild the local database from every migration and
# check it, then run the integration tests against it. The rebuild wipes local data, accounts
# included. Docker must be running.
check-db: check-migrations test-integration

check-migrations:
	@$(SUPABASE) start $(SUPABASE_START_FLAGS)
	@$(SUPABASE) db reset --local
	@$(SUPABASE) db lint --local --fail-on error
	@$(SUPABASE) db advisors --local --type security --fail-on error

# The integration tests, against the running local Supabase. The URL and keys come from
# `supabase status`, never from backend/.env, and the tests refuse any URL that isn't local.
test-integration:
	@env=$$($(SUPABASE) status -o env) && eval "$$env" && cd backend && \
		SAGE_TEST_SUPABASE_URL="$$API_URL" SAGE_TEST_PUBLISHABLE_KEY="$$PUBLISHABLE_KEY" \
		SAGE_TEST_SECRET_KEY="$$SECRET_KEY" uv run pytest -m integration

# Loads the made-up student onto one local account: make seed USER_ID=<account id>.
# The URL and key come from the running local Supabase, never from backend/.env.
seed:
	@env=$$($(SUPABASE) status -o env) && eval "$$env" && cd backend && \
		SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
		uv run sage seed --user "$(USER_ID)"
