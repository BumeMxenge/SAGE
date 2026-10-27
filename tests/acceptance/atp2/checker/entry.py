# Entry rules as SEMANTICS.md reads them (Entry rules): each is met (True), not met (False) or open
# (None), and an open rule never blocks a course, so its course is conditional
from collections.abc import Iterable
from dataclasses import dataclass

from checker.record import PASSED, Line, Record
from sage.shared.rules import (
    AllOf,
    AnyOf,
    CourseNeed,
    EntryRule,
    MinYearOfStudy,
    Refer,
    StudentIn,
)

# When each term starts and ends, in steps through the year: q1 and q2 make up sem1, q3 and q4
# sem2, full_year spans both, winter falls between the semesters and summer after them
SPAN = {
    "q1": (0, 2),
    "q2": (2, 4),
    "sem1": (0, 4),
    "winter": (4, 5),
    "q3": (5, 7),
    "q4": (7, 9),
    "sem2": (5, 9),
    "full_year": (0, 9),
    "summer": (9, 10),
}


@dataclass(frozen=True)
class Context:
    # What a rule is judged against: her record, curriculum and year of study, and inside a plan
    # the judged course's term, with each other plan course's covers and term. Outside a plan, as
    # on Explore Electives, plan is None.
    record: Record
    curriculum: str
    year: int
    term: str = ""
    plan: tuple[tuple[frozenset[str], str], ...] | None = None


def value(rule: EntryRule | None, context: Context) -> bool | None:
    match rule:
        case None:
            return True
        case AllOf():
            return every(value(child, context) for child in rule.all)
        case AnyOf():
            return some(value(child, context) for child in rule.any)
        case Refer():
            return None  # printed words a person must judge
        case StudentIn():
            return context.curriculum in rule.student_in
        case MinYearOfStudy():
            return context.year >= rule.min_year_of_study
        case CourseNeed():
            return leaf(rule, context)


def every(values: Iterable[bool | None]) -> bool | None:
    # all: not met when any child isn't, open when any child is open, and met otherwise
    found = set(values)
    if False in found:
        return False
    return None if None in found else True


def some(values: Iterable[bool | None]) -> bool | None:
    # any: met when any child is, open when any child is open, and not met otherwise
    found = set(values)
    if True in found:
        return True
    return None if None in found else False


def leaf(need: CourseNeed, context: Context) -> bool | None:
    # Any of her attempts can meet a leaf, through the codes each covers, and inside a plan so can
    # a plan course
    values = [
        attempt(need, line)
        for line in context.record.lines
        if need.course in line.covers
    ]
    if context.plan is None:
        if need.need == "concurrent":
            values.append(None)  # outside a plan she could take it alongside
    else:
        values += [
            planned(need, context.term, term)
            for covers, term in context.plan
            if need.course in covers
        ]
    return some(values)


def attempt(need: CourseNeed, line: Line) -> bool | None:
    # One line against a leaf, by the table in "What each result means on a leaf"
    if line.outcome == "in_progress":
        return None
    if need.min_mark is None:  # a pass leaf, or a co-requisite met by an earlier pass
        return None if line.outcome == "supp_pending" else line.outcome in PASSED
    if line.outcome in ("dp_refused", "not_counted"):
        return False
    if line.outcome == "supp_pending":
        return None if need.min_mark <= 50 else False
    if line.outcome == "credited":
        return None
    if line.mark is None:
        # A pass printed with no mark, such as PA or UP, is open, and a fail with none isn't met
        return None if line.outcome == "pass" else False
    return line.mark >= need.min_mark


def planned(need: CourseNeed, term: str, theirs: str) -> bool | None:
    # A plan course taken in place of a pass, assuming she passes it: a co-requisite that starts
    # no later, or a pass leaf, or a mark leaf of 50 or less, on a course in an earlier term. A
    # mark leaf above 50 there is open.
    start = SPAN[term][0]
    if need.need == "concurrent":
        return SPAN[theirs][0] <= start
    if SPAN[theirs][1] > start:
        return False
    return True if need.need == "pass" or need.min_mark <= 50 else None
