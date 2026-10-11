# Command-line entry point: `uv run sage <command>`, e.g. `uv run sage seed --user <account id>`
import argparse
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from sage.adapters.supabase.rules import SupabaseRuleRepository
from sage.adapters.supabase.students import SupabaseStudentRepository
from sage.config import get_settings
from sage.domain.repositories import AccountNotFound
from sage.services.seed import load_seed, seed

SEED_FILE = Path(__file__).resolve().parents[3] / "data" / "synthetic" / "mbali.json"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="sage")
    commands = parser.add_subparsers(dest="command", required=True)

    seed_command = commands.add_parser(
        "seed", help="Load the made-up student onto one sign-in account"
    )
    seed_command.add_argument(
        "--user", type=UUID, required=True, help="the account's id in Supabase Auth"
    )
    seed_command.add_argument(
        "--yes", action="store_true", help="write to a hosted project without asking"
    )

    args = parser.parse_args(argv)
    if args.command == "seed":
        run_seed(args.user, yes=args.yes)


def run_seed(account: UUID, *, yes: bool) -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise SystemExit(
            "Set SUPABASE_URL and SUPABASE_SECRET_KEY first: `make seed` does it for "
            "local Supabase, and backend/.env holds the hosted project's"
        )
    host = urlsplit(settings.supabase_url).hostname or settings.supabase_url
    # A bad file stops here, before anything is written
    data = load_seed(SEED_FILE, account)

    # Anywhere but this laptop is real data, so it needs a yes
    if host not in LOCAL_HOSTS and not yes:
        answer = input(f"This writes to {host}. Type yes to continue: ")
        if answer.strip().lower() != "yes":
            raise SystemExit("Nothing written")

    url, key = settings.supabase_url, settings.supabase_secret_key
    rules, students = (
        SupabaseRuleRepository(url, key),
        SupabaseStudentRepository(url, key),
    )
    try:
        result = seed(rules, students, data)
    except AccountNotFound:
        raise SystemExit(
            f"No account {account} on {host}. Sign in once, then copy the id from "
            "Authentication > Users in the Supabase dashboard"
        ) from None

    print(f"Seeded {SEED_FILE.name} onto account {account} on {host}:")
    for table, count in result.written.items():
        print(f"  {table}: {count}")
    for difference in result.rulebook_differences:
        print(f"  Already stored, left as it was: {difference}")
    if result.student_differences:
        problems = "; ".join(result.student_differences)
        raise SystemExit(f"Her data didn't read back as written: {problems}")
    print("Read back: her data matches the file.")
