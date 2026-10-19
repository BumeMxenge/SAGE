# ATP-1's rules for marking SAGE against the labels: the Scoring section of labels/README.md, with
# the readings settled at the harness's Stop 1. Trees are compared as E2's score.py compares them,
# and a count with nothing wrong takes E2's bound, so both come from score.py, which make puts on
# Python's path.
import json
import re
from collections.abc import Iterable, Sequence
from datetime import time
from math import sqrt
from statistics import NormalDist
from typing import Any

import transcripts
from labels.check_labels import DAYS, NO_ENTRY, Row
from score import canonical, normal, upper_bound

from sage.ingestion import complementary
from sage.ingestion.timetable import Printed
from sage.ingestion.transcript import TranscriptLine, TranscriptWarning
from sage.shared.rules import HandbookDelta

# How SAGE came to hold an item: no person saw it, a person decided a review row that showed it, or
# SAGE holds nothing from it
ACCEPTED = "accepted without review"
REVIEWED = "reviewed"
NOT_STORED = "not stored"

# A decided requirement row shows a person the printed line, where it's printed, and the trees. It
# never shows a course's title, credits, NQF level or term, and no review row shows a meeting.
SHOWN = {"entry_rule", "requirement", "corequisite", "page", "book"}
# What a 2026 row can carry over unchanged from a 2023 decision. A page belongs to its year's book.
CARRIED = {"entry_rule", "requirement", "corequisite"}

# The rule fields a course sheet labels, by the name SAGE's courses give each
FIELDS = {
    "title": "name",
    "credits": "credits",
    "nqf_level": "nqf_level",
    "term": "term",
    "entry_rule": "entry_rule",
}
COLUMNS = {
    "title": "Title",
    "credits": "Credits",
    "nqf_level": "NQF level",
    "term": "Term",
}

# Each faculty handbook by its cover title, as the labels name it, and by the workbook's name for it
BOOKS = {
    "University of Cape Town, Faculty of Commerce (Undergraduate), 2026": (
        "UCT Faculty of Commerce Undergraduate Handbook 2026 (Book 6a)"
    ),
    "University of Cape Town, Faculty of Engineering & the Built Environment (Undergraduate), 2026": (
        "UCT Faculty of Engineering & the Built Environment Undergraduate Handbook 2026 (Book 7a)"
    ),
    "University of Cape Town, Faculty of Humanities (Undergraduate), 2026": (
        "UCT Faculty of Humanities Undergraduate Handbook 2026 (Book 9a)"
    ),
    "University of Cape Town, Faculty of Science, 2026": (
        "UCT Faculty of Science Handbook 2026 (Book 11)"
    ),
}
# A day as the workbook writes it, mon to sun, by the name the labels give it
WORKBOOK_DAYS = dict(zip(complementary.DAYS, DAYS, strict=True))
# A page or a range in the workbook's printed pages, as in 58, 58–59 or 153, 247
PAGE_RANGE = re.compile(r"(\d+)(?:[–-](\d+))?")
# The year a Term GPA warning names, as in "Your 2024 lines don't add up"
YEAR = re.compile(r"\b\d{4}\b")
Z = NormalDist().inv_cdf(0.975)  # 1.96, for a two-sided 95% interval


def tree(cell: Any) -> Any:
    # A label's tree from its cell, where a blank and null both mean no requirement
    return None if cell is None else json.loads(str(cell))


def joined(requirement: Any, corequisite: Any) -> Any:
    # A label's Requirement tree and Co-requisite tree as the one rule SAGE stores for its course. A
    # blank or null tree adds nothing, so a course with one tree keeps it alone.
    trees = [found for found in map(tree, (requirement, corequisite)) if found]
    if not trees:
        return None
    return trees[0] if len(trees) == 1 else {"all": trees}


def same_tree(label: Any, sage: Any) -> bool:
    # Both sides in the types' own JSON, then in E2's normal form, as E2's score.py compares them
    return normal(canonical(label)) == normal(canonical(sage))


def evened(text: str | None) -> str | None:
    # Printed text with its spacing evened out, as SAGE's readers keep it
    return None if text is None else " ".join(str(text).split())


def labelled(row: Row, field: str) -> Any:
    # A course sheet's label for one rule field, in the form SAGE stores the field
    if field == "entry_rule":
        return joined(row["Requirement tree"], row["Co-requisite tree"])
    value = row[COLUMNS[field]]
    return int(value) if field in ("credits", "nqf_level") else str(value)


def agrees(field: str, label: Any, sage: Any) -> bool:
    # A label and a value of SAGE's for one field: titles ignoring case, as SAGE title-cases names,
    # trees in normal form, and printed text with its spacing evened out
    if field == "title":
        return label.casefold() == sage.casefold()
    if field in ("entry_rule", "requirement_tree", "corequisite_tree"):
        return same_tree(label, sage)
    if field in ("requirement", "corequisite"):
        return evened(label) == evened(sage)
    return label == sage


def printed(row: Row | None) -> bool:
    # Whether a course sheet holds the course for its year: a row with an entry
    return row is not None and row["Note"] != NO_ENTRY


def judgement(row: Row) -> bool:
    # A judgement call: a Note other than the sheet maker's "no entry printed", or Ambiguous yes
    return row["Note"] not in (None, NO_ENTRY) or row.get("Ambiguous") == "yes"


def within(page: int, pages: str) -> bool:
    # Whether a page falls within the workbook's printed pages for a course
    return any(
        int(first) <= page <= int(last or first)
        for first, last in PAGE_RANGE.findall(pages)
    )


def day_name(number: int) -> str:
    # A timetable meeting's day, which the reader numbers from 1 for Monday, by its name
    return DAYS[number - 1]


