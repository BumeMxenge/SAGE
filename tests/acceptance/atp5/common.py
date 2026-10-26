# Shared foundation for ATP-5 (load) and ATP-6 (access and privacy): the project under test read
# from .env, the clients the scripts build on, a token cache that signs accounts in and refreshes
# them, the test-account manifest, a CSV writer, and the lists of routes and tables the sweeps walk.
# ATP-6's scripts in ../atp6 import this. Nothing here ever prints a token or a secret.
from __future__ import annotations

import csv
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any

import httpx

HERE = Path(__file__).resolve().parent  # tests/acceptance/atp5
REPO_ROOT = HERE.parents[2]
BACKEND = REPO_ROOT / "backend"
# git-ignored: the token cache and the account manifest live here
CACHE = HERE / ".cache"
ENV_FILE = HERE / ".env"
MANIFEST = CACHE / "accounts.json"
TOKENS = CACHE / "tokens.json"

# The four settings every script needs, read from .env (hosted) or the environment (a local run
# sets them from supabase status). Their names are told to B, who fills in .env.
REQUIRED = (
    "HOSTED_API_URL",
    "HOSTED_SUPABASE_URL",
    "HOSTED_SUPABASE_SECRET_KEY",
    "HOSTED_SUPABASE_PUBLISHABLE_KEY",
)
# Supabase's auth rate limit: 30 sign-ins per 5 minutes per IP. The runbook raises it for the
# window, but the harness paces anyway, so a forgotten raise only slows it rather than failing it.
# Seconds between sign-ins, so 30 fit comfortably inside any 5-minute window
SIGN_IN_GAP = 10.0


def load_env() -> None:
    # Reads KEY=VALUE lines from .env into the environment without overwriting a value already set,
    # so a local run's command-line settings win over a hosted .env left in place.
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


class Config:
    def __init__(self) -> None:
        load_env()
        missing = [name for name in REQUIRED if not os.environ.get(name)]
        if missing:
            raise SystemExit(
                "Set these in tests/acceptance/atp5/.env, or in the environment for a local run: "
                + ", ".join(missing)
            )
        self.api_url = os.environ["HOSTED_API_URL"].rstrip("/")
        self.supabase_url = os.environ["HOSTED_SUPABASE_URL"].rstrip("/")
        self.secret_key = os.environ["HOSTED_SUPABASE_SECRET_KEY"]
        self.publishable_key = os.environ["HOSTED_SUPABASE_PUBLISHABLE_KEY"]


def number_of(email: str) -> str:
    # A student's number is the part of their UCT email before the @, upper-cased, as the backend
    # works it out. Staff emails have no number.
    return email.partition("@")[0].upper()


# ---- the token cache ----
# Each account is signed in once, through Supabase's auth REST endpoint with the publishable key,
# exactly as a browser would. The session is cached so Locust reads a ready token rather than
# signing in under load, and a token near its one-hour expiry is refreshed outside the timed work.


class Tokens:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._lock = threading.Lock()
        self._auth = f"{cfg.supabase_url}/auth/v1"
        self._headers = {"apikey": cfg.publishable_key}
        self._sessions: dict[str, dict[str, Any]] = {}
        if TOKENS.exists():
            self._sessions = json.loads(TOKENS.read_text(encoding="utf-8"))

    def sign_in(self, email: str, password: str) -> None:
        # grant_type=password, the browser's own sign-in. Records when it was obtained, so staleness
        # is judged without decoding the token.
        response = httpx.post(
            f"{self._auth}/token",
            params={"grant_type": "password"},
            headers=self._headers,
            json={"email": email, "password": password},
            timeout=30,
        )
        response.raise_for_status()
        self._store(email, response.json())

    def refresh(self, email: str) -> None:
        session = self._sessions[email]
        response = httpx.post(
            f"{self._auth}/token",
            params={"grant_type": "refresh_token"},
            headers=self._headers,
            json={"refresh_token": session["refresh_token"]},
            timeout=30,
        )
        response.raise_for_status()
        self._store(email, response.json())

    def refresh_if_older_than(self, email: str, seconds: float) -> bool:
        # Refreshes a session older than the limit, so no token expires mid-stage. Returns whether
        # it refreshed, for the caller to pace. A session not yet signed in is left alone.
        with self._lock:
            session = self._sessions.get(email)
            if session is None or time.time() - session["obtained"] < seconds:
                return False
        self.refresh(email)
        return True

    def access_token(self, email: str) -> str:
        return self._sessions[email]["access_token"]

    def raw_access_token(self, email: str) -> str | None:
        # The cached token as it stands, never refreshed, for the expired-token attempt
        session = self._sessions.get(email)
        return session["access_token"] if session else None

    def obtained(self, email: str) -> float | None:
        session = self._sessions.get(email)
        return session["obtained"] if session else None

    def _store(self, email: str, body: dict[str, Any]) -> None:
        with self._lock:
            self._sessions[email] = {
                "access_token": body["access_token"],
                "refresh_token": body["refresh_token"],
                "obtained": time.time(),
            }
            CACHE.mkdir(exist_ok=True)
            TOKENS.write_text(json.dumps(self._sessions), encoding="utf-8")


# ---- the account manifest ----


def save_manifest(accounts: list[dict[str, Any]]) -> None:
    CACHE.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps({"accounts": accounts}, indent=2), encoding="utf-8")


def load_manifest() -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        raise SystemExit("No account manifest. Run accounts.py --create first.")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["accounts"]


def accounts_of_role(role: str) -> list[dict[str, Any]]:
    return [account for account in load_manifest() if account["role"] == role]


# ---- CSV ----


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    # Writes a result file whole, so a rerun never appends to the last run's rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, Any]],
    *,
    fresh: bool = False,
) -> None:
    # Adds rows, writing the header only on a new file. A probe runs in several calls across the
    # window, so fresh truncates on the first call of a run.
    path.parent.mkdir(parents=True, exist_ok=True)
    new = fresh or not path.exists()
    with path.open("w" if fresh else "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if new:
            writer.writeheader()
        writer.writerows(rows)


# ---- the routes and tables the sweeps walk ----


def routes(api_url: str) -> list[tuple[str, str]]:
    # Every operation the app serves, from its OpenAPI schema, as test_guards.py lists them, so a
    # route left out of the schema is the only way to escape the sweep
    schema = httpx.get(f"{api_url}/openapi.json", timeout=30).json()
    return [
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
    ]


def student_tables() -> list[str]:
    from sage.shared.supabase import students

    return ["students", *students.ORDER]


def rulebook_tables() -> list[str]:
    from sage.shared.rules import RuleSet

    return list(RuleSet.model_fields)


def transcript_pdf(student_number: str) -> bytes:
    # A made-up transcript for this number, printed the way backend/scripts/transcript.py prints
    # one: the committed fixture with only its Campus ID swapped, through the tests' own printer
    sys.path.insert(0, str(BACKEND))
    from tests.pdf import pdf_of, split_pages

    fixture = BACKEND / "tests" / "fixtures" / "transcript.txt"
    text, found = re.subn(
        r"^Campus ID: \S+",
        f"Campus ID: {student_number}",
        fixture.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    if not found:
        raise SystemExit(f"{fixture} holds no Campus ID line to change")
    return pdf_of(split_pages(text))
