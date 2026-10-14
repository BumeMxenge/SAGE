# Command-line entry point: `uv run sage <command>`, e.g. `uv run sage seed --user <account id>`
import argparse
import json
from collections import Counter, defaultdict
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from sage.adapters.supabase import connect
from sage.adapters.supabase.auth import sign_in_token
from sage.adapters.supabase.rules import SupabaseRuleRepository
from sage.adapters.supabase.students import SupabaseStudentRepository
from sage.config import LOCAL_HOSTS, get_settings, is_local
from sage.domain.repositories import AccountNotFound
from sage.ingestion.sources import SourceError
from sage.services.ingest import DryRun, ingest
from sage.services.seed import SEED_FILE, SeedResult, load_seed, seed


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

    sign_in_command = commands.add_parser(
        "sign-in",
        help="Print a one-time link that signs the made-up student in locally",
    )
    sign_in_command.add_argument(
        "--port", type=int, default=3000, help="the local frontend's port"
    )

    ingest_command = commands.add_parser(
        "ingest", help="Read a handbook year's sources into a candidate rulebook"
    )
    ingest_command.add_argument(
        "--year", type=int, required=True, help="the handbook year, such as 2026"
    )
    ingest_command.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="print the report and write nothing to any database",
    )

    args = parser.parse_args(argv)
    if args.command == "seed":
        run_seed(args.user, yes=args.yes)
    elif args.command == "sign-in":
        run_sign_in(args.port)
    elif args.command == "ingest":
        run_ingest(args.year)


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

    client = connect(settings.supabase_url, settings.supabase_secret_key)
    rules, students = SupabaseRuleRepository(client), SupabaseStudentRepository(client)
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
    check_read_back(result)
    print("Read back: her data matches the file.")


def run_sign_in(port: int) -> None:
    settings = get_settings()
    # The link needs no password, so it may only ever sign in to this laptop's Supabase
    if not is_local(settings.supabase_url):
        raise SystemExit(
            "sage sign-in only runs on local Supabase: `make sign-in` points it there"
        )
    client = connect(settings.supabase_url, settings.supabase_secret_key)
    fake_account = json.loads(SEED_FILE.read_text(encoding="utf-8"))["fake_account"]
    account, token = sign_in_token(client, fake_account["email"])
    students = SupabaseStudentRepository(client)
    # Her seed goes on once, so changes made while trying the app survive the next sign-in
    if students.profile(account) is None:
        rules = SupabaseRuleRepository(client)
        check_read_back(seed(rules, students, load_seed(SEED_FILE, account)))
    # Only the link, so a script such as Playwright's setup can read it
    print(f"http://localhost:{port}/?{urlencode({'token_hash': token})}")


def check_read_back(result: SeedResult) -> None:
    if result.student_differences:
        problems = "; ".join(result.student_differences)
        raise SystemExit(f"Her data didn't read back as written: {problems}")


def run_ingest(year: int) -> None:
    try:
        run = ingest(year)
    except SourceError as error:
        raise SystemExit(f"Stopped: {error}") from None
    print(report(run))


def report(run: DryRun) -> str:
    lines = [
        f"sage ingest {run.year}, a dry run: nothing is written to any database",
        "",
        "Rows per table and source",
    ]
    for table, counts in run.rows.items():
        sources = ", ".join(f"{source} {count}" for source, count in counts.items())
        sources = sources or "none, as the year has no such source"
        lines.append(f"  {table:<26} {sources}")
    lines += ["", "Accepted automatically, and flagged by cause"]
    flags: dict[str, Counter] = defaultdict(Counter)
    for reading in run.readings:
        flags[reading.entity][reading.flag or "accepted"] += 1
    for table, counts in flags.items():
        causes = ", ".join(
            f"{cause} {count}" for cause, count in sorted(counts.items())
        )
        lines.append(f"  {table:<26} {causes}")
    translations = run.translations.translations
    refused = [t for t in translations if t.cause]
    read = len(translations) - len(refused)
    lines += [
        "",
        f"Requirements: {len(translations)} distinct printed strings. "
        + f"The grammar read {read} and refused {len(refused)}:",
    ]
    for cause, count in Counter(t.cause for t in refused).most_common():
        drafted = sum(t.drafted for t in refused if t.cause == cause)
        lines.append(
            f"  {cause:<26} {count}: {drafted} drafted, {count - drafted} awaiting a draft"
        )
    lines.append(f"  Model calls in this run: {run.translations.calls}")
    lines += [
        f"  Not kept, as it isn't a rule tree: {p}" for p in run.translations.refused
    ]
    lines.append("")
    lines += [
        f"{wildcard} stands for {', '.join(codes)}, an assumption"
        for wildcard, codes in run.expanded.items()
    ]
    if run.left_out:
        lines.append(f"Left out, as only notes name them: {', '.join(run.left_out)}")
    lines.append(
        "Entries that print no requirement line, read as needing nothing beyond any "
        + f"co-requisite: {', '.join(run.unprinted)}"
    )
    notes: dict[str, list[str]] = defaultdict(list)
    for note in run.notes:
        notes[note.text].append(f"{note.sheet}!{note.cell}")
    lines += [
        f"Timetable note at {', '.join(cells)}: {text}" for text, cells in notes.items()
    ]
    lines += ["", "Checks"]
    for check in run.checks:
        state = f"{len(check.failures)} failed" if check.failures else "passed"
        lines.append(f"  {state}: {check.name}")
        lines += [f"      {f.place}: {f.what}" for f in check.failures]
    return "\n".join(lines)
