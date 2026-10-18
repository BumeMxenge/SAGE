# Ingests one handbook year into a candidate rulebook, writing nothing to any database. It checks the
# year's sources against their manifest, reads each, translates the printed requirements, grammar
# first, and checks the sources against each other. A requirement printed in the words the latest
# approved year before it printed keeps that year's approved rule. Every row keeps where it was
# printed and why a person must look at it. review_year writes the rows a person must decide,
# approve writes the approved year once none is pending, and load writes that to a database.
import json
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from pydantic import JsonValue

from sage.domain.base import Row
from sage.domain.drafting import Drafter
from sage.domain.repositories import RuleRepository
from sage.domain.rules import (
    TERM_BY_SUFFIX,
    AllOf,
    Course,
    EntryRule,
    HandbookVersion,
    Refer,
    RuleSet,
)
from sage.ingestion import (
    checks,
    complementary,
    curricula,
    equivalences,
    handbook,
    sources,
    timetable,
    translate,
)
from sage.ingestion.names import title_case
from sage.ingestion.review import Problem, Review, Snapshot, compare

# Four folders up from this file: the repo root, as for the seed file
DATA = Path(__file__).resolve().parents[4] / "data"
# Each approved year's snapshot, as data/rules/<year>/ holds it
SNAPSHOT = "rulebook.json"
WORKBOOK = "complementary workbook"


class YearLoaded(Exception):
    # The database holds the year already, and loading it again would replace it
    pass


class Candidate(Row):
    year: int
    rules: RuleSet
    readings: tuple[sources.Reading, ...]
    # Each table's rows by the source they came from
    rows: dict[str, dict[str, int]]
    translations: translate.Translations
    checks: tuple[checks.Check, ...]
    # Each wildcard and the courses it stands for
    expanded: dict[str, tuple[str, ...]]
    # Codes only a curriculum's notes name, with no entry to read
    left_out: tuple[str, ...]
    # Every code the handbook prints an entry for, in any department
    entries: frozenset[str]
    # Entries that print no requirement line, read like a printed "None"
    unprinted: tuple[str, ...]
    notes: tuple[timetable.Note, ...]
    # The latest year approved before this one, which this year is compared with
    previous: Snapshot | None
    # Courses whose requirement is printed in words that year printed, so keep its approved rule
    carried: tuple[str, ...]


