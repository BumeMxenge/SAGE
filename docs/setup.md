<!-- How to install everything and run SAGE locally, from a fresh laptop -->
# Running SAGE locally

This guide takes you from a fresh laptop to a running backend and frontend. Commands are for macOS. Notes for Windows and Linux are given where they differ.

What runs today: the **backend** (FastAPI) and the **frontend** (React), on your laptop and on Azure, and the **database** on Supabase (section 12).

## 1. Install the tools (once per laptop)

| Tool | Why you need it | How to install |
| --- | --- | --- |
| Xcode Command Line Tools | Gives you `git` and `make` | `xcode-select --install` (skip if you already have Xcode) |
| uv | Installs Python 3.12 and every Python package | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js 24 (LTS) | Runs the frontend's tools, and npm, which installs its packages | Download the LTS macOS installer (`.pkg`) from [nodejs.org](https://nodejs.org) and open it |
| Docker Desktop (optional) | Builds and runs the backend image exactly as Azure will, and runs a local database (section 12) | Download from [docker.com](https://www.docker.com/products/docker-desktop/), choosing the Intel or Apple chip version to match your Mac |

You do **not** need to install Python yourself. uv downloads a ready-made Python 3.12 the first time it runs.

**Why not Homebrew?** Since September 2026, Homebrew no longer provides ready-made packages for Intel Macs. On an Intel Mac, `brew install uv` compiles uv and 18 dependencies from source, including LLVM and Rust, which can take hours. Each tool's official installer downloads a ready-made build in seconds and works the same on Intel and Apple chip Macs.

Close and reopen your terminal after installing, then check:

```bash
git --version
uv --version
node --version   # should show v24, e.g. v24.11.1
```

**Linux:** use the same uv command as above. **Windows:** install uv in PowerShell with `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. `make` isn't available on Windows by default, so use the plain commands shown next to each `make` command below. On every system, install Node.js with the LTS installer for that system from nodejs.org.

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

- http://localhost:8000/health should show `{"status":"ok","commit":"dev"}`. On Azure, `commit` shows which commit is running.
- http://localhost:8000/docs shows every API route, and lets you try them

`--reload` restarts the server whenever you save a file. Press `Ctrl + C` in the terminal to stop it.

Nothing in `.env` is needed yet. The backend runs with the values blank. When Supabase is wired in, copy the project URL and the **secret** key from your Supabase project's API settings into `.env`. Never commit `.env`.

## 4. Set up and run the frontend

The first time only, tell Supabase that sign-in may return to your laptop: in your Supabase project, go to Authentication → URL Configuration and add `http://localhost:3000/**` under **Redirect URLs**.

Then, in a second terminal (leave the backend from step 3 running), from the repo root:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

`cp` makes your settings file. Fill it in before `npm run dev`: `VITE_API_URL` already points at your local backend, and the other two values come from your Supabase project's API settings. They are the project URL (just `https://<project>.supabase.co`, without `/rest/v1/` on the end) and the **publishable** key (it starts with `sb_publishable_`). Vite reads `.env` only when it starts, so restart `npm run dev` after editing it.

`npm ci` installs exactly what `package-lock.json` lists, into `frontend/node_modules`. `npm run dev` serves the app on port 3000.

Then open http://localhost:3000. The page should say the backend is up, running a local build. **Continue with UCT email** sends you to Microsoft and back, then shows your email.

From then on, `make dev-all` from the repo root starts the backend and the frontend together in one terminal, and one `Ctrl + C` stops both.

Everything in `frontend/.env` ends up in the files your browser downloads, where anyone can read it. That's fine for the publishable key. The **secret** key only ever goes in `backend/.env`.

| From `frontend/` | What it does |
| --- | --- |
| `npm ci` | Install packages to match `package-lock.json`. Run it after every `git pull` |
| `npm run dev` | Run the app on port 3000, reloading as you save. `Ctrl + C` stops it |
| `npm run lint` | Check the code for mistakes (oxlint) |
| `npm run build` | Check the types, then build the production files into `frontend/dist/` |
| `npm run preview` | Serve that build on port 3000, the way Azure will |
| `npm install <package>` | Add a package. Commit `package.json` and `package-lock.json` together |

## 5. Everyday commands

From the **repo root** you can use the Makefile shortcuts. The middle column does the same thing without `make`, from inside `backend/` unless it says otherwise.

| From the repo root | Same thing, without `make` | What it does |
| --- | --- | --- |
| `make install` | `uv sync` | Install or update packages to match `uv.lock` |
| `make dev` | `uv run uvicorn sage.main:app --reload` | Run the backend on port 8000 |
| `make dev-web` | `npm run dev`, from `frontend/` | Run the frontend on port 3000 |
| `make dev-all` | The two above, in two terminals | Run the backend and frontend together in one terminal. Their log lines mix; `Ctrl + C` stops both |
| `make test` | `uv run pytest -m "not integration"` | Run the tests CI runs |
| `make lint` | `uv run ruff check && uv run ruff format --check` | Check the code for mistakes and formatting |
| `make format` | `uv run ruff check --fix && uv run ruff format` | Fix what can be fixed and tidy the formatting |
| `make ingest YEAR=2026` | `uv run sage ingest --year 2026` | Load a year's handbook (not built yet) |

Run `make install` (or `uv sync`) after every `git pull`, in case someone added a package.

## 6. Adding a package

From `backend/`:

```bash
uv add <package>          # needed by the running app
uv add --dev <package>    # only needed for tests and tooling
```

This updates both `pyproject.toml` and `uv.lock`. Commit both files together.

## 7. Run the production image (optional)

This builds the same Docker image Azure will run. Docker Desktop must be open.

```bash
cd backend
docker build -t sage-backend .
docker run --rm -p 8000:8000 --env-file .env sage-backend
```

Then check http://localhost:8000/health as before. `Ctrl + C` stops it.

## 8. VS Code

Open the `SAGE` folder in VS Code. Then press `Cmd + Shift + P`, run **Python: Select Interpreter**, and choose the one inside `backend/.venv`. This stops VS Code underlining every import as missing.

Install the **EditorConfig for VS Code** extension too. It makes VS Code follow `.editorconfig` (spaces, line endings, a newline at the end of every file).

## 9. Azure (one-off setup)

The backend runs on Azure Container Apps and the frontend on an Azure Storage static website, both in South Africa North. `infra/azure/setup.sh` creates everything they need there. You run it once. Running it again is safe, because it skips or updates whatever already exists.

1. Install the Azure CLI. Microsoft only supports Homebrew for this on macOS, so use uv, which installs it like any other Python tool:
   ```bash
   uv tool install azure-cli --python 3.12
   az login
   ```
   `az login` opens your browser. Sign in with the account that holds your Azure subscription.
2. From the repo root, run `bash infra/azure/setup.sh`. It shows which subscription it will use and asks before creating anything. The first run takes about five minutes.
3. It ends by printing three values. On GitHub, add each one as a repository secret: Settings → Secrets and variables → Actions → New repository secret. It also prints the frontend's web address, which section 11 uses.

If you ran the script before the frontend existed, run it again. It adds the storage account and leaves everything else as it is.

To delete everything SAGE has on Azure and stop all charges, run `az group delete --name rg-sage`.

## 10. Deploying the backend

`.github/workflows/deploy-backend.yml` deploys on its own. After every push to `main` that passes CI, it builds the backend image, pushes it to GitHub's registry as `ghcr.io/bumemxenge/sage-backend:<commit>`, runs it on Azure as the container app `ca-sage-api`, then waits until `/health` on the live URL reports the new commit. The run's summary page shows that URL.

- **Redeploy without a new commit:** Actions → Deploy backend → Run workflow, on `main`.
- **Resize:** edit `CPU`, `MEMORY`, `MIN_REPLICAS` or `MAX_REPLICAS` at the top of the workflow and push. With `MIN_REPLICAS: "0"` the app costs nothing while idle, but the first request after a quiet spell waits a few seconds for it to start.
- **Which websites may call it:** each deploy sets `CORS_ORIGINS` on the app to the frontend's web address, looked up from the storage account. On your laptop the backend allows `http://localhost:3000` instead (see `backend/.env.example`).
- **Read the logs:** `az containerapp logs show --resource-group rg-sage --name ca-sage-api --follow`. Add `--type system` to see Azure's own messages, such as why a container won't start.

## 11. Deploying the frontend

`.github/workflows/deploy-frontend.yml` also deploys on its own after every push to `main` that passes CI. It looks up the backend's address, builds the frontend with it, uploads the files to the storage account `sageuct`, then checks the website serves the new version. The run's summary page shows the web address.

Before the first deploy (once):

1. Run `infra/azure/setup.sh` (section 9). It creates the storage account and prints the web address.
2. In Supabase, go to Authentication → URL Configuration. Under **Redirect URLs**, add the web address followed by `/**`, next to `http://localhost:3000/**`. Set **Site URL** to the web address too: Supabase sends people there if a sign-in asks to return somewhere that isn't on the list.
3. On GitHub, go to Settings → Secrets and variables → Actions, open the **Variables** tab and add `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`, with the same values as your `frontend/.env`. They are variables rather than secrets because they end up in the public files anyway.

- **Redeploy without a new commit:** Actions → Deploy frontend → Run workflow, on `main`.
- **Seeing a new version:** files in `assets/` get new names with every build, so browsers keep them for a year. `index.html` is re-checked on every visit, so a new deploy shows on the next reload.

## 12. Database (Supabase)

The database lives on Supabase. Its tables are built by **migrations**: timestamped SQL files in `supabase/migrations/`, applied in order. `supabase/config.toml` holds the CLI's settings. Run the Supabase CLI through Node.js, at the version CI uses, from the repo root: `npx supabase@2.120.0 <command>`. It needs no separate install.

Link your laptop to the project (once per laptop):

```bash
npx supabase@2.120.0 login
npx supabase@2.120.0 link --project-ref qkqsiesntzriurhgttgy
```

`login` opens your browser. If `link` asks for the database password, type it into the terminal (nothing shows as you type). Never put it in a file. If you've lost it, reset it in the Supabase dashboard's database settings.

Add a migration:

1. Run `npx supabase@2.120.0 migration new what_it_does`. It creates an empty, timestamped file in `supabase/migrations/`.
2. Write the SQL. Every table in `public` needs row level security switched on, a policy for each kind of access, and a `grant` for each role that may reach it. Without the grant the Data API can't see the table at all. The heartbeat migration is a short example of all three.
3. Commit and push. CI's **Database** job applies every migration to an empty database, lints them, and fails if a table the API can reach has no row level security.

Once CI is green, apply new migrations to the hosted project:

```bash
npx supabase@2.120.0 db push --dry-run
npx supabase@2.120.0 db push
```

The first lists what would run. The second runs it, after asking. `npx supabase@2.120.0 migration list` shows which migrations each side has. Never edit a migration after pushing it; make the change in a new one.

**Local database (optional):** with Docker Desktop open, `npx supabase@2.120.0 db start` starts one with every migration applied, and `npx supabase@2.120.0 db reset` rebuilds it from scratch.

**Keep-alive:** Supabase pauses a free project after a week without database activity. `.github/workflows/keep-alive.yml` reads the one row in `public.heartbeat` every six hours, with the same two GitHub variables the frontend deploy uses (section 11).

- **Check it by hand:** Actions → Keep Supabase awake → Run workflow, on `main`.
- **If a run fails:** GitHub emails you. A paused project comes back with **Resume project** on its Supabase dashboard page.
- **After 60 days without a commit:** GitHub switches off scheduled workflows in public repos. Actions → Keep Supabase awake → Enable workflow turns it back on.

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
| The deploy stops at **Check the image is public** | Azure pulls without a password, so the package must be public. Open the link in the error, choose **Change visibility → Public**, then re-run the workflow. |
| **Sign in to Azure** fails with `AADSTS70021: No matching federated identity record` | Azure only trusts runs on `main`. Run the workflow from `main`, and don't add `environment:` to the job. The error shows the subject GitHub sent, to compare with `GITHUB_SUBJECT` in `infra/azure/setup.sh`. |
| The deploy stops at **Check the new commit is live** | The new image didn't start, so Azure kept the old one running (its commit shows in the step's output). Read the system logs (section 10), fix the cause and push again. |
| `node: command not found`, or `node --version` doesn't show v24 | Install Node.js 24 with the LTS installer from nodejs.org (step 1), then close and reopen the terminal. |
| `Port 3000 is already in use` | Another dev server is still running. Find it with `lsof -i :3000` and stop it. The port is fixed on purpose, because the backend and Supabase only allow 3000. |
| A blank page at http://localhost:3000 | Open the browser console (`Cmd + Option + J` in Chrome). If it says a `VITE_` setting isn't set, copy `.env.example` to `.env` in `frontend/`, fill it in and restart `npm run dev`. |
| The page says it can't reach the backend | Locally: check the backend is running (`make dev`) and that `VITE_API_URL` in `frontend/.env` matches it. On Azure: run Deploy backend again, which re-reads the frontend's address. |
| Sign-in ends on the wrong site, or Supabase says the redirect isn't allowed | Add that site's address followed by `/**` under Supabase's Redirect URLs (sections 4 and 11). |
| The Azure script says another customer has the storage name | Choose a new name (3 to 24 lowercase letters and digits). Change `STORAGE_ACCOUNT` in `infra/azure/setup.sh` and in both deploy workflows, then run the script again. |
| Deploy backend stops with `Storage account sageuct not found` | Run `infra/azure/setup.sh` (section 9), then re-run the workflow. |
| Deploy frontend stops at **Build**, saying a `VITE_` variable isn't set | Add it on GitHub as a variable, not a secret (section 11). |
| Deploy frontend stops at **Upload to Azure Storage** with `AuthorizationPermissionMismatch` | The upload role from the Azure script can take a few minutes to start working. Wait five minutes and re-run the workflow. If it keeps failing, run the script again. |
| `link` or `db push` fails with `failed SASL auth` | Give the CLI the database password for this terminal: run `read -rs SUPABASE_DB_PASSWORD`, type the password and press Enter, run `export SUPABASE_DB_PASSWORD`, then try again. Run `unset SUPABASE_DB_PASSWORD` when done. |
| `link` or `db push` can't reach the database | The CLI uses Supabase's IPv4 pooler unless you add `--skip-pooler`, so leave that flag off. Check the project isn't paused (section 12). |
| `link` warns that the database version differs | Set `major_version` in `supabase/config.toml` to the version it shows, then commit. |
| The Data API says `permission denied for table` | The table has no `grant` for that role. Add one in a new migration (section 12). |
| The Data API returns `[]` for a table that has rows | Row level security is hiding them: no policy lets that role read. Add one in a new migration. |
| Keep Supabase awake fails | Its error says why. A paused project needs **Resume project** on the Supabase dashboard. `Could not find the table` means the heartbeat migration hasn't been pushed yet (section 12). |