def by_cell(meetings: Iterable[Printed]) -> dict[tuple[str, str], Printed]:
    # Each printed meeting by its sheet and the first cell of its block, which holds its text and
    # names it on timetable.xlsx
    return {(m.sheet, m.cells.split(":")[0]): m for m in meetings}


def course_review(
    field: str, decided: bool, unchanged: bool = False, decided_before: bool = False
) -> str:
    # Whether a person saw a stored course's field: a row decided in its year showed it, or a row
    # decided in 2023 showed it and it hasn't changed since
    if field in SHOWN and (
        decided or (field in CARRIED and unchanged and decided_before)
    ):
        return REVIEWED
    return ACCEPTED


def course_changes(
    code: str, before: Row | None, after: Row | None, delta: HandbookDelta | None
) -> list[dict[str, str]]:
    # A course's labelled changes from 2023 to 2026, each recalled when SAGE's 2026 review records
    # a delta for it in that field, flagged or not. Then a flagged delta the labels show no change of
    # rule for is a wording change where the labelled text changed, and otherwise a false alarm.
    old = delta.old_value if delta else None
    new = delta.new_value if delta else None
    flag = delta.flag if delta and delta.flag else ""
    calls = "yes" if any(row and judgement(row) for row in (before, after)) else "no"
    found = []

    def change(
        field: str, kind: str, outcome: str, was: Any = "", now: Any = ""
    ) -> None:
        found.append(
            {
                "code": code,
                "field": field,
                "change": kind,
                "label_2023": shown(was),
                "label_2026": shown(now),
                "flag": flag,
                "outcome": outcome,
                "judgement": calls,
            }
        )

    if printed(before) and printed(after):
        rule_changed = False
        for field, column in FIELDS.items():
            was, now = labelled(before, field), labelled(after, field)
            if agrees(field, was, now):
                continue
            rule_changed = rule_changed or field == "entry_rule"
            recorded = (
                old is not None and new is not None and old[column] != new[column]
            )
            change(field, "changed", "recalled" if recorded else "missed", was, now)
        if flag and (old is None or new is None):
            # SAGE added or removed a course both years print
            change("course", "none", "false alarm")
        elif flag and not rule_changed:
            worded = any(
                evened(before[column]) != evened(after[column])
                for column in ("Requirement", "Co-requisite")
            )
            change("entry_rule", "none", "wording change" if worded else "false alarm")
    elif printed(before) or printed(after):
        removed = printed(before)
        recorded = delta is not None and (new if removed else old) is None
        change(
            "course",
            "removed" if removed else "added",
            "recalled" if recorded else "missed",
        )
    return found


def read_back(
    student: str,
    rows: Sequence[transcripts.Row],
    lines: Sequence[TranscriptLine],
    warnings: Sequence[TranscriptWarning],
) -> list[dict[str, str]]:
    # What the transcript reader gave back for each printed row: the row itself, recovered; a line
    # it marked unverified, or only its year's Term GPA warning, which flag it; or neither, so it was
    # dropped, and a line with its year and code but other values is extra. Every line no row
    # accounts for is extra, and every warning is listed, as a made-up record should raise none.
    left = list(lines)
    warned = {
        int(year) for warning in warnings for year in YEAR.findall(warning.message)
    }
    found = []
    for row in rows:
        same = [
            line
            for line in left
            if (line.academic_year, line.course_code) == (row.year, row.code)
        ]
        exact = next((line for line in same if said(line) == said(row)), None)
        unverified = next((line for line in same if line.unverified), None)
        if exact is not None:
            outcome, line = "recovered", exact
        elif unverified is not None:
            outcome, line = "unverified", unverified
        else:
            outcome, line = "GPA warning" if row.year in warned else "dropped", None
        if line is not None:
            left.remove(line)
        found.append(
            returned(student, row.year, row.code, row.kind, row, line, outcome)
        )
    found += [
        returned(student, line.academic_year, line.course_code, "", None, line, "extra")
        for line in left
    ]
    found += [
        {
            "student": student,
            "year": next(iter(YEAR.findall(warning.message)), ""),
            "code": "",
            "kind": "",
            "printed": "",
            "read": warning.message,
            "outcome": "warning",
        }
        for warning in warnings
    ]
    return found


def said(line: TranscriptLine | transcripts.Row) -> tuple[Any, ...]:
    # What a printed row says and its line should give back: name, NQF level, credits, mark, result
    if isinstance(line, TranscriptLine):
        return (line.course_name, line.nqf_level, line.credits, line.mark, line.result)
    return (line.name, line.nqf, line.credits, line.mark, line.result)


def returned(
    student: str,
    year: int,
    code: str,
    kind: str,
    row: transcripts.Row | None,
    line: TranscriptLine | None,
    outcome: str,
) -> dict[str, str]:
    # A row of transcripts.csv: what was printed, what the reader gave back, and which outcome
    def described(found: TranscriptLine | transcripts.Row | None) -> str:
        return " | ".join(map(shown, said(found))) if found is not None else ""

    return {
        "student": student,
        "year": str(year),
        "code": code,
        "kind": kind,
        "printed": described(row),
        "read": described(line),
        "outcome": outcome,
    }


def shown(value: Any) -> str:
    # A value as a CSV cell: blank for none, trees as JSON, times as HH:MM
    if value is None:
        return ""
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return str(value)


def wilson(k: int, n: int) -> tuple[float, float]:
    # The 95% Wilson score interval for k of n, held within 0 and 1 against rounding
    p, z2 = k / n, Z * Z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = Z * sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def bound(wrong: int, n: int) -> float | None:
    # E2's one-sided 95% upper bound on the error rate, which applies only when none of n is wrong
    return upper_bound(n) if wrong == 0 else None
