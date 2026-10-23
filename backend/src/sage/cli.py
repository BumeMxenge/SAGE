# Command-line entry point: `uv run sage <command>`, e.g. `uv run sage seed --user <account id>`
import argparse
import json
import subprocess
import tempfile
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import get_args
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from pydantic import JsonValue

from sage.config import get_settings, is_local
from sage.ingestion.electives import LANGUAGES, TABS
from sage.ingestion.ingest import (
    Candidate,
    Sitting,
    YearLoaded,
    approve,
    approved_snapshot,
    load,
    review_file,
    review_year,
)
from sage.ingestion.review import DECISIONS, TREES, Review, ReviewRow, tree_fault
from sage.ingestion.sources import SourceError
from sage.shared.language_model import (
    ModelUnavailable,
    Response,
    Said,
    Schema,
    Tokens,
    Tool,
    ToolResult,
)
from sage.shared.openai import OpenAIModel
from sage.shared.repositories import AccountNotFound, YearInUse
from sage.shared.rules import DeltaTable, RuleSet
from sage.shared.seed import (
    SEED_FILE,
    SeedResult,
    YearNotLoaded,
    load_seed,
    require_loaded,
    seed,
)
from sage.shared.supabase.auth import sign_in_token
from sage.shared.supabase.client import Client, connect
from sage.shared.supabase.rules import SupabaseRuleRepository
from sage.shared.supabase.students import SupabaseStudentRepository
from sage.shared.wording import in_words


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
        "ingest",
        help="Read a handbook year's sources, compare them with the latest approved year and "
        "write what needs a person to data/rules/<year>/review.json",
    )
    ingest_command.add_argument(
        "--year", type=int, required=True, help="the handbook year, such as 2026"
    )
    ingest_command.add_argument(
        "--draft",
        action="store_true",
        help="ask the language model for every draft not cached yet, a rule tree for each refused "
        "string and each complementary course's tab and summary, and cache them",
    )

    review_command = commands.add_parser(
        "review",
        help="Decide a year's pending review rows one at a time in the terminal, each saved to "
        "data/rules/<year>/review.json as it's made",
    )
    review_command.add_argument(
        "--year", type=int, required=True, help="the handbook year, such as 2026"
    )

    approve_command = commands.add_parser(
        "approve",
        help="Approve a year whose review has nothing pending, writing "
        "data/rules/<year>/rulebook.json",
    )
    approve_command.add_argument(
        "--year", type=int, required=True, help="the handbook year, such as 2026"
    )

    load_command = commands.add_parser(
        "load",
        help="Write an approved year, data/rules/<year>/rulebook.json, to the database "
        "SUPABASE_URL names",
    )
    load_command.add_argument(
        "--year", type=int, required=True, help="the handbook year, such as 2026"
    )
    load_command.add_argument(
        "--replace", action="store_true", help="replace the year if it's stored already"
    )
    load_command.add_argument(
        "--yes", action="store_true", help="write to a hosted project without asking"
    )

    args = parser.parse_args(argv)
    if args.command == "seed":
        run_seed(args.user, yes=args.yes)
    elif args.command == "sign-in":
        run_sign_in(args.port)
    elif args.command == "ingest":
        run_ingest(args.year, draft=args.draft)
    elif args.command == "review":
        run_review(args.year)
    elif args.command == "approve":
        run_approve(args.year)
    elif args.command == "load":
        run_load(args.year, replace=args.replace, yes=args.yes)


def project(yes: bool) -> tuple[Client, str]:
    # The project SUPABASE_URL names, and its host. Anywhere but this laptop is real data, so
    # writing there needs a yes.
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise SystemExit(
            "Set SUPABASE_URL and SUPABASE_SECRET_KEY first: `make seed` and `make load` do "
            "it for local Supabase, and backend/.env holds the hosted project's"
        )
    host = urlsplit(settings.supabase_url).hostname or settings.supabase_url
    if not is_local(settings.supabase_url) and not yes:
        answer = input(f"This writes to {host}. Type yes to continue: ")
        if answer.strip().lower() != "yes":
            raise SystemExit("Nothing written")
    return connect(settings.supabase_url, settings.supabase_secret_key), host


