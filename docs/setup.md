<!-- How to run SAGE locally from a fresh clone -->
# Local setup

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.12 for you)
- Docker, only for building the backend image
- Node.js and the Supabase CLI, once the frontend and database work starts

## Backend

```bash
cd backend
cp .env.example .env      # then fill in the values
uv sync                   # installs Python 3.12 and all dependencies
uv run pytest             # tests should pass
uv run uvicorn sage.main:app --reload
```

Open http://localhost:8000/health for the health check and http://localhost:8000/docs for the API docs.

From the repo root, `make install`, `make dev`, `make test` and `make lint` do the same.

## Adding a dependency

```bash
cd backend
uv add <package>          # runtime
uv add --dev <package>    # tests and tooling only
```

Commit both `pyproject.toml` and `uv.lock`.
