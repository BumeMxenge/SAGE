# Runs ATP-1: SAGE's readers, grammar and drafts, and its two approved years, against the labels in
# labels/, and writes one CSV per source to results/ for report.py. It reads the held-out drafts its
# first run made from results/, and calls no model. make atp1 runs it from backend/, with the folders
# it imports from on Python's path.
import csv
import hashlib
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import count_changes
import scoring
import transcripts
from labels.check_labels import NO_ENTRY, SHEETS, Row, clock, read
from scoring import ACCEPTED, NOT_STORED, REVIEWED

from sage.ingestion import (
    complementary,
    grammar,
    handbook,
    sources,
    timetable,
    translate,
)
from sage.ingestion.ingest import DATA, approved_snapshot, review_file
from sage.ingestion.review import Snapshot
from sage.ingestion.transcript import pdf_pages, read_lines
from tests.pdf import pdf_of, split_pages

HERE = Path(__file__).resolve().parent
LABELS = HERE / "labels"
RESULTS = HERE / "results"
# The held-out drafts as translate caches them, and every string the grammar refused with the
# model's reply and what took its place, which translate doesn't keep when a reply isn't a tree
DRAFTS = RESULTS / "drafts.json"
REFUSALS = RESULTS / "refusals.json"
YEARS = (2023, 2026)
# The printed strings of an entry, by its field, with their column on the sheets and their need
TEXTS = {
    "requirement": ("Requirement", "pass"),
    "corequisite": ("Co-requisite", "concurrent"),
}
# Every sheet's CSV: one row per labelled item and field
COLUMNS = (
    "row",
    "item",
    "field",
    "label",
    "sage",
    "match",
    "review",
    "judgement",
    "cause",
    "draft",
)


def main() -> None:
    if not REFUSALS.exists():
        raise SystemExit(
            "The held-out drafts are missing: results/ should hold the first result's drafts.json "
            "and refusals.json, as committed"
        )
    manifests = {year: sources.load(DATA / "sources" / str(year)) for year in YEARS}
    books = {
        year: handbook.Handbook(handbook.pages(manifest.path(manifest.handbook)))
        for year, manifest in manifests.items()
    }
    snapshots = {year: approved_snapshot(year) for year in YEARS}
    seen = {year: decided(year) for year in YEARS}
    sheets = {
        "courses_2023": courses(2023, books[2023], snapshots[2023], seen[2023]),
        "courses_2026": courses(
            2026,
            books[2026],
            snapshots[2026],
            seen[2026],
            (snapshots[2023], seen[2023]),
        ),
        "timetable": timetable_cells(manifests[2026], snapshots[2026]),
        "complementary": workbook_meetings(manifests[2026], seen[2026]),
        "held_out": held_out(books[2026]),
    }
    for name, rows in sheets.items():
        write(name, COLUMNS, rows)
    write(
        "changes",
        (
            "code",
            "field",
            "change",
            "label_2023",
            "label_2026",
            "flag",
            "outcome",
            "judgement",
        ),
        changes(snapshots[2026]),
    )
    write("counts", ("kind", "added", "removed", "changed"), counts(snapshots))
    write("sittings", ("year", "start", "end", "decided"), sittings())
    write(
        "transcripts",
        ("student", "year", "code", "kind", "printed", "read", "outcome"),
        read_back(),
    )
    write("inputs", ("file", "sha256"), inputs(manifests))


def decided(year: int) -> set[str]:
    # The courses a row decided in the year's review covers
    rows = json.loads(review_file(year).read_text(encoding="utf-8"))["rows"]
    return {
        key.removeprefix("courses/")
        for row in rows
        if row["decision"] is not None
        for key in row["covers"]
        if key.startswith("courses/")
    }


