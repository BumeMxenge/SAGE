# Shortcuts for common tasks, run from the repo root. CI runs the check targets too, so `make check`
# passing on your laptop means CI's backend, frontend and contract jobs will pass.
.PHONY: install dev dev-web dev-all test lint format check check-backend check-frontend check-contract api-types check-db check-migrations test-integration check-ui seed sign-in sign-in-new transcript load mutation planted-faults atp1 atp2 atp3-resolve atp3 atp3-report

# The Supabase CLI, pinned. CI sets SUPABASE=supabase, the copy its setup step installs.
SUPABASE ?= npx supabase@2.120.0
# Services `start` skips. None on a laptop, so Studio runs; CI skips the ones its checks never use.
SUPABASE_START_FLAGS ?=
# The running local Supabase's URL and keys, from `supabase status`, as shell variables such as
# API_URL and SECRET_KEY. Targets take them from here, never from backend/.env.
LOCAL_SUPABASE = env=$$($(SUPABASE) status -o env) && eval "$$env"

install:
	@cd backend && uv sync
	@cd frontend && npm ci

# The backend on port 8000, against the running local Supabase (make check-db or supabase start
# starts it)
dev:
	@$(LOCAL_SUPABASE) && cd backend && \
		SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
		uv run uvicorn sage.main:app --reload

dev-web:
	@cd frontend && npm run dev

# Backend and frontend together in one terminal: -j2 runs both targets at once. Ctrl + C stops both.
dev-all:
	@$(MAKE) --no-print-directory -j2 dev dev-web

# The folders ATP-1's harness imports from, none of them a package: its own, and E2's, whose score.py
# compares rule trees and gives the zero-failure bound. Paths are from backend/.
ATP1_PATH = PYTHONPATH=../tests/acceptance/atp1:../experiments/ingestion/requirement-parsing
# ATP-2's harness adds its own folder, which holds the checker, and takes ATP-1's interval and bound
ATP2_PATH = $(ATP1_PATH):../tests/acceptance/atp2
# ATP-3's harness adds its own folder, and scripts/ for ask_advisor.py's Recorded and show_plans.py's
# made-up account. It takes ATP-1's interval code, so it needs ATP-1's folders too.
ATP3_PATH = $(ATP1_PATH):../tests/acceptance/atp3:scripts

# The unit tests and the ATP harnesses' own tests, then each file's lines they never run. --cov sits
# here rather than in pytest's own settings, so mutmut's runs and a plain uv run pytest stay fast.
test:
	@cd backend && $(ATP3_PATH):../tests/acceptance/atp2 uv run pytest -m "not integration" \
		tests ../tests/acceptance/atp1/test_scoring.py ../tests/acceptance/atp2/test_checker.py \
		../tests/acceptance/atp3 --cov

# ruff's lint and format checks on the backend and the acceptance tests' scripts, then the
# dependency rule's contracts in backend/pyproject.toml
lint:
	@cd backend && uv run ruff check . ../tests && uv run ruff format --check . ../tests && \
		uv run lint-imports --no-cache --no-logo

format:
	@cd backend && uv run ruff check --fix . ../tests && uv run ruff format . ../tests

# Everything CI's backend, frontend and contract jobs check. The database check is separate because
# it needs Docker.
check: check-backend check-frontend check-contract

check-backend: lint test

check-frontend:
	@cd frontend && npm run lint && npm test && npm run build

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

# The integration tests, against the running local Supabase. They refuse any URL that isn't local.
test-integration:
	@$(LOCAL_SUPABASE) && cd backend && \
		SAGE_TEST_SUPABASE_URL="$$API_URL" SAGE_TEST_PUBLISHABLE_KEY="$$PUBLISHABLE_KEY" \
		SAGE_TEST_SECRET_KEY="$$SECRET_KEY" uv run pytest -m integration

# The UI checks: axe, the keyboard walk and the parity images, in light and dark, against this
# worktree's frontend on PORT (3000 by default), which Playwright starts if it isn't running. They
# need local Supabase and the backend (make dev), so CI never runs them. The first run downloads
# Playwright's Chromium.
check-ui:
	@$(SUPABASE) status > /dev/null 2>&1 || \
		{ echo "Local Supabase isn't running: start Docker, then run npx supabase@2.120.0 start in ~/SAGE"; exit 1; }
	@curl --silent --fail --max-time 5 --output /dev/null http://localhost:8000/health || \
		{ echo "The backend isn't running: run make dev in ~/SAGE"; exit 1; }
	@cd frontend && npx playwright install chromium && npx playwright test

# How many small faults (mutants) planted in the code the unit tests catch, written to
# backend/mutation-score.txt. It's too slow for CI, which never runs it. Each run starts afresh, as
# mutmut only re-tests code that changed and would miss a deleted test. mutmut imports a copy of the
# code from backend/mutants/, one folder deeper than usual, so while the run lasts a copy of data/
# goes where SEED_FILE and DATA look for it, and a link puts experiments/ where the drafter's test
# finds E2 and the advisor's tests find E4. A copy, not a link, so a mutant that loses its folder
# can't write to the real one. mutmut runs several test sessions at once, so SAGE_TEST_TEMP gives
# each its own temporary folder.
mutation:
	@cd backend && rm -rf mutants data && cp -R ../data data && ln -sfn ../experiments experiments && \
		export SAGE_TEST_TEMP=$$(mktemp -d) && \
		trap 'rm -rf data "$$SAGE_TEST_TEMP"; rm -f experiments' EXIT && \
		uv run --group mutation mutmut run && \
		uv run --group mutation mutmut export-cicd-stats > /dev/null && \
		score=$$(uv run python scripts/mutation_score.py) && echo "$$score" | tee mutation-score.txt

