# Ingests one handbook year into a candidate rulebook, writing nothing to any database. It checks the
# year's sources against their manifest, reads each, translates the printed requirements, grammar
# first, and checks the sources against each other. Every row keeps where it was printed and why a
# person must look at it, for the review in C2.
from collections import defaultdict
from pathlib import Path

from sage.domain.base import Row
from sage.domain.drafting import Drafter
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

# Four folders up from this file: the repo root, as for the seed file
DATA = Path(__file__).resolve().parents[4] / "data"
WORKBOOK = "complementary workbook"


class DryRun(Row):
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
    # Entries that print no requirement line, read like a printed "None"
    unprinted: tuple[str, ...]
    notes: tuple[timetable.Note, ...]


def ingest(year: int, drafter: Drafter | None = None, data: Path = DATA) -> DryRun:
    manifest = sources.load(data / "sources" / str(year))
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
    translated = translate.translate(
        strings, data / "rules" / str(year) / "drafts.json", drafter
    )
    found = {(t.printed, t.need): t for t in translated.translations}

    def translation(printed: str | None, need: str) -> translate.Translation | None:
        return found[" ".join(printed.split()), need] if printed else None

    courses, readings = [], list(read.readings)
    for code, entry in entries.items():
        parts = [
            t
            for t in (
                translation(entry.requirement, "pass"),
                translation(entry.corequisite, "concurrent"),
            )
            if t
        ]
        courses.append(
            Course(
                handbook_year=year,
                code=code,
                name=entry.name,
                credits=entry.credits,
                nqf_level=entry.nqf_level,
                term=entry.term or TERM_BY_SUFFIX[code[-1]],
                entry_rule=_rule(parts),
                convener=entry.convener,
            )
        )
        printed = " Co-requisites: ".join(
            text for text in (entry.requirement, entry.corequisite) if text
        )
        readings.append(_course_reading(code, f"p. {entry.page}", printed, parts))
    for offering in typed:
        # The workbook's "Not stated in course entry." is a refer leaf, as it doesn't mean there's
        # no requirement; any other wording was translated
        not_stated = offering.requirement == complementary.NOT_STATED
        parts = (
            []
            if not_stated
            else [found[" ".join(offering.requirement.split()), "pass"]]
        )
        courses.append(
            Course(
                handbook_year=year,
                code=offering.code,
                name=title_case(offering.name),
                credits=offering.credits,
                nqf_level=offering.nqf_level,
                term=offering.term,
                entry_rule=Refer(refer=offering.requirement)
                if not_stated
                else _rule(parts),
                convener=offering.convener,
            )
        )
        place = f"{offering.handbook}, p. {offering.pages} ({offering.sheet} row {offering.row})"
        readings.append(
            _course_reading(offering.code, place, offering.requirement, parts)
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
    typed_slots = complementary.slots(workbook, year)[0] if workbook else ()

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
    return DryRun(
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
        unprinted=tuple(
            code for code, entry in entries.items() if not entry.requirement
        ),
        notes=notes,
    )


def _present(
    sources: set[str], rows: dict[str, dict[str, int]]
) -> dict[str, dict[str, int]]:
    # Each table's rows from the sources the year has, as 2023 has no timetable or workbook
    return {
        table: {source: count for source, count in counts.items() if source in sources}
        for table, counts in rows.items()
    }


def _rule(parts: list[translate.Translation]) -> EntryRule | None:
    # A course's requirement and co-requisite as one tree, where both are printed
    trees = tuple(part.tree for part in parts if part.tree is not None)
    if not trees:
        return None
    return trees[0] if len(trees) == 1 else AllOf(all=trees)


def _course_reading(
    code: str, place: str, printed: str, parts: list[translate.Translation]
) -> sources.Reading:
    # A course with wording the grammar refused is flagged with that refusal's cause
    return sources.Reading(
        entity="courses",
        key=code,
        place=place,
        printed=printed or "No requirement printed",
        flag=next((part.cause for part in parts if part.cause), None),
    )