def courses(
    year: int,
    book: handbook.Handbook,
    snapshot: Snapshot,
    seen: set[str],
    earlier: tuple[Snapshot, set[str]] | None = None,
) -> list[dict[str, str]]:
    # Each course on the year's sheet: its rule fields against the approved year, and its page and
    # printed text against the handbook reader. In 2026 a field can also be reviewed by a 2023
    # decision it hasn't changed since.
    stored = {c.code: c.model_dump(mode="json") for c in snapshot.rules.courses}
    lines = printed_lines(snapshot)
    before, before_lines, before_seen = (
        (
            {c.code: c.model_dump(mode="json") for c in earlier[0].rules.courses},
            printed_lines(earlier[0]),
            earlier[1],
        )
        if earlier
        else ({}, {}, set())
    )
    rows = []
    for number, label in read(LABELS / f"courses_{year}.xlsx").items():
        code = label["Code"]
        course = stored.get(code)
        if label["Note"] == NO_ENTRY:
            held = course is not None
            review = REVIEWED if code in seen else (ACCEPTED if held else NOT_STORED)
            got = "held" if held else "absent"
            rows.append(
                cell(number, code, "entry", NO_ENTRY, got, not held, review, label)
            )
            continue
        # Whether each field is unchanged since 2023: the rule as stored, and the printed line
        same_rule = (
            course is not None
            and code in before
            and before[code]["entry_rule"] == course["entry_rule"]
        )
        same_line = code in before_lines and before_lines[code] == lines.get(code)
        reviews = {
            field: scoring.course_review(
                field,
                code in seen,
                same_rule if field == "entry_rule" else same_line,
                code in before_seen,
            )
            if course
            else NOT_STORED
            for field in (*scoring.FIELDS, "page", *TEXTS)
        }
        for field, column in scoring.FIELDS.items():
            want = scoring.labelled(label, field)
            got = course[column] if course else None
            match = course is not None and scoring.agrees(field, want, got)
            rows.append(
                cell(number, code, field, want, got, match, reviews[field], label)
            )
        entry = book.entry(code)
        page = int(label["Page"])
        got = entry.page if entry else None
        rows.append(
            cell(number, code, "page", page, got, got == page, reviews["page"], label)
        )
        for field, (column, need) in TEXTS.items():
            read_text = getattr(entry, field) if entry else None
            # The labels write None for an entry that prints no requirement line
            printed = (
                (read_text or "None") if entry and field == "requirement" else read_text
            )
            if field == "corequisite" and not (label[column] or printed):
                continue
            match = entry is not None and scoring.agrees(field, label[column], printed)
            rows.append(
                cell(
                    number,
                    code,
                    field,
                    label[column],
                    printed,
                    match,
                    reviews[field],
                    label,
                    grammar_cause(read_text, need),
                )
            )
    return rows


def printed_lines(snapshot: Snapshot) -> dict[str, str]:
    # Each course's printed requirement line, as the year's review showed it
    return {r.key: r.printed for r in snapshot.readings if r.entity == "courses"}


def grammar_cause(text: str | None, need: translate.Need) -> str:
    # What the grammar makes of a string the reader read: read, or the cause it refuses it for
    if text is None:
        return ""
    try:
        grammar.read(text, need)
    except grammar.Refused as refused:
        return refused.cause
    return "read"


def timetable_cells(
    manifest: sources.Manifest, snapshot: Snapshot
) -> list[dict[str, str]]:
    # Each sampled cell against the meeting the reader reads there. A meeting of a course the
    # rulebook doesn't hold, such as Labs D27's EEE2041F, is never stored, and no row shows one.
    source = manifest.timetable
    cells = scoring.by_cell(
        timetable.read(manifest.path(source), source.sheets).printed
    )
    held = {course.code for course in snapshot.rules.courses}
    rows = []
    for number, label in read(LABELS / "timetable.xlsx").items():
        item = f"{label['Sheet']}!{label['Cell']}"
        meeting = cells.get((label["Sheet"], label["Cell"]))
        review = ACCEPTED if meeting and held & set(meeting.codes) else NOT_STORED
        codes = sorted(code.strip() for code in str(label["Course"]).split(","))
        found: dict[str, tuple[Any, Any]] = {
            "course": (", ".join(codes), meeting and ", ".join(sorted(meeting.codes)))
        }
        if label["Day"] is not None:
            found |= {
                "day": (label["Day"], meeting and scoring.day_name(meeting.day)),
                "start": (
                    clock(label["Start"]),
                    meeting and timetable.PERIODS[meeting.first][0],
                ),
                "end": (
                    clock(label["End"]),
                    meeting and timetable.PERIODS[meeting.last][1],
                ),
                "term": (label["Term"], meeting and meeting.semester),
            }
        rows += [
            cell(number, item, field, want, got, want == got, review, label)
            for field, (want, got) in found.items()
        ]
    return rows


