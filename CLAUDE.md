<!-- Rules Claude Code reads at the start of every session in this repo. Every line costs context in
every session, so keep it short and keep anything Claude can work out from the code out of it.
HTML comments like this one are stripped before Claude sees the file. -->
# SAGE

SAGE (Student Advisor for Guided Enrolment) is B's final-year thesis app at UCT (EEE4022S, YM-04).
Submission is 26 October 2026. B wants to understand every step, not just receive the result.

## How to work with B

- Plan before changing anything. Research, then present the plan with your questions, and change
  nothing until B approves it. Plan mode enforces this; follow it even in a session that starts in another mode.
- Stop only when B's input is needed. Hand cheap work to subagents: searches to `Explore`,
  checks to `test-runner`. Keep judgement on the main model: schema, RLS policies, engine logic.
- Every plan starts with a short crash course on the task, written for a curious 16-year-old.
- Write clean, concise, industry-standard files with plain comments that say why, not what.
- After the work, walk B through everything you did, again written for a curious 16-year-old.
- Make minimal, targeted changes. Explain why each one is needed.
- In comparisons, list only options that would genuinely work.
- UK English, concise, no em dashes. This covers code comments, docs and commit messages.
- Commit messages: a short title, then a body saying what changed and why.

## Secrets and private data

- Never ask B to paste a secret into the chat. Secrets go straight into GitHub, Azure, Supabase or a
  local `.env`, which is never committed. `.claude/settings.json` blocks you from reading `.env` files.
- The repo is public. Tests and fixtures use made-up data only. B's real transcript stays in
  `private_data/`, which git ignores and you can't read.

## Commands B pastes into his terminal

B uses zsh on an Intel Mac without Homebrew (official installers or uv).
- No inline `# comments` (zsh passes them to the command) and no `!` inside double quotes.
- Commits: `git commit -m "title" -m "body"`, each on one line, no heredocs.
- A secret B must type: `read -rs NAME`, then `export NAME`, use it, then `unset NAME`.

## Checks

- `make check` runs exactly what CI's backend and frontend jobs run. `make check-db` runs CI's
  database job and needs Docker running. Run both through the `test-runner` subagent.
- `make format` fixes Python formatting. `make install` installs the backend and frontend packages.

## Stack

- Backend: FastAPI on Python 3.12 with uv, in `backend/src/sage/`. Folder map and dependency rule:
  `docs/architecture.md`.
- Frontend: React 19, TypeScript and Vite in `frontend/`, on port 3000. The backend runs on 8000.
- Database and sign-in: Supabase (Postgres 17). Migrations in `supabase/migrations/`.
  The CLI is `npx supabase@2.120.0`.
- Hosting: Azure. Resource names live only in `infra/azure/names.env`.
- Laptop setup, deploys and troubleshooting: `docs/setup.md`.

## Rules that catch people out

- FastAPI dependencies are written as `Annotated[T, Depends(...)]`; ruff's B008 fails otherwise.
- Every new `public` table: RLS on, its policies, `revoke all` from `anon` and `authenticated`, then
  explicit grants, including to `service_role` (the backend's secret key skips RLS but still needs
  table privileges). Copy the pattern in `supabase/migrations/20261007062637_create_heartbeat.sql`.
  CI fails if any table the API can reach has RLS off.
- The Supabase publishable key goes in the `apikey` header only. As a Bearer token it is rejected.
- Migrations reach production only through `npx supabase@2.120.0 db push`, which B runs after CI is
  green. Never push migrations yourself.
- After a deploy, trust what the live app reports (the commit from `/health`), not Azure's status flags.

## Needs B's approval every time

`git push`, `az`, and any Supabase command that reaches the hosted project (`db push`, `link`,
`migration repair`, anything with `--linked`). `.claude/settings.json` makes these ask first.
