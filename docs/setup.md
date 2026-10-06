<!-- How to install everything and run SAGE locally, from a fresh laptop -->
# Running SAGE locally

This guide takes you from a fresh laptop to a running backend. Commands are for macOS. Notes for Windows and Linux are given where they differ.

What runs today: the **backend** (FastAPI), on your laptop and on Azure. The frontend and local database are listed under [Not set up yet](#not-set-up-yet) and will be added here as they land.

## 1. Install the tools (once per laptop)

| Tool | Why you need it | How to install |
| --- | --- | --- |
| Xcode Command Line Tools | Gives you `git` and `make` | `xcode-select --install` (skip if you already have Xcode) |
| uv | Installs Python 3.12 and every Python package | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker Desktop (optional) | Builds and runs the backend image exactly as Azure will | Download from [docker.com](https://www.docker.com/products/docker-desktop/), choosing the Intel or Apple chip version to match your Mac |

You do **not** need to install Python yourself. uv downloads a ready-made Python 3.12 the first time it runs.

**Why not Homebrew?** Since September 2026, Homebrew no longer provides ready-made packages for Intel Macs. On an Intel Mac, `brew install uv` compiles uv and 18 dependencies from source, including LLVM and Rust, which can take hours. Each tool's official installer downloads a ready-made build in seconds and works the same on Intel and Apple chip Macs.

Close and reopen your terminal after installing, then check:

```bash
git --version
uv --version
```

**Linux:** use the same uv command as above. **Windows:** install uv in PowerShell with `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. `make` isn't available on Windows by default, so use the plain commands shown next to each `make` command below.

## 2. Get the code

```bash
git clone https://github.com/BumeMxenge/SAGE.git SAGE
cd SAGE
```

The `SAGE` at the end names the folder. Keep the folder name free of colons. uv refuses to run inside a path that contains `:`.

## 3. Set up and run the backend

Run these from the `backend` folder:

```bash
cd backend
cp .env.example .env        # your private settings file; fill in values when needed
uv sync                     # installs Python 3.12 and all packages into backend/.venv
uv run pytest               # all tests should pass
uv run uvicorn sage.main:app --reload
```

Then open in your browser:

- http://localhost:8000/health should show `{"status":"ok"}`
- http://localhost:8000/docs shows every API route, and lets you try them

`--reload` restarts the server whenever you save a file. Press `Ctrl + C` in the terminal to stop it.

Nothing in `.env` is needed yet. The backend runs with the values blank. When Supabase is wired in, copy the project URL and the **secret** key from your Supabase project's API settings into `.env`. Never commit `.env`.

## 4. Everyday commands

From the **repo root** you can use the Makefile shortcuts. The right-hand column does the same thing from inside `backend/`.

| From the repo root | Same thing, from `backend/` | What it does |
| --- | --- | --- |
| `make install` | `uv sync` | Install or update packages to match `uv.lock` |
| `make dev` | `uv run uvicorn sage.main:app --reload` | Run the backend on port 8000 |
| `make test` | `uv run pytest -m "not integration"` | Run the tests CI runs |
| `make lint` | `uv run ruff check && uv run ruff format --check` | Check the code for mistakes and formatting |
| `make format` | `uv run ruff check --fix && uv run ruff format` | Fix what can be fixed and tidy the formatting |
| `make ingest YEAR=2026` | `uv run sage ingest --year 2026` | Load a year's handbook (not built yet) |

Run `make install` (or `uv sync`) after every `git pull`, in case someone added a package.

## 5. Adding a package

From `backend/`:

```bash
uv add <package>          # needed by the running app
uv add --dev <package>    # only needed for tests and tooling
```

This updates both `pyproject.toml` and `uv.lock`. Commit both files together.

## 6. Run the production image (optional)

This builds the same Docker image Azure will run. Docker Desktop must be open.

```bash
cd backend
docker build -t sage-backend .
docker run --rm -p 8000:8000 --env-file .env sage-backend
```

Then check http://localhost:8000/health as before. `Ctrl + C` stops it.

## 7. VS Code

Open the `SAGE` folder in VS Code. Then press `Cmd + Shift + P`, run **Python: Select Interpreter**, and choose the one inside `backend/.venv`. This stops VS Code underlining every import as missing.

Install the **EditorConfig for VS Code** extension too. It makes VS Code follow `.editorconfig` (spaces, line endings, a newline at the end of every file).

## 8. Azure (one-off setup)

The backend runs on Azure Container Apps in South Africa North. `infra/azure/setup.sh` creates everything it needs there. You run it once. Running it again is safe, because it skips or updates whatever already exists.

1. Install the Azure CLI. Microsoft only supports Homebrew for this on macOS, so use uv, which installs it like any other Python tool:
   ```bash
   uv tool install azure-cli --python 3.12
   az login
   ```
   `az login` opens your browser. Sign in with the account that holds your Azure subscription.
2. From the repo root, run `bash infra/azure/setup.sh`. It shows which subscription it will use and asks before creating anything. The first run takes about five minutes.
3. It ends by printing three values. On GitHub, add each one as a repository secret: Settings → Secrets and variables → Actions → New repository secret.

To delete everything SAGE has on Azure and stop all charges, run `az group delete --name rg-sage`.

## 9. Deploying the backend

`.github/workflows/deploy-backend.yml` deploys on its own. After every push to `main` that passes CI, it builds the backend image, pushes it to GitHub's registry as `ghcr.io/bumemxenge/sage-backend:<commit>`, runs it on Azure as the container app `ca-sage-api`, then checks `/health` on the live URL. The run's summary page shows that URL.

The first deploy needs one click from you. New images on GitHub's registry start private, and Azure pulls without a password, so that run stops at **Check the image is public**. Open the link in its error, choose **Change visibility → Public**, then press **Re-run all jobs**. Later images stay public.

- **Redeploy without a new commit:** Actions → Deploy backend → Run workflow, on `main`.
- **Resize:** edit `CPU`, `MEMORY`, `MIN_REPLICAS` or `MAX_REPLICAS` at the top of the workflow and push. With `MIN_REPLICAS: "0"` the app costs nothing while idle, but the first request after a quiet spell waits a few seconds for it to start.
- **Read the logs:** `az containerapp logs show --resource-group rg-sage --name ca-sage-api --follow`. Add `--type system` to see Azure's own messages, such as why a container won't start.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `path segment contains separator ':'` | Your folder name contains a colon. Rename it, e.g. to `SAGE`. |
| A `brew install` runs for ages, compiling LLVM or Rust | Press `Ctrl + C`. On Intel Macs, use the tool's official installer instead (see step 1). |
| `uv: command not found` | Close and reopen the terminal. The installer adds uv to your path, but only new terminals see it. |
| `make: command not found` | Run `xcode-select --install`, or use the plain commands in the table above. |
| `address already in use` on port 8000 | Another server is still running. Find it with `lsof -i :8000` and stop it, or run on another port with `--port 8001`. |
| `ModuleNotFoundError: No module named 'sage'` | Run commands from `backend/`, and run `uv sync` first. |
| Tests pass locally but fail in CI | Run `uv sync` and commit `uv.lock`. CI installs exactly what the lockfile says. |
| The Azure script says it can't use `southafricanorth` | Azure for Students limits each subscription to a few regions. Choose one from the list it prints and change `LOCATION` at the top of the script. |
| The Azure script stops with `PrincipalNotFound` | Azure hadn't finished creating the deploy identity. Wait a minute and run the script again. |
| CI fails at **Check formatting** or **Lint** | Run `make format`, then `make lint`, then commit and push. |
| CI passed but nothing deployed | Deploys follow pushes to `main` only, not pull requests. The deploy workflow must also be on `main` itself. |
| The deploy stops at **Check the image is public** | Make the package public once (section 9), then re-run the workflow. |
| **Sign in to Azure** fails with `AADSTS70021: No matching federated identity record` | Azure only trusts runs on `main`. Run the workflow from `main`, and don't add `environment:` to the job. The error shows the subject GitHub sent, to compare with `GITHUB_SUBJECT` in `infra/azure/setup.sh`. |
| The deploy stops at **Wait for the new revision to take over** | The new image didn't start, so Azure kept the old one running. Read the system logs (section 9), fix the cause and push again. |

## Not set up yet

These sections will be filled in as each part is built. Each will use the tool's official installer, not Homebrew.

- **Frontend:** React app in `frontend/`, running on http://localhost:3000. Will need Node.js, from the installer at [nodejs.org](https://nodejs.org).
- **Local database:** Supabase CLI and migrations in `supabase/`. Will need Docker Desktop. The CLI can run through Node.js with `npx supabase`, so it needs no separate install.