def ingest(year: int, drafter: Drafter | None = None, data: Path = DATA) -> Candidate:
    manifest = sources.load(data / "sources" / str(year))
    previous = _latest_approved(year, data)
    book = handbook.Handbook(handbook.pages(manifest.path(manifest.handbook)))
    department = next(
        section
        for section in manifest.handbook.passages
        if section.section == manifest.department
    )
    read = curricula.read(book, department, year, manifest.department)
    workbook = (
        complementary.read(
            manifest.path(manifest.complementary), manifest.complementary
        )
        if manifest.complementary
        else None
    )
    offerings = workbook.offerings if workbook else ()
    # A course the faculty handbook prints is read from the handbook, not the workbook's copy
    wanted = read.scope | {
        o.code for o in offerings if o.handbook == manifest.handbook.title
    }
    entries = {code: entry for code in sorted(wanted) if (entry := book.entry(code))}
    typed = [o for o in offerings if o.code not in entries]
    listed = {row.code for row in read.listed}

    strings = [(e.requirement, "pass") for e in entries.values() if e.requirement]
    strings += [
        (e.corequisite, "concurrent") for e in entries.values() if e.corequisite
    ]
    strings += [
        (o.requirement, "pass")
        for o in typed
        if o.requirement != complementary.NOT_STATED
    ]
    # Every year's cached drafts, in year order, as each folder is named by its year
    caches = sorted((data / "rules").glob("*/drafts.json"))
    translated = translate.translate(
        strings,
        data / "rules" / str(year) / "drafts.json",
        drafter,
        [cache for cache in caches if int(cache.parent.name) < year],
    )
    found = {(t.printed, t.need): t for t in translated.translations}

    def translation(printed: str | None, need: str) -> translate.Translation | None:
        return found[" ".join(printed.split()), need] if printed else None

    # Each requirement the previous approved year printed, by its words, and the rule it approved
    approved: dict[str, EntryRule | None] = {}
    if previous:
        rules = {course.code: course.entry_rule for course in previous.rules.courses}
        approved = {
            r.printed: rules[r.key] for r in previous.readings if r.entity == "courses"
        }
    courses, readings, carried = [], list(read.readings), []

    def settle(
        code: str,
        place: str,
        printed: str,
        rule: EntryRule | None,
        parts: list[translate.Translation],
    ) -> EntryRule | None:
        # Words the previous approved year printed keep the rule it approved, unflagged. Other words
        # keep the rule read now, flagged with the grammar's cause where it refused a part.
        cause = next((p.cause for p in parts if p.cause), None)
        if printed in approved:
            carried.append(code)
            rule, cause = approved[printed], None
        readings.append(
            sources.Reading(
                entity="courses", key=code, place=place, printed=printed, flag=cause
            )
        )
        return rule

    for code, entry in entries.items():
        parts = [
            t
            for t in (
                translation(entry.requirement, "pass"),
                translation(entry.corequisite, "concurrent"),
            )
            if t
        ]
        printed = _printed(entry.requirement, entry.corequisite)
        courses.append(
            Course(
                handbook_year=year,
                code=code,
                name=entry.name,
                credits=entry.credits,
                nqf_level=entry.nqf_level,
                term=entry.term or TERM_BY_SUFFIX[code[-1]],
                entry_rule=settle(
                    code, f"p. {entry.page}", printed, _rule(parts), parts
                ),
                convener=entry.convener,
            )
        )
    for offering in typed:
        # The workbook's "Not stated in course entry." is a refer leaf, as it doesn't mean there's
        # no requirement; any other wording was translated
        not_stated = offering.requirement == complementary.NOT_STATED
        parts = (
            []
            if not_stated
            else [found[" ".join(offering.requirement.split()), "pass"]]
        )
        rule = Refer(refer=offering.requirement) if not_stated else _rule(parts)
        place = f"{offering.handbook}, p. {offering.pages} ({offering.sheet} row {offering.row})"
        courses.append(
            Course(
                handbook_year=year,
                code=offering.code,
                name=title_case(offering.name),
                credits=offering.credits,
                nqf_level=offering.nqf_level,
                term=offering.term,
                entry_rule=settle(
                    offering.code,
                    place,
                    _printed(offering.requirement, None),
                    rule,
                    parts,
                ),
                convener=offering.convener,
            )
        )

    members = list(read.members)
    if workbook:
        typed_members, member_readings = complementary.members(workbook, year)
        members += typed_members
        readings += member_readings
    equivalence = equivalences.read(manifest.path(manifest.equivalences), year)
    readings += equivalence.readings

    loaded = {course.code for course in courses}
    taking: dict[str, set[str]] = defaultdict(set)
    for curriculum, code in read.taken:
        taking[code].add(curriculum)
    printed_meetings: tuple[timetable.Printed, ...] = ()
    notes: tuple[timetable.Note, ...] = ()
    slots, links, differences = [], [], ()
    if manifest.timetable:
        sheets = manifest.timetable.sheets
        sheet_read = timetable.read(manifest.path(manifest.timetable), sheets)
        printed_meetings, notes = sheet_read.printed, sheet_read.notes
        meetings = timetable.stored(
            sheet_read, sheets, taking, manifest.timetable.alternatives, year, loaded
        )
        slots, links = list(meetings.slots), list(meetings.links)
        differences = timetable.round_trip(
            sheet_read, meetings, sheets, read.taken, loaded
        )
    typed_slots = complementary.slots(workbook, year) if workbook else ()

    units = book.prose(
        [s for s in manifest.handbook.passages if s.section != manifest.department]
    )
    units += read.units
    units += [
        handbook.Unit(
            section=f"{code} {entry.name}",
            page=entry.page,
            line=book.starts[code][0],
            content=entry.content,
            course_code=code,
        )
        for code, entry in entries.items()
    ]
    printed_passages = handbook.passages(units, year, manifest.handbook.title)
    typed_passages = (
        complementary.passages(workbook, year, set(entries)) if workbook else ()
    )

    places = {r.key: r.place for r in readings if r.entity == "courses"}
    found_checks = [
        checks.entries(read.listed, entries),
        checks.credits(read.listed, entries),
        checks.terms(entries, printed_meetings),
        checks.tree_codes(courses, places, set(book.starts), equivalence.equivalences),
        checks.totals(read.subtotals),
    ]
    if manifest.timetable:
        found_checks += [
            checks.known_codes(
                printed_meetings, loaded, set(manifest.timetable.excluded)
            ),
            checks.round_trip(differences),
        ]
    if workbook:
        found_checks.append(checks.overlaps(offerings, entries))
    failed = {f.flags for check in found_checks for f in check.failures if f.flags}
    readings = [
        r.model_copy(update={"flag": "check_failed"})
        if r.flag is None and (r.entity, r.key) in failed
        else r
        for r in readings
    ]
    rules = RuleSet(
        handbook_versions=(HandbookVersion(year=year),),
        curricula=read.curricula,
        curriculum_rules=read.rules,
        courses=tuple(courses),
        course_groups=read.groups,
        course_group_members=tuple(members),
        equivalences=equivalence.equivalences,
        timetable_slots=(*slots, *typed_slots),
        timetable_slot_curricula=tuple(links),
        passages=(*printed_passages, *typed_passages),
    )
    return Candidate(
        year=year,
        rules=rules,
        readings=tuple(readings),
        rows=_present(
            {"handbook", "equivalences"}
            | ({"timetable"} if manifest.timetable else set())
            | ({WORKBOOK} if workbook else set()),
            {
                "curricula": {"handbook": len(read.curricula)},
                "curriculum_rules": {"handbook": len(read.rules)},
                "courses": {"handbook": len(entries), WORKBOOK: len(typed)},
                "course_groups": {"handbook": len(read.groups)},
                "course_group_members": {
                    "handbook": len(read.members),
                    WORKBOOK: len(members) - len(read.members),
                },
                "equivalences": {"equivalences": len(equivalence.equivalences)},
                "timetable_slots": {
                    "timetable": len(slots),
                    WORKBOOK: len(typed_slots),
                },
                "timetable_slot_curricula": {"timetable": len(links)},
                "passages": {
                    "handbook": len(printed_passages),
                    WORKBOOK: len(typed_passages),
                },
            },
        ),
        translations=translated,
        checks=tuple(found_checks),
        expanded=read.expanded,
        left_out=tuple(sorted(read.scope - entries.keys() - listed)),
        entries=frozenset(book.starts),
        unprinted=tuple(
            code for code, entry in entries.items() if not entry.requirement
        ),
        notes=notes,
        previous=previous,
        carried=tuple(carried),
    )