def run_seed(account: UUID, *, yes: bool) -> None:
    # A bad file stops here, before anything is written
    data = load_seed(SEED_FILE, account)
    client, host = project(yes)
    rules, students = SupabaseRuleRepository(client), SupabaseStudentRepository(client)
    try:
        result = seed(rules, students, data)
    except AccountNotFound:
        raise SystemExit(
            f"No account {account} on {host}. Sign in once, then copy the id from "
            "Authentication > Users in the Supabase dashboard"
        ) from None
    except YearNotLoaded as missing:
        year = missing.args[0]
        raise SystemExit(
            f"{host} doesn't hold the approved {year} rules her plans use: "
            f"sage load --year {year} loads them"
        ) from None

    print(f"Seeded {SEED_FILE.name} onto account {account} on {host}:")
    for table, count in result.written.items():
        print(f"  {table}: {count}")
    check_read_back(result)
    print("Read back: her data matches the file.")


def run_load(year: int, *, replace: bool, yes: bool) -> None:
    try:
        snapshot = approved_snapshot(year)
    except FileNotFoundError:
        raise SystemExit(
            f"{year} isn't approved yet: sage approve --year {year} writes its snapshot"
        ) from None
    client, host = project(yes)
    try:
        written = load(snapshot, SupabaseRuleRepository(client), replace=replace)
    except YearLoaded:
        raise SystemExit(
            f"{host} holds {year} differently from its snapshot: "
            f"sage load --year {year} --replace replaces it"
        ) from None
    except YearInUse:
        raise SystemExit(
            f"A student's plan or chat on {host} uses {year}, so the database won't remove it"
        ) from None
    if not written:
        print(
            f"{host} holds {year} exactly as its snapshot already, so it's left as it is"
        )
        return
    print(f"Loaded {year}'s approved snapshot onto {host}:")
    for table in RuleSet.model_fields:
        print(f"  {table}: {len(getattr(snapshot.rules, table))}")


def local_client() -> Client:
    # A sign-in link needs no password, so it may only ever sign in to this laptop's Supabase.
    # sage sign-in and make sign-in-new's script both start here.
    settings = get_settings()
    if not is_local(settings.supabase_url):
        raise SystemExit(
            "A sign-in link only runs on local Supabase: make sign-in and make sign-in-new "
            "point there"
        )
    return connect(settings.supabase_url, settings.supabase_secret_key)


def link(token: str, port: int) -> str:
    # The local frontend's address that swaps the token for a session
    return f"http://localhost:{port}/?{urlencode({'token_hash': token})}"


def run_sign_in(port: int) -> None:
    client = local_client()
    rules, students = SupabaseRuleRepository(client), SupabaseStudentRepository(client)
    file = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    try:
        # Her plans need their year's rules, so nothing is written until they're loaded, not even
        # her account
        require_loaded(rules, {row["period"] for row in file["plan_sets"]})
    except YearNotLoaded as missing:
        raise SystemExit(
            f"Local Supabase doesn't hold the approved {missing.args[0]} rules her plans use: "
            "make load loads them"
        ) from None
    account, token = sign_in_token(client, file["fake_account"]["email"])
    # Her seed goes on once, so changes made while trying the app survive the next sign-in
    if students.profile(account) is None:
        check_read_back(seed(rules, students, load_seed(SEED_FILE, account)))
    # Only the link, so a script such as Playwright's setup can read it
    print(link(token, port))


def check_read_back(result: SeedResult) -> None:
    if result.student_differences:
        problems = "; ".join(result.student_differences)
        raise SystemExit(f"Her data didn't read back as written: {problems}")


class Metered:
    # SAGE's model as sage ingest --draft asks it, adding up every call's tokens for the cost line
    def __init__(self, model: OpenAIModel) -> None:
        self._model = model
        self.model = model.model
        self.tokens = Tokens()

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Said | Response | ToolResult],
        schema: Schema | None = None,
        tools: Sequence[Tool] = (),
        effort: str | None = None,
    ) -> Response:
        reply = self._model.respond(instructions, conversation, schema, tools, effort)
        self.tokens += reply.tokens
        return reply

    @property
    def cost(self) -> float:
        return self._model.cost(self.tokens)


