# Reads the complementary studies workbook: each course and language option on the approved list, as
# the faculty handbook describing it prints it, and their meetings. Every row is checked against the
# rules the workbook was typed to, and a row that breaks one stops the run with its number. Both
# sheets of offerings join the complementary group, and language options are its languages category.
import re
from collections import defaultdict
from collections.abc import Iterator
from datetime import time
from pathlib import Path
from typing import Annotated, Literal, Self

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import Field, StringConstraints, ValidationError, model_validator

from sage.ingestion.curricula import COMPLEMENTARY
from sage.ingestion.names import title_case
from sage.ingestion.sources import ComplementaryFile, Reading, SourceError, row_id
from sage.shared.base import Row
from sage.shared.rules import (
    COURSE_CODE,
    TERM_BY_SUFFIX,
    CourseGroupMember,
    Passage,
    TermCode,
    TimetableSlot,
)

OFFERING_COLUMNS = {
    "Handbook course code": "code",
    "Course name": "name",
    "Faculty": "faculty",
    "Credits": "credits",
    "NQF level": "nqf_level",
    "Course outline": "outline",
    "Entry requirements / Corequisites": "requirement",
    "Term": "term",
    "Class times": "class_times",
    "Assessment": "assessment",
    "Course Convener": "convener",
    "Other handbook details": "details",
    "Handbook": "handbook",
    "Printed page": "pages",
}
MEETING_COLUMNS = {
    "Code": "code",
    "Kind": "kind",
    "Days": "days",
    "Start": "start",
    "End": "end",
    "Choice group": "choice_group",
    "Choice": "choice",
}
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
# The workbook's words where an entry prints no requirement, which doesn't mean there's none
NOT_STATED = "Not stated in course entry."

Code = Annotated[str, StringConstraints(pattern=rf"^{COURSE_CODE}$")]
# A page, a range or a list of them, as in 58, 58–59 or 153, 247
Pages = Annotated[
    str, StringConstraints(pattern=r"^\d+(?:[–-]\d+)?(?:, ?\d+(?:[–-]\d+)?)*$")
]
Day = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
Kind = Literal[
    "lecture", "tutorial", "practical", "lab", "workshop", "screening", "conversation"
]


class Offering(Row):
    # One course or language option, as the workbook types it from a faculty handbook
    sheet: str
    row: int
    code: Code
    name: str
    faculty: str
    credits: int = Field(ge=0)
    nqf_level: int = Field(ge=5, le=10)
    outline: str
    requirement: str
    term: TermCode
    class_times: str
    assessment: str
    convener: str
    details: str
    handbook: str  # the faculty handbook's title
    pages: Pages

    @model_validator(mode="after")
    def term_agrees_with_suffix(self) -> Self:
        if TERM_BY_SUFFIX.get(self.code[-1]) != self.term:
            raise ValueError(
                f"term {self.term} doesn't agree with {self.code}'s suffix"
            )
        return self


class Meeting(Row):
    row: int
    code: str
    kind: Kind
    days: tuple[Day, ...]  # empty when the handbook prints no day
    start: time | None
    end: time | None
    choice_group: str | None
    choice: str | None

    @model_validator(mode="after")
    def times_and_choices_pair_up(self) -> Self:
        if (self.start is None) != (self.end is None):
            raise ValueError("a meeting has both a start and an end, or neither")
        if self.start is not None and self.end <= self.start:
            raise ValueError("a meeting ends after it starts")
        if (self.choice_group is None) != (self.choice is None):
            raise ValueError(
                "a meeting has both a choice group and a choice, or neither"
            )
        return self


class Complementary(Row):
    offerings: tuple[Offering, ...]
    languages: str  # the sheet of language options
    meetings: tuple[Meeting, ...]


def read(path: Path, source: ComplementaryFile) -> Complementary:
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    offerings: list[Offering] = []
    for name in (source.courses, source.languages):
        for number, fields in _rows(book[name], OFFERING_COLUMNS):
            fields |= {"sheet": name, "row": number, "pages": str(fields["pages"])}
            offering = _valid(Offering, f"{name} row {number}", fields)
            if any(o.code == offering.code for o in offerings):
                raise SourceError(
                    f"{name} row {number}: {offering.code} is listed twice"
                )
            offerings.append(offering)
    codes = {offering.code for offering in offerings}
    meetings: list[Meeting] = []
    choices: dict[tuple[str, str], set[str]] = defaultdict(set)
    for number, fields in _rows(book[source.meetings], MEETING_COLUMNS):
        days = tuple(fields["days"].split(",")) if fields["days"] else ()
        fields |= {"row": number, "days": days}
        meeting = _valid(Meeting, f"{source.meetings} row {number}", fields)
        if meeting.code not in codes:
            raise SourceError(
                f"{source.meetings} row {number}: {meeting.code} isn't listed"
            )
        if meeting.choice_group is not None:
            choices[meeting.code, meeting.choice_group].add(meeting.choice)
        meetings.append(meeting)
    for (code, group), letters in choices.items():
        if len(letters) < 2:
            raise SourceError(
                f"{code}'s choice group {group} has one choice, not two or more"
            )
    return Complementary(
        offerings=tuple(offerings), languages=source.languages, meetings=tuple(meetings)
    )