def workbook_meetings(
    manifest: sources.Manifest, seen: set[str]
) -> list[dict[str, str]]:
    # Each sampled row of the workbook's Meetings sheet against the meeting the reader reads from it,
    # then its course's handbook and pages. A decided requirement row shows those, but no row shows
    # a meeting.
    source = manifest.complementary
    workbook = complementary.read(manifest.path(source), source)
    meetings = {meeting.row: meeting for meeting in workbook.meetings}
    offerings = {offering.code: offering for offering in workbook.offerings}
    rows = []
    for number, label in read(LABELS / "complementary.xlsx").items():
        meeting = meetings[int(label["Row"])]
        if meeting.code != label["Course"]:
            raise SystemExit(
                f"Meetings row {label['Row']} holds {meeting.code} for the reader, but "
                f"complementary.xlsx names {label['Course']}"
            )
        offering = offerings[meeting.code]
        days = (
            [day.strip() for day in str(label["Days"]).split(",")]
            if label["Days"]
            else []
        )
        their_days = [scoring.WORKBOOK_DAYS[day] for day in meeting.days]
        start = clock(label["Start"]) if label["Start"] else None
        end = clock(label["End"]) if label["End"] else None
        book, page = label["Book"], int(label["Page"])
        shown = scoring.course_review("book", meeting.code in seen)
        found = [
            (
                "days",
                ", ".join(days),
                ", ".join(their_days),
                set(days) == set(their_days),
                ACCEPTED,
            ),
            ("start", start, meeting.start, start == meeting.start, ACCEPTED),
            ("end", end, meeting.end, end == meeting.end, ACCEPTED),
            (
                "kind",
                label["Kind"],
                meeting.kind,
                label["Kind"] == meeting.kind,
                ACCEPTED,
            ),
            (
                "book",
                book,
                offering.handbook,
                scoring.BOOKS[book] == offering.handbook,
                shown,
            ),
            ("page", page, offering.pages, scoring.within(page, offering.pages), shown),
        ]
        item = f"Meetings row {label['Row']}, {meeting.code}"
        rows += [
            cell(number, item, field, want, got, match, review, label)
            for field, want, got, match, review in found
            if field != "kind" or want is not None
        ]
    return rows


def held_out(book: handbook.Handbook) -> list[dict[str, str]]:
    # Each held-out entry from the 2026 handbook, its strings through the grammar and, where it
    # refuses one, the first result's draft. Each string is scored on its own: one the grammar reads
    # is accepted without review, and a refused one is reviewed, as is the page of an entry with one.
    labels = read(LABELS / "held_out.xlsx")
    entries: dict[int, handbook.Entry | None] = {}
    stops: dict[int, str] = {}
    for number, label in labels.items():
        try:
            entries[number] = book.entry(label["Code"])
        except sources.SourceError as error:
            stops[number] = f"the reader stops: {error}"  # so a person must handle it
    strings = [
        (getattr(entry, field), need)
        for entry in entries.values()
        if entry
        for field, (_, need) in TEXTS.items()
        if getattr(entry, field)
    ]
    translated = translate.translate(strings, DRAFTS, None)
    on_record(translated)
    found = {(t.printed, t.need): t for t in translated.translations}
    rows = []
    for number, label in labels.items():
        code, page = label["Code"], int(label["Page"])
        entry = entries.get(number)
        if entry is None:
            # SAGE holds nothing from an entry its reader doesn't find, and a person must handle
            # one it stops on
            got = stops.get(number, "not found")
            review = REVIEWED if number in stops else NOT_STORED
            wanted = {
                "page": page,
                "requirement": label["Requirement"],
                "requirement_tree": scoring.tree(label["Requirement tree"]),
            }
            for field, want in wanted.items():
                rows.append(cell(number, code, field, want, got, False, review, label))
            continue
        parts: dict[str, translate.Translation | None] = {}
        for field, (_, need) in TEXTS.items():
            text = getattr(entry, field)
            parts[field] = found[scoring.evened(text), need] if text else None
        refused = any(part and part.cause for part in parts.values())
        review = REVIEWED if refused else ACCEPTED
        rows.append(
            cell(
                number,
                code,
                "page",
                page,
                entry.page,
                entry.page == page,
                review,
                label,
            )
        )
        for field, (column, _) in TEXTS.items():
            part, read_text = parts[field], getattr(entry, field)
            # The labels write None for an entry that prints no requirement line
            printed = (read_text or "None") if field == "requirement" else read_text
            if field == "corequisite" and not (label[column] or printed):
                continue
            review = REVIEWED if part and part.cause else ACCEPTED
            reading = (part.cause or "read") if part else ""
            match = scoring.agrees(field, label[column], printed)
            rows.append(
                cell(
                    number,
                    code,
                    field,
                    label[column],
                    printed,
                    match,
                    review,
                    label,
                    reading,
                )
            )
            want = scoring.tree(label[f"{column} tree"])
            got = translate.DRAFT.dump_python(part.tree, mode="json") if part else None
            draft = (
                ("kept" if part.drafted else "not kept") if part and part.cause else ""
            )
            match = scoring.same_tree(want, got)
            rows.append(
                cell(
                    number,
                    code,
                    f"{field}_tree",
                    want,
                    got,
                    match,
                    review,
                    label,
                    reading,
                    draft,
                )
            )
    return rows