def run_ingest(year: int, *, draft: bool) -> None:
    model = None
    if draft:
        settings = get_settings()
        if not settings.openai_api_key:
            raise SystemExit("Add OPENAI_API_KEY to backend/.env first")
        model = Metered(OpenAIModel(settings.openai_api_key, settings.language_model))
    try:
        run, review = review_year(year, model)
    except SourceError as error:
        raise SystemExit(f"Stopped: {error}") from None
    except ModelUnavailable as error:
        raise SystemExit(
            f"Stopped, as the model can't be reached ({error}). Drafts already cached are "
            + "kept: run it again to carry on"
        ) from None
    print(report(run))
    print(review_report(review))
    if model is not None:
        tokens = model.tokens
        print(
            f"\nDrafting with {model.model}: {tokens.fresh:,} tokens in, "
            + f"{tokens.cached:,} read from the provider's cache, {tokens.written:,} written "
            + f"to it and {tokens.output:,} out, USD {model.cost:.4f}"
        )


def report(run: Candidate) -> str:
    lines = [
        f"sage ingest {run.year}: nothing is written to any database",
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
    lines.append(
        f"  Model calls in this run: {run.translations.calls}. "
        + f"Drafts copied from an earlier year: {run.translations.reused}"
    )
    lines += [
        f"  Not kept, as it isn't a rule tree: {p}" for p in run.translations.refused
    ]
    offered = sum(r.flag == "model_written" for r in run.readings)
    if offered:
        written = run.written
        lines += [
            "",
            f"Electives: {offered} complementary courses, {len(written.electives)} with a tab "
            + f"and summary drafted and {offered - len(written.electives)} awaiting a draft",
            f"  Model calls in this run: {written.calls}. "
            + f"Drafts copied from an earlier year: {written.reused}",
            *(f"  Not kept: {problem}" for problem in written.refused),
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
    if run.previous:
        year = run.previous.year
        lines.append(
            f"Requirements printed in {year}'s words keep {year}'s approved rules: "
            + f"{len(run.carried)} courses"
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
        lines += [
            f"      {f.place}: {f.what}, reported as settled" for f in check.reported
        ]
    return "\n".join(lines)


def review_report(review: Review) -> str:
    if review.compared_with is None:
        lines = ["", f"No approved year before {review.year}, so every row is new"]
    else:
        lines = [
            "",
            f"Compared with the approved {review.compared_with}: {review.carried} rows "
            + "carried over unchanged",
        ]
    lines.append("Rows added, changed and removed, and how many of each are for review")
    changes: dict[str, Counter] = defaultdict(Counter)
    for delta in review.deltas:
        change = (
            "added"
            if delta.old_value is None
            else "removed"
            if delta.new_value is None
            else "changed"
        )
        changes[delta.entity][change] += 1
        changes[delta.entity][f"{change} for review"] += bool(delta.flag)
    for table in get_args(DeltaTable):
        counts = changes[table]
        parts = [
            f"{change} {counts[change]}"
            + (f" ({n} for review)" if (n := counts[f"{change} for review"]) else "")
            for change in ("added", "changed", "removed")
        ]
        lines.append(f"  {table:<26} {', '.join(parts)}")
    causes = Counter(cause for row in review.rows for cause in row.causes)
    lines += [
        "",
        f"data/rules/{review.year}/review.json: {len(review.rows)} rows for you, by cause:",
    ]
    lines += [f"  {cause:<26} {count}" for cause, count in causes.most_common()]
    pending = review.pending
    lines.append(f"Decided {len(review.rows) - len(pending)}, pending {len(pending)}")
    if review.returned:
        lines.append(
            "Returned to pending, as the reading they were decided on has changed: "
            + ", ".join(review.returned)
        )
    if review.problems:
        lines.append("Decisions that can't be used yet:")
        lines += [
            f"  {problem.row or 'the year as decided'}: {problem.text}"
            for problem in review.problems
        ]
    return "\n".join(lines)


def run_approve(year: int) -> None:
    try:
        review, snapshot = approve(year)
    except SourceError as error:
        raise SystemExit(f"Stopped: {error}") from None
    if snapshot is None:
        print(review_report(review))
        raise SystemExit(
            f"Not approved, as rows are pending: sage review --year {year} decides them"
        )
    rules = snapshot.rules
    rows = sum(
        len(getattr(rules, table))
        for table in RuleSet.model_fields
        if table != "handbook_deltas"
    )
    settled = Counter(
        "accepted automatically"
        if delta.flag is None
        else "corrected"
        if delta.corrected_value is not None
        else "rejected"
        if delta.approved is False
        else "accepted"
        for delta in rules.handbook_deltas
    )
    print(
        f"Approved {year}: data/rules/{year}/rulebook.json holds {rows} rows and "
        + f"{len(rules.handbook_deltas)} changes, "
        + ", ".join(f"{count} {how}" for how, count in settled.most_common())
    )


# The keys that decide a row, and the decision each makes
KEYS = {"a": "accept", "c": "correct", "r": "reject"}


def run_review(year: int) -> None:
    try:
        candidate, review = review_year(year)
    except SourceError as error:
        raise SystemExit(f"Stopped: {error}") from None
    if not review.pending:
        print(
            f"Nothing is pending in {year}'s review: sage approve --year {year} approves it"
        )
        return
    sitting = Sitting(candidate, review_file(year), lambda: datetime.now().astimezone())
    walk(sitting, input, open_in_code)


def walk(
    sitting: Sitting, ask: Callable[[str], str], edit: Callable[[Path], None]
) -> None:
    # Shows each pending row in turn until the last or q, then the sitting's minutes
    review = sitting.review
    pending = [row for row in review.rows if row.id in review.pending]
    with tempfile.TemporaryDirectory() as folder:
        try:
            for number, row in enumerate(pending, 1):
                problems = [p.text for p in sitting.review.problems if p.row == row.id]
                heading = f"Row {number} of {len(pending)}"
                print(shown(row, heading, problems, review.compared_with))
                if not settle(sitting, row, ask, edit, Path(folder)):
                    break
        except (KeyboardInterrupt, EOFError):
            print()
    sittings = sitting.end()
    minutes, decided = sittings[-1]
    review = sitting.review
    print(f"\nThis sitting took {minutes:.0f} minutes and decided {decided} rows.")
    print(
        f"{review.year}'s review: {len(sittings)} sittings over "
        + f"{sum(m for m, _ in sittings):.0f} minutes, and {len(review.pending)} of "
        + f"{len(review.rows)} rows pending"
    )
    for problem in review.problems:
        if problem.row is None:
            print(f"Failing on the year as decided: {problem.text}")


def settle(
    sitting: Sitting,
    row: ReviewRow,
    ask: Callable[[str], str],
    edit: Callable[[Path], None],
    folder: Path,
) -> bool:
    # One row's decision, asked for until it's kept or the row is skipped; False when the person quits
    allowed = DECISIONS[row.kind]
    choices = [f"{key} {word}" for key, word in KEYS.items() if word in allowed]
    prompt = ", ".join([*choices, "s skip", "q quit"]) + ": "
    while True:
        key = ask(prompt).strip().lower()
        if key in ("s", "q"):
            return key == "s"
        decision = KEYS.get(key)
        if decision not in allowed:
            continue
        corrected = None
        if decision == "correct":
            corrected = (
                corrected_elective(row, ask)
                if row.kind == "elective"
                else corrected_tree(row, folder, edit)
            )
            if corrected is None:
                continue
        problems = sitting.decide(row.id, decision, corrected)
        if problems and all(problem.note for problem in problems):
            print(*(f"  {problem.text}" for problem in problems), sep="\n")
            note = ask("Note saying why it stands, or Enter to choose again: ").strip()
            if not note:
                continue
            problems = sitting.decide(row.id, decision, corrected, note)
        if not problems:
            return True
        print(*(f"  Not kept: {problem.text}" for problem in problems), sep="\n")


def corrected_tree(
    row: ReviewRow, folder: Path, edit: Callable[[Path], None]
) -> JsonValue:
    # The tree saved in the editor, which opens filled with the draft and reopens with the error at
    # the top until what's saved is a tree of the row's kind. None when the file is saved empty.
    path = folder / f"{row.id.replace('/', '-')}.jsonc"
    start = row.new if row.corrected is None else row.corrected
    text, error = json.dumps(start, indent=2, ensure_ascii=False), None
    while True:
        header = [
            f"// {row.id}: {row.printed}",
            "// Save and close this tab to use the tree below, or empty the file to choose again.",
        ]
        if error:
            header.append(f"// Not used: {error}")
        path.write_text("\n".join([*header, text]) + "\n", encoding="utf-8")
        edit(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        text = "\n".join(line for line in lines if not line.lstrip().startswith("//"))
        text = text.strip()
        if not text:
            return None
        try:
            tree = json.loads(text)
        except json.JSONDecodeError as problem:
            error = f"this isn't JSON: {problem}"
            continue
        error = tree_fault(row.kind, tree)
        if error is None:
            return tree


def corrected_elective(row: ReviewRow, ask: Callable[[str], str]) -> JsonValue:
    # The tab picked from the numbered list, unless the row is a language option's, whose tab is
    # fixed, then the summary as typed. Enter keeps either as drafted. None when neither changed, to
    # choose again.
    value = dict(row.new)
    if not row.language:
        tabs = [tab for tab in TABS if tab != LANGUAGES]
        numbered = {str(n): tab for n, tab in enumerate(tabs, 1)}
        print(*(f"  {n} {tab}" for n, tab in numbered.items()), sep="\n")
        while (picked := ask(f"Tab, or Enter to keep {value['tab']}: ").strip()) and (
            picked not in numbered
        ):
            continue
        if picked:
            value["tab"] = numbered[picked]
    if summary := ask("Summary, or Enter to keep it: ").strip():
        value["summary"] = summary
    return None if value == row.new else value


def open_in_code(path: Path) -> None:
    # Opens a file in VS Code and waits until its tab is closed
    try:
        subprocess.run(["code", "--wait", str(path)], check=True)
    except FileNotFoundError:
        raise SystemExit(
            "There's no code command: in VS Code, run Shell Command: Install 'code' command in "
            "PATH"
        ) from None


def shown(row: ReviewRow, heading: str, problems: list[str], before: int | None) -> str:
    # A row as a person decides it: why it's here, what it covers, the print, and each value in
    # plain words beside its JSON
    lines = ["", f"{heading}: {row.id}", f"Causes: {', '.join(row.causes)}"]
    if row.mark:
        lines.append(
            "Mark: the words print a DP, which models have read as a pass, so read the "
            + "draft closely"
        )
    if row.failures:
        lines += ["Failed checks:", *(f"  {text}" for text in row.failures)]
    if row.covers:
        lines += [
            "Covers:",
            *(f"  {key} ({place})" for key, place in row.covers.items()),
        ]
    lines.append(f"Printed: {row.printed}")
    if row.kind not in ("check", "no_entry"):
        approved = f"{before} approved" if before else "Approved before"
        if not row.old:
            lines.append(f"{approved}: nothing")
        for key, value in row.old.items():
            lines += [f"{approved}, for {key}:", *_described(row.kind, key, value)]
        lines += ["Read now:", *_described(row.kind, None, row.new)]
    lines += [f"Not usable yet: {text}" for text in problems]
    return "\n".join(lines)


def _described(kind: str, key: str | None, value: JsonValue) -> list[str]:
    # A value in plain words, then as JSON
    if value is None:
        return ["  nothing: it's gone" if kind == "removal" else "  no requirement"]
    words = None
    if kind in TREES:
        words = in_words(TREES[kind].validate_python(value))
    elif kind == "equivalence":
        words = f"{value['course_code']} counts as {value['counts_as']}"
    elif kind == "elective":
        words = (
            f"on the {value['tab']} tab: {value['summary']}"
            if value["summary"]
            else "nothing drafted yet"
        )
    elif key and key.startswith("courses/"):
        entry = value["entry_rule"]
        rule = in_words(
            None if entry is None else TREES["requirement"].validate_python(entry)
        )
        words = f"{value['code']} {value['name']}, needing {rule}"
    elif key and key.startswith("course_group_members/"):
        words = f"{value['course_code']} in {value['group_key']}"
    json_line = f"  {json.dumps(value, ensure_ascii=False)}"
    return [f"  {words}", json_line] if words else [json_line]
