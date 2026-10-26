<!-- What ATP-5's load harness measures, how to run it, and how to read its report -->
# ATP-5: performance under load

ATP-5 asks whether the deployed SAGE meets NF-4 at 35 concurrent sessions, and again at 35 after a
spike to 70: a first plan set or a reply within 10 s at the 95th percentile, opening, narrowing or
checking a plan within 1 s, and at most 1% of operations failing. It also asks where the time goes.
The harness drives the real deployment, so it reads the project under test from `.env`.

This is an environment, not a package, as `experiments/` are: `uv sync` here installs the backend's
`sage` package by path, plus Locust. ATP-6's scripts in `../atp6` share this environment.

## Settings

Copy `.env.example` to `.env` and fill in the four values (the hosted backend URL, the Supabase
project URL, and its secret and publishable keys). `.env` is git-ignored and never printed. A local
dry run sets the same four names in the environment instead, from `supabase status`.

## The scripts

| Script | What it does |
| --- | --- |
| `accounts.py` | Makes, signs in and deletes the test accounts through the admin API: 105 load students (70 for the stages, 35 for the rescaled run), three access students A, B and C, and one staff account. The manifest and the cached session tokens live in a git-ignored `.cache/`. |
| `probes.py` | The two cold starts, each after more than six minutes idle, and 50 `/health` against 50 `/v1/me`, so the gap estimates the round trip to the EU database. |
| `locustfile.py` | The simulated student: finish setup (timed "first plan set"), the questionnaire ("narrow"), then a weighted loop of the plan set, one plan ("open"), a pair, Explore Electives ("check") and Course History, with a question about every three minutes ("reply", capped at 600). The `LoadTestShape` runs the ramp, hold and spike stages when `SAGE_LOAD_SHAPE=1`. |
| `report.py` | Reads the CSVs in `results/` and writes `report.md`: p50, p95 and p99 per operation and per stage against NF-4's targets, with error classes and a verdict each. |

## Running it

Each load account is signed in once by `accounts.py sign-in`; Locust reads the cached token and
refreshes any token over 50 minutes old outside the timed requests, so no refresh counts as an
operation. The stage run is `SAGE_LOAD_SHAPE=1 ... locust --headless ...`; the rescaled comparison
is a flat 35-user run with `SAGE_LOAD_OUT=requests_rescaled.csv` so it writes beside the stage run.
The window's runbook gives every command. `make atp5-report` writes the report from the CSVs.

## Where the time goes

The report accounts for the baseline time ATP-5 measures: the cold starts, the EU round trip and
the rescaled comparison. Splitting a reply's time between its model calls is left to the Chapter 5
figures, which join ATP-3's `calls.csv`; ATP-5 measures the reply end to end only.

## Outputs

`results/` holds `requests.csv`, `requests_rescaled.csv`, `stages.csv`, `probes.csv`,
`azure_metrics.csv` and `report.md`. The report is made only from the CSVs, so every number traces
to a row.
