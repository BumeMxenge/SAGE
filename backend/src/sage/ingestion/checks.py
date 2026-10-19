# Checks the sources against each other. Each check names every failure and where to look, and a
# failure on a row a person reviews flags that row check_failed. A finding a person has already
# settled is reported, not failed, so it never stops a year being approved.
from collections.abc import Iterable, Mapping

from sage.ingestion.complementary import NOT_STATED, Offering
from sage.ingestion.curricula import Listed, Subtotal
from sage.ingestion.handbook import Entry
from sage.ingestion.names import title_case
from sage.ingestion.timetable import WITHIN, Printed
from sage.shared.base import Row
from sage.shared.rules import (
    TERM_BY_SUFFIX,
    AllOf,
    AnyOf,
    Course,
    CourseNeed,
    EntryRule,
    Equivalence,
)


class Failure(Row):
    place: str  # where to look, such as "p. 138" or "Labs!D27:D30"
    what: str
    flags: tuple[str, str] | None = None  # the reviewed row it flags: its table and key


class Check(Row):
    name: str
    failures: tuple[Failure, ...]
    reported: tuple[Failure, ...] = ()


def known_codes(
    meetings: Iterable[Printed], known: set[str], excluded: set[str]
) -> Check:
    # A code the manifest excludes, such as a Labs course no curriculum lists, is reported
    unknown = [(m, code) for m in meetings for code in m.codes if code not in known]

    def failure(meeting: Printed, code: str) -> Failure:
        return Failure(
            place=f"{meeting.sheet}!{meeting.cells}",
            what=f"{code} isn't in the rulebook",
        )

    return Check(
        name="Every timetable code is a course the rulebook holds",
        failures=tuple(failure(m, code) for m, code in unknown if code not in excluded),
        reported=tuple(failure(m, code) for m, code in unknown if code in excluded),
    )


def entries(listed: Iterable[Listed], read: Mapping[str, Entry]) -> Check:
    return Check(
        name="Every curriculum course has an entry",
        failures=tuple(
            Failure(
                place=f"p. {row.page}",
                what=f"{row.curriculum} lists {row.code}, which has no entry",
                flags=("curriculum_rules", f"{row.curriculum}/{row.year}"),
            )
            for row in listed
            if row.code not in read
        ),
    )


def credits(listed: Iterable[Listed], read: Mapping[str, Entry]) -> Check:
    failures = []
    for row in listed:
        entry = read.get(row.code)
        if entry and (row.credits, row.nqf_level) != (entry.credits, entry.nqf_level):
            failures.append(
                Failure(
                    place=f"p. {row.page} and p. {entry.page}",
                    what=(
                        f"{row.curriculum} lists {row.code} at {row.credits} credits and NQF "
                        f"level {row.nqf_level}, its entry {entry.credits} and {entry.nqf_level}"
                    ),
                    flags=("courses", row.code),
                )
            )
    return Check(
        name="Credits and NQF levels agree between table and entry",
        failures=tuple(failures),
    )


def terms(read: Mapping[str, Entry], meetings: Iterable[Printed]) -> Check:
    # An entry's printed term, and the semester a meeting is printed under, against the code's suffix.
    # A full-year course meets in either semester.
    failures = [
        Failure(
            place=f"p. {entry.page}",
            what=f"{code}'s entry prints {entry.term}",
            flags=("courses", code),
        )
        for code, entry in read.items()
        if entry.term and TERM_BY_SUFFIX.get(code[-1]) != entry.term
    ]
    failures += [
        Failure(place=f"{m.sheet}!{m.cells}", what=f"{code} is printed in {m.semester}")
        for m in meetings
        for code in m.codes
        if TERM_BY_SUFFIX.get(code[-1]) not in (*WITHIN[m.semester], "full_year")
    ]
    return Check(
        name="Printed terms agree with codes' suffixes", failures=tuple(failures)
    )


def tree_codes(
    courses: Iterable[Course],
    places: Mapping[str, str],
    printed: set[str],
    equivalences: Iterable[Equivalence],
) -> Check:
    # A code a rule names must be a course the rulebook holds, one the handbook prints an entry
    # for, or one an equivalence names; any other, such as a retired code, is for a person to judge
    courses = list(courses)
    known = {c.code for c in courses} | printed
    known |= {code for e in equivalences for code in (e.course_code, e.counts_as)}
    failures = [
        Failure(
            place=places[course.code],
            what=f"{course.code}'s rule names {code}, which isn't loaded, printed or equivalent",
            flags=("courses", course.code),
        )
        for course in courses
        if course.entry_rule
        for code in sorted(_named(course.entry_rule) - known)
    ]
    return Check(
        name="Every code a rule names is loaded, printed or equivalent",
        failures=tuple(failures),
    )


def round_trip(differences: Iterable[str]) -> Check:
    return Check(
        name="The timetable rebuilds from the stored meetings",
        failures=tuple(Failure(place="timetable", what=d) for d in differences),
    )


def totals(subtotals: Iterable[Subtotal]) -> Check:
    return Check(
        name="Printed totals add up",
        failures=tuple(
            Failure(
                place=f"p. {s.page}",
                what=(
                    f"{s.curriculum} year {s.year}'s core table prints {s.printed} credits, "
                    f"but its rows add up to {s.summed}"
                ),
                flags=("curriculum_rules", f"{s.curriculum}/{s.year}"),
            )
            for s in subtotals
            if s.printed != s.summed
        ),
    )


def overlaps(offerings: Iterable[Offering], read: Mapping[str, Entry]) -> Check:
    # A workbook row for a course the faculty handbook also prints agrees with that entry, where an
    # entry with no requirement line is what the workbook types as not stated
    failures = []
    for offering in offerings:
        entry = read.get(offering.code)
        if entry is None:
            continue
        typed = {
            "name": title_case(offering.name),
            "credits": offering.credits,
            "NQF level": offering.nqf_level,
            "requirement": " ".join(offering.requirement.split()),
        }
        printed = {
            "name": entry.name,
            "credits": entry.credits,
            "NQF level": entry.nqf_level,
            "requirement": entry.requirement or NOT_STATED,
        }
        differences = [
            f"{field} {typed[field]!r}, printed {printed[field]!r}"
            for field in typed
            if typed[field] != printed[field]
        ]
        if differences:
            failures.append(
                Failure(
                    place=f"{offering.sheet} row {offering.row} and p. {entry.page}",
                    what=f"{offering.code} is typed with {'; '.join(differences)}",
                    flags=("courses", offering.code),
                )
            )
    return Check(
        name="Workbook rows agree with the handbook's entries", failures=tuple(failures)
    )


def _named(tree: EntryRule) -> set[str]:
    if isinstance(tree, CourseNeed):
        return {tree.course}
    if isinstance(tree, AllOf | AnyOf):
        children = tree.all if isinstance(tree, AllOf) else tree.any
        return set().union(*(_named(child) for child in children))
    return set()