# The 33 planted faults, each in a copy of the backend, and the test that caught it, if any: the 24
# from my test review, two in the review and approval, four in the plan encoding, and three in the
# advisor's guardrails.
planted-faults:
	@cd backend && uv run python scripts/planted_faults.py

# ATP-1: SAGE against labels written from print, then the report, in tests/acceptance/atp1/results/.
# It runs from the held-out drafts its first run cached, so it calls no model. The run also imports
# count_changes.py and the tests' PDF printer, so their folders join Python's path.
atp1:
	@cd backend && $(ATP1_PATH):../experiments/ingestion:. \
		uv run python ../tests/acceptance/atp1/run.py && \
		$(ATP1_PATH) uv run python ../tests/acceptance/atp1/report.py

# ATP-2: the engine against labels written from print and against the checker, then the report, in
# tests/acceptance/atp2/results/. The checker's own tests run first, as its gate, so no record runs
# on a checker that fails them. Everything is in memory, so it needs no database, and it calls no
# model. Run it on a quiet laptop, as it times the engine.
atp2:
	@cd backend && $(ATP2_PATH) uv run pytest -q ../tests/acceptance/atp2/test_checker.py && \
		$(ATP2_PATH) uv run python ../tests/acceptance/atp2/run.py && \
		$(ATP2_PATH) uv run python ../tests/acceptance/atp2/report.py

# ATP-3: the advisor against held-back prompts and students, beside a control arm, in three steps, all
# in tests/acceptance/atp3/results/. atp3-resolve fixes every expectation from the engine and the plan
# data, and calls no model. atp3 asks both arms, then judges every reply, which costs about USD 2.30
# and stops past USD 5; it asks nothing again once turns.csv is complete, and the judge reads its
# cache. Both SDKs build each reply type when the first reply of that type arrives, which isn't
# thread-safe, so atp3 has them built at import. atp3-report draws the human sample, or reads my
# marks back, then writes the report, and calls no model.
atp3-resolve:
	@cd backend && $(ATP3_PATH) uv run python ../tests/acceptance/atp3/resolve.py

atp3:
	@cd backend && DEFER_PYDANTIC_BUILD=false $(ATP3_PATH) \
		uv run python ../tests/acceptance/atp3/ask.py && \
		DEFER_PYDANTIC_BUILD=false $(ATP3_PATH) uv run python ../tests/acceptance/atp3/judge.py

atp3-report:
	@cd backend && $(ATP3_PATH) uv run python ../tests/acceptance/atp3/sample.py && \
		$(ATP3_PATH) uv run python ../tests/acceptance/atp3/report.py

# The seed file of a student other than Mbali, as FILE=data/synthetic/ziyela.json, for the targets
# below. It is made absolute, as they run from backend/.
SEED_FILE_OPTION = $(if $(FILE),--file "$(abspath $(FILE))")

# Loads the made-up student onto one local account: make seed USER_ID=<account id>, with FILE= for
# another seed file than Mbali's
seed:
	@$(LOCAL_SUPABASE) && cd backend && \
		SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
		uv run sage seed --user "$(USER_ID)" $(SEED_FILE_OPTION)

# Loads every approved year, each data/rules/<year>/rulebook.json, into local Supabase, as after make
# check-db wipes it. A year held exactly as its snapshot is passed over, so a newly approved year loads
# beside the others. One held differently stops it, as sage load --replace is the way to replace one.
load:
	@$(LOCAL_SUPABASE) && cd backend && \
		for snapshot in ../data/rules/*/rulebook.json; do \
			[ -e "$$snapshot" ] || { echo "No year is approved yet: sage approve writes one"; exit 1; }; \
			year=$$(basename "$$(dirname "$$snapshot")") && \
			SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
			uv run sage load --year "$$year" || exit 1; \
		done

# Prints a one-time link that signs Mbali in on the local frontend, with no password and no
# Microsoft. On a fresh local database it first makes her account and loads her seed. PORT=3001 or
# 3002 points the link at a worktree's frontend, and FILE=data/synthetic/ziyela.json signs in the
# student of another seed file instead. Only the link goes to stdout, for scripts to read.
sign-in:
	@$(LOCAL_SUPABASE) && cd backend && \
		SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
		uv run sage sign-in $(if $(PORT),--port $(PORT)) $(SEED_FILE_OPTION) && \
		echo "Open that link in your browser to sign in as $(if $(FILE),the student in $(FILE),Mbali). It works once, within an hour." >&2

# Prints a one-time link for Ilvane, a second made-up student, who hasn't finished setup. Each run
# first deletes her account and everything it saved, so onboarding starts fresh, and never touches
# Mbali's. PORT works as for sign-in, and again only the link goes to stdout.
sign-in-new:
	@$(LOCAL_SUPABASE) && cd backend && \
		SUPABASE_URL="$$API_URL" SUPABASE_SECRET_KEY="$$SECRET_KEY" \
		uv run python scripts/sign_in_new.py $(if $(PORT),--port $(PORT)) && \
		echo "Open that link to sign in as Ilvane, with onboarding fresh. It works once, within an hour." >&2

# Writes the made-up transcript as a PDF with Ilvane's student number, for her onboarding to upload:
# local/transcript.pdf
transcript:
	@cd backend && uv run python -m scripts.transcript