def review_year(
    year: int, drafter: Drafter | None = None, data: Path = DATA
) -> tuple[Candidate, Review]:
    # Ingests the year, compares it with the latest approved year before it, and writes the rows a
    # person must decide to review.json, with each decision there that still holds
    path = review_file(year, data)
    held = _read_review(path)
    candidate = ingest(year, drafter, data)
    review = _compare(candidate, held["rows"])
    _write_review(path, held["sittings"], review)
    return candidate, review


def review_file(year: int, data: Path = DATA) -> Path:
    return data / "rules" / str(year) / "review.json"


def approve(year: int, data: Path = DATA) -> tuple[Review, Snapshot | None]:
    # Reruns the year's review, and only once no row is pending and no check fails unexplained
    # writes the approved year: its rows as decided, every change with its flag and decision, and
    # where each row was printed, with any removed row a person kept from the year before
    candidate, review = review_year(year, data=data)
    if not review.settled:
        return review, None
    kept = {
        key
        for row in review.rows
        if row.kind == "removal" and row.decision == "reject"
        for key in row.covers
    }
    earlier = candidate.previous.readings if candidate.previous else ()
    snapshot = Snapshot(
        rules=review.rules.model_copy(
            update={
                "handbook_versions": (HandbookVersion(year=year, approved=True),),
                "handbook_deltas": review.deltas,
            }
        ),
        readings=(
            *candidate.readings,
            *(r for r in earlier if f"{r.entity}/{r.key}" in kept),
        ),
    )
    path = data / "rules" / str(year) / SNAPSHOT
    path.write_text(snapshot.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return review, snapshot


class Sitting:
    # One sitting of a person deciding a year's pending rows. Each decision is checked as sage ingest
    # checks it and saved to review.json as it's made, with when the sitting began and last saved and
    # the rows it decided, so stopping at any point loses nothing. One that decides nothing is saved
    # when it ends.
    def __init__(
        self, candidate: Candidate, path: Path, clock: Callable[[], datetime]
    ) -> None:
        self._candidate, self._path, self._clock = candidate, path, clock
        held = _read_review(path)
        self.review = _compare(candidate, held["rows"])
        started = clock().isoformat(timespec="seconds")
        self._sittings = [
            *held["sittings"],
            {"start": started, "end": started, "decided": 0},
        ]

    def decide(
        self,
        row_id: str,
        decision: str,
        corrected: JsonValue = None,
        note: str | None = None,
    ) -> tuple[Problem, ...]:
        # A decision on one row, kept and saved only if it leaves the row with no problem; else the
        # problems, with the row as it was
        rows = [row.model_dump() for row in self.review.rows]
        for row in rows:
            if row["id"] == row_id:
                row.update(decision=decision, corrected=corrected, note=note)
        review = _compare(self._candidate, rows)
        problems = tuple(p for p in review.problems if p.row == row_id)
        if not problems:
            self.review = review
            self._sittings[-1]["decided"] += 1
            self._save()
        return problems

    def end(self) -> list[tuple[float, int]]:
        # Saves the sitting's end, and every sitting's minutes and rows decided, this one last
        self._save()
        return [
            (
                (
                    datetime.fromisoformat(sitting["end"])
                    - datetime.fromisoformat(sitting["start"])
                ).total_seconds()
                / 60,
                sitting["decided"],
            )
            for sitting in self._sittings
        ]

    def _save(self) -> None:
        self._sittings[-1]["end"] = self._clock().isoformat(timespec="seconds")
        _write_review(self._path, self._sittings, self.review)


def approved_snapshot(year: int, data: Path = DATA) -> Snapshot:
    return Snapshot.model_validate_json(
        (data / "rules" / str(year) / SNAPSHOT).read_text(encoding="utf-8")
    )


def load(snapshot: Snapshot, rules: RuleRepository, *, replace: bool) -> None:
    # Writes an approved year to the database, refusing one already there unless asked to replace it
    if not replace and rules.get(snapshot.year).handbook_versions:
        raise YearLoaded(snapshot.year)
    rules.replace_year(snapshot.rules)


def _compare(candidate: Candidate, decided: list[dict[str, JsonValue]]) -> Review:
    return compare(
        candidate.year,
        candidate.rules,
        candidate.readings,
        candidate.checks,
        left_out=candidate.left_out,
        entries=candidate.entries,
        previous=candidate.previous,
        decided=decided,
    )


def _read_review(path: Path) -> dict[str, list]:
    # review.json's sittings and rows as last saved, or none before the year's first review
    if not path.exists():
        return {"sittings": [], "rows": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise sources.SourceError(f"{path.name} isn't valid JSON: {error}") from None


def _write_review(path: Path, sittings: list[dict], review: Review) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [row.model_dump() for row in review.rows]
    text = json.dumps(
        {"sittings": sittings, "rows": rows}, indent=2, ensure_ascii=False
    )
    path.write_text(text + "\n", encoding="utf-8")


def _latest_approved(year: int, data: Path) -> Snapshot | None:
    # The latest approved year before this one, each held in data/rules/<year>/rulebook.json
    before = [
        int(path.parent.name)
        for path in (data / "rules").glob(f"*/{SNAPSHOT}")
        if int(path.parent.name) < year
    ]
    return approved_snapshot(max(before), data) if before else None


def _present(
    sources: set[str], rows: dict[str, dict[str, int]]
) -> dict[str, dict[str, int]]:
    # Each table's rows from the sources the year has, as 2023 has no timetable or workbook
    return {
        table: {source: count for source, count in counts.items() if source in sources}
        for table, counts in rows.items()
    }


def _rule(parts: list[translate.Translation]) -> EntryRule | None:
    # A course's requirement and co-requisite as one tree. Where only one is printed, the course
    # stores it alone, as the canonical form unwraps an all of one.
    trees = tuple(part.tree for part in parts if part.tree is not None)
    return AllOf(all=trees) if trees else None


def _printed(requirement: str | None, corequisite: str | None) -> str:
    # A course's requirement as a reviewer reads it and the next year matches it: single-spaced, with
    # any co-requisite labelled, so the same words as a requirement and as a co-requisite never match
    words = [requirement or "", f"Co-requisites: {corequisite}" if corequisite else ""]
    return " ".join(" ".join(words).split()) or "No requirement printed"