def _rows(sheet: Worksheet, columns: dict[str, str]) -> Iterator[tuple[int, dict]]:
    # A sheet's rows under its title and its header, by field name
    rows = sheet.iter_rows(values_only=True)
    next(rows)  # the sheet's title
    header = next(rows)
    if header[: len(columns)] != tuple(columns) or any(header[len(columns) :]):
        raise SourceError(f"{sheet.title}'s columns aren't the workbook's: {header}")
    for number, values in enumerate(rows, start=3):
        if any(values[len(columns) :]):
            raise SourceError(
                f"{sheet.title} row {number} has a value past its columns"
            )
        if any(value is not None for value in values):
            yield number, dict(zip(columns.values(), values, strict=False))


def _valid[T: Row](model: type[T], where: str, fields: dict[str, object]) -> T:
    # A row the rules refuse stops the run, named by its sheet and number
    try:
        return model.model_validate(fields)
    except ValidationError as error:
        problem = error.errors()[0]
        field = ".".join(str(part) for part in problem["loc"])
        raise SourceError(f"{where}: {field} {problem['msg']}") from error


def members(
    read: Complementary, year: int
) -> tuple[tuple[CourseGroupMember, ...], tuple[Reading, ...]]:
    # Every offering joins the complementary group, with the row it's typed in. Language options
    # are the languages category; the other categories, which a model would pick, wait for M3.
    rows = tuple(
        CourseGroupMember(
            handbook_year=year,
            group_key=COMPLEMENTARY,
            course_code=offering.code,
            category="languages" if offering.sheet == read.languages else None,
        )
        for offering in read.offerings
    )
    readings = tuple(
        Reading(
            entity="course_group_members",
            key=f"{COMPLEMENTARY}/{offering.code}",
            place=f"{offering.sheet} row {offering.row}",
            printed=f"{offering.code} {offering.name}",
        )
        for offering in read.offerings
    )
    return rows, readings


def slots(read: Complementary, year: int) -> tuple[TimetableSlot, ...]:
    # One stored meeting per day a row prints, or one with no day when it prints none. Rows are
    # stored as written, so REL1017S's "plus two tutorials" is two tutorials even though neither
    # prints a time, as each id includes its row.
    terms = {offering.code: offering.term for offering in read.offerings}
    slots = []
    for meeting in read.meetings:
        for day in meeting.days or (None,):
            row = {
                "handbook_year": year,
                "course_code": meeting.code,
                "term": terms[meeting.code],
                "day": DAYS.index(day) + 1 if day else None,
                "start_time": meeting.start,
                "end_time": meeting.end,
                "kind": meeting.kind,
                "choice_group": meeting.choice_group,
                "choice": meeting.choice,
            }
            place = f"Meetings row {meeting.row}"
            slots.append(TimetableSlot(id=row_id({"place": place, **row}), **row))
    return tuple(slots)


def passages(read: Complementary, year: int, skip: set[str]) -> tuple[Passage, ...]:
    # One passage per offering, from the workbook's copy of its entry, under the handbook that
    # prints it and its first printed page. Each handbook's passages are numbered by page, then
    # row. An offering in skip is read from the faculty handbook itself.
    by_source: dict[str, list[Offering]] = defaultdict(list)
    for offering in read.offerings:
        if offering.code not in skip:
            by_source[offering.handbook].append(offering)
    rows = []
    for source, offerings in by_source.items():
        offerings.sort(key=lambda o: (_first_page(o), o.sheet != read.languages, o.row))
        for position, offering in enumerate(offerings, start=1):
            row = {
                "handbook_year": year,
                "curriculum_code": None,
                "course_code": offering.code,
                "source": source,
                "section": f"{offering.code} {title_case(offering.name)}",
                "page": _first_page(offering),
                "position": position,
                "content": "\n".join(
                    f"{label}: {text}"
                    for label, text in (
                        ("Course outline", offering.outline),
                        ("Entry requirements", offering.requirement),
                        ("Class times", offering.class_times),
                        ("Assessment", offering.assessment),
                        ("Other details", offering.details),
                    )
                ),
            }
            rows.append(Passage(id=row_id(row), **row))
    return tuple(rows)


def _first_page(offering: Offering) -> int:
    return int(re.match(r"\d+", offering.pages)[0])