def on_record(translated: translate.Translations) -> None:
    # The first run recorded every refused string with its cause, the model's reply and what took
    # its place. Each refused string must be on that record, so none was left undrafted.
    held = json.loads(REFUSALS.read_text(encoding="utf-8"))
    recorded = {(r["need"], r["printed"]) for r in held}
    missing = [
        t.printed
        for t in translated.translations
        if t.cause and (t.need, t.printed) not in recorded
    ]
    if missing:
        raise SystemExit(
            f"{len(missing)} held-out strings the grammar refuses aren't on the record of drafts, "
            "so the reader's wording has changed since. Drafting them would be a retest, on a "
            "branch of its own"
        )


def changes(snapshot: Snapshot) -> list[dict[str, str]]:
    # Every labelled change between the two course sheets, and every flagged 2026 delta on their
    # courses, by scoring's rules
    before = by_code(read(LABELS / "courses_2023.xlsx"))
    after = by_code(read(LABELS / "courses_2026.xlsx"))
    deltas = {
        d.entity_key: d for d in snapshot.rules.handbook_deltas if d.entity == "courses"
    }
    return [
        row
        for code in sorted(before.keys() | after.keys())
        for row in scoring.course_changes(
            code, before.get(code), after.get(code), deltas.get(code)
        )
    ]


def by_code(rows: dict[int, Row]) -> dict[str, Row]:
    return {row["Code"]: row for row in rows.values()}


def counts(snapshots: dict[int, Snapshot]) -> list[dict[str, str]]:
    # count_changes.py's table of what changed between the two approved years, then the conveners,
    # which it counts apart, as they aren't rules
    old, new = snapshots[2023].rules, snapshots[2026].rules
    before, after = count_changes.kinds(old), count_changes.kinds(new)
    rows = [
        dict(
            zip(
                ("kind", "added", "removed", "changed"),
                (name, *map(str, count_changes.changes(before[name], after[name]))),
                strict=True,
            )
        )
        for name in before
    ]
    moved = count_changes.changes(
        count_changes.conveners(old), count_changes.conveners(new)
    )
    return [
        *rows,
        {"kind": "Conveners", "added": "", "removed": "", "changed": str(moved[2])},
    ]


def sittings() -> list[dict[str, str]]:
    # CP2's sittings, each with when it began and last saved and the rows it decided
    return [
        {
            "year": str(year),
            "start": sitting["start"],
            "end": sitting["end"],
            "decided": str(sitting["decided"]),
        }
        for year in YEARS
        for sitting in json.loads(review_file(year).read_text(encoding="utf-8"))[
            "sittings"
        ]
    ]


def read_back() -> list[dict[str, str]]:
    # Each made-up record printed as tests/pdf.py prints PDFs, then read by SAGE's transcript reader
    rows = []
    for made in transcripts.records():
        transcript = read_lines(pdf_pages(pdf_of(split_pages(made.text))), made.number)
        rows += scoring.read_back(
            made.number, made.rows, transcript.lines, transcript.warnings
        )
    return rows


def inputs(manifests: dict[int, sources.Manifest]) -> list[dict[str, str]]:
    # The SHA-256 of every file the run read, which ties the result to them
    root = DATA.parent
    paths = [
        *(LABELS / name for name in SHEETS),
        *(
            manifest.path(source)
            for manifest in manifests.values()
            for source in (
                manifest.handbook,
                manifest.timetable,
                manifest.complementary,
            )
            if source
        ),
        *(DATA / "rules" / str(year) / "rulebook.json" for year in YEARS),
        *(review_file(year) for year in YEARS),
        DRAFTS,
        REFUSALS,
    ]
    return [
        {
            "file": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in paths
        if path.exists()
    ]


def cell(
    number: int,
    item: str,
    field: str,
    label_value: Any,
    sage_value: Any,
    match: bool,
    review: str,
    label: Row,
    cause: str = "",
    draft: str = "",
) -> dict[str, str]:
    return {
        "row": str(number),
        "item": item,
        "field": field,
        "label": scoring.shown(label_value),
        "sage": scoring.shown(sage_value),
        "match": "yes" if match else "no",
        "review": review,
        "judgement": "yes" if scoring.judgement(label) else "no",
        "cause": cause,
        "draft": draft,
    }


def write(name: str, columns: Sequence[str], rows: Iterable[dict[str, str]]) -> None:
    rows = list(rows)
    with (RESULTS / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"results/{name}.csv: {len(rows)} rows")


if __name__ == "__main__":
    main()
