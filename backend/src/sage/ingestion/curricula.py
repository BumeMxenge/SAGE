# Reads a department's curricula from its section of the handbook: each curriculum's name and code,
# and each year's tables as course groups, their members and one rule. A printed line no rule shape
# can hold, such as a footnote about the 576-credit curriculum, is kept as a note for a person to
# judge, and each curriculum's introduction and tables are kept word for word as passages.
import re
from collections import defaultdict

from sage.ingestion.handbook import Handbook, Unit
from sage.ingestion.sources import Reading, Section, SourceError
from sage.shared.base import Row
from sage.shared.rules import (
    COMPLEMENTARY,
    COURSE_CODE,
    AllOfGroup,
    ChooseFromGroup,
    CourseGroup,
    CourseGroupMember,
    CreditsFromGroups,
    Curriculum,
    CurriculumRule,
    TotalCredits,
    YearRule,
    YearRules,
)

YEARS = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4, "Fifth": 5}
COUNTS = {"one": 1, "two": 2}
# The line under a curriculum's name, as in BSc(Engineering)(Electrical Engineering)[EB009EEE01]
CURRICULUM = re.compile(r".*\[([A-Z]{2}\d{3}[A-Z]{3}\d{2})\]")
# A table's heading, such as "First Year Core Courses (EE)*†", whose marks point at notes below it
TABLE = re.compile(r"(First|Second|Third|Fourth|Fifth) Year (.*)Courses \(\w+\)[*†]*")
OPTIONAL = "Optional Courses"
COLUMNS = "Code Course NQF Credits NQF Level"
# A course row: code, title, dot leaders, credits and NQF level
LISTED = re.compile(rf"({COURSE_CODE}) .+?[.…]+ ?(\d+) (\d+)")
# A wildcard row, such as CSC3xxx, standing for every course whose code starts that way
WILDCARD = re.compile(r"([A-Z]{3}\d)xxx .+?[.…]+ ?\d+ \d+")
# The complementary studies slot and its credits, however its marks are printed
SLOT = re.compile(
    r".*Approved Complementary Studies Elective F/S/P/L ?[.…]+ ?(\d+)( \d+)?"
)
# A year's total, or a core table's, where a range such as 154-162 gives its minimum first
TOTAL = re.compile(r"(Total|Core) credits per year( \(minimum\))? ?[.…]+ ?(\d+)(-\d+)?")
# The line that opens an elective table's second list
FURTHER = "And further courses from"
# What an elective table's instructions demand
CREDITS = re.compile(r"Select courses amounting to at least (\d+) credits")
CHOOSE = re.compile(
    r"(?:At least|Select) (one|two) (?:courses? from|out of the following)"
)
# The notes that hold no rule: the complementary list, where entries are and a timetable warning
KNOWN = (
    "see separate list of approved complementary studies courses",
    "course descriptions are set out in the section on departments",
    "note: some elective core courses in the first semester are in the same timetable",
)
NOTE_MARKS = ("*", "†", "Note:")


class Listed(Row):
    # A course row as a curriculum table prints it, to check against the course's entry
    curriculum: str
    year: int
    code: str
    credits: int
    nqf_level: int
    page: int


class Subtotal(Row):
    # A core table's printed total, and what its rows and complementary slot add up to
    curriculum: str
    year: int
    page: int
    printed: int
    summed: int


class Curricula(Row):
    curricula: tuple[Curriculum, ...]
    rules: tuple[CurriculumRule, ...]
    groups: tuple[CourseGroup, ...]
    members: tuple[CourseGroupMember, ...]
    readings: tuple[Reading, ...]
    # The year of study each curriculum takes each course in
    taken: dict[tuple[str, str], int]
    # Every code the curricula print, and each wildcard's courses
    scope: frozenset[str]
    listed: tuple[Listed, ...]
    subtotals: tuple[Subtotal, ...]
    # Each wildcard, such as CSC3xxx, and the courses it stands for
    expanded: dict[str, tuple[str, ...]]
    units: tuple[Unit, ...]


def read(book: Handbook, section: Section, year: int, department: str) -> Curricula:
    lines = book.section(section)
    reader = _Reader(book, year, department)
    for at in lines:
        reader.read(at)
    return reader.done(lines.stop)


class _Group:
    def __init__(self, label: str, page: int) -> None:
        self.label, self.page = label, page
        self.members: list[tuple[str, int, str]] = []  # each code, its page and its row


class _Year:
    # What one year's tables print, gathered before they become groups and a rule
    def __init__(self) -> None:
        self.groups: dict[str, _Group] = {}
        self.choose: int | None = None
        self.credits: int | None = None
        self.slots: list[int] = []
        self.summed = 0  # the core table's credits so far
        self.total: int | None = None
        self.pages: set[int] = set()


class _Reader:
    def __init__(self, book: Handbook, year: int, department: str) -> None:
        self.book, self.handbook_year, self.department = book, year, department
        self.curricula: list[tuple[Curriculum, int]] = []  # each with its page
        self.years: dict[tuple[str, int], _Year] = {}
        self.listed: list[Listed] = []
        # Each curriculum year's printed lines no rule shape can hold, for a person to judge
        self.notes: dict[tuple[str, int], list[str]] = defaultdict(list)
        self.subtotals: list[Subtotal] = []
        self.units: list[Unit] = []
        self.expanded: dict[str, tuple[str, ...]] = {}
        self.scope: set[str] = set()
        self.slot: int | None = None  # the page of the first complementary slot
        self.code = ""  # the curriculum being read
        # The table's year of study; None before the curriculum's first table
        self.year: int | None = None
        self.group: str | None = None  # where rows go; None for the optional courses
        self.columns = False  # whether the table's rows have started
        self.instructions: list[str] = []
        self.loose: list[int] = []  # lines not placed yet, which become notes
        self.unit: tuple[int, str] | None = None  # the open unit's first line and label

    def read(self, at: int) -> None:
        page, line = self.book.lines[at]
        if found := CURRICULUM.fullmatch(line):
            # The name is the run of lines above, back to the break
            start = at
            while self.book.lines[start - 1][1]:
                start -= 1
            self.loose = [k for k in self.loose if k < start]
            self._flush()
            name = " ".join(text for _, text in self.book.lines[start:at])
            self._open(start, name)
            self.code, self.year, self.group = found[1], None, None
            curriculum = Curriculum(
                handbook_year=self.handbook_year,
                code=self.code,
                name=name,
                department=self.department,
            )
            self.curricula.append((curriculum, page))
        elif found := TABLE.fullmatch(line):
            self._flush()
            label = line.rstrip("*†")
            self._open(at, label)
            self.year, self.columns, self.instructions = YEARS[found[1]], False, []
            year = self._year()
            year.pages.add(page)
            if "Elective" not in found[2]:
                self.group = self._core()
            else:
                self.group = self._elective(2 if "Further" in found[2] else 1)
            year.groups.setdefault(self.group, _Group(label, page))
        elif line == OPTIONAL:
            self._flush()
            self._open(at, line)
            self.group, self.columns, self.instructions = None, False, []
        elif line == COLUMNS:
            self._flush()
            if not self.columns:
                self._instruct()
            self.columns = True
        elif line.startswith(FURTHER):
            self._flush()
            if self.group != self._elective(2):
                self.group = self._elective(2)
                self._year().groups[self.group] = _Group(line.rstrip(":"), page)
        elif found := LISTED.fullmatch(line):
            self._flush()
            code, credits = found[1], int(found[2])
            self.listed.append(
                Listed(
                    curriculum=self.code,
                    year=self.year,
                    code=code,
                    credits=credits,
                    nqf_level=int(found[3]),
                    page=page,
                )
            )
            self._add((code,), credits, page, line)
        elif found := WILDCARD.fullmatch(line):
            self._flush()
            codes = tuple(sorted(c for c in self.book.starts if c.startswith(found[1])))
            if not codes:
                raise SourceError(
                    f"No entry's code starts with {found[1]} (page {page})"
                )
            self.expanded[found[1] + "xxx"] = codes
            self._add(codes, 0, page, line)
        elif found := SLOT.fullmatch(line):
            self._flush()
            self._year().slots.append(int(found[1]))
            self.slot = self.slot or page
            self._add((), int(found[1]), page, line)
        elif found := TOTAL.fullmatch(line):
            self._flush()
            year = self._year()
            year.total = int(found[3])
            year.pages.add(page)
            if self.group == self._core():
                self.subtotals.append(
                    Subtotal(
                        curriculum=self.code,
                        year=self.year,
                        page=page,
                        printed=year.total,
                        summed=year.summed,
                    )
                )
        elif self.year is not None and not self.columns:
            self.instructions.append(line)
        elif self.year is not None:
            self.loose.append(at)

    def done(self, end: int) -> Curricula:
        self._flush()
        self._close(end)
        handbook_year = self.handbook_year
        groups, members, rules, readings, taken = [], [], [], [], {}
        for curriculum, page in self.curricula:
            readings.append(
                Reading(
                    entity="curricula",
                    key=curriculum.code,
                    place=f"p. {page}",
                    printed=curriculum.name,
                )
            )
        for (code, number), year in self.years.items():
            for key, group in year.groups.items():
                groups.append(
                    CourseGroup(
                        handbook_year=handbook_year, group_key=key, label=group.label
                    )
                )
                readings.append(
                    Reading(
                        entity="course_groups",
                        key=key,
                        place=f"p. {group.page}",
                        printed=group.label,
                    )
                )
                for course, page, row in group.members:
                    members.append(
                        CourseGroupMember(
                            handbook_year=handbook_year,
                            group_key=key,
                            course_code=course,
                        )
                    )
                    readings.append(
                        Reading(
                            entity="course_group_members",
                            key=f"{key}/{course}",
                            place=f"p. {page}",
                            printed=row,
                        )
                    )
                    taken[code, course] = number
            notes = self.notes[code, number]
            rules.append(
                CurriculumRule(
                    handbook_year=handbook_year,
                    curriculum_code=code,
                    year_of_study=number,
                    rule=YearRules(all=self._rules(code, number, year)),
                )
            )
            readings.append(
                Reading(
                    entity="curriculum_rules",
                    key=f"{code}/{number}",
                    place=_pages(year.pages),
                    printed=" ".join(notes)
                    or "; ".join(g.label for g in year.groups.values()),
                    flag="refused_free_text" if notes else None,
                )
            )
        if self.slot is not None:
            label = "Approved complementary studies courses"
            groups.append(
                CourseGroup(
                    handbook_year=handbook_year, group_key=COMPLEMENTARY, label=label
                )
            )
            readings.append(
                Reading(
                    entity="course_groups",
                    key=COMPLEMENTARY,
                    place=f"p. {self.slot}",
                    printed=label,
                )
            )
        return Curricula(
            curricula=tuple(curriculum for curriculum, _ in self.curricula),
            rules=tuple(rules),
            groups=tuple(groups),
            members=tuple(members),
            readings=tuple(readings),
            taken=taken,
            scope=frozenset(self.scope),
            listed=tuple(self.listed),
            subtotals=tuple(self.subtotals),
            expanded=self.expanded,
            units=tuple(self.units),
        )

    def _rules(self, code: str, number: int, year: _Year) -> tuple[YearRule, ...]:
        core = f"{code}-y{number}-core"
        electives = tuple(key for key in year.groups if key != core)
        if electives and not (year.choose or year.credits):
            raise SourceError(
                f"{code} year {number}'s electives have no rule to pick them"
            )
        rules: list[YearRule] = []
        if core in year.groups:
            rules.append(AllOfGroup(all_of_group=core))
        if year.choose:
            rules.append(ChooseFromGroup(choose=year.choose, from_group=electives[0]))
        if year.credits:
            rules.append(CreditsFromGroups(credits=year.credits, from_groups=electives))
        rules += [
            CreditsFromGroups(credits=slot, from_groups=(COMPLEMENTARY,))
            for slot in year.slots
        ]
        if year.total is not None:
            rules.append(TotalCredits(total_credits=year.total))
        return tuple(rules)

    def _year(self) -> _Year:
        return self.years.setdefault((self.code, self.year), _Year())

    def _core(self) -> str:
        return f"{self.code}-y{self.year}-core"

    def _elective(self, number: int) -> str:
        return f"{self.code}-y{self.year}-group-{number}"

    def _add(self, codes: tuple[str, ...], credits: int, page: int, row: str) -> None:
        self.scope.update(codes)
        self._year().pages.add(page)
        if self.group is not None:
            self._year().groups[self.group].members += [
                (code, page, row) for code in codes
            ]
        if self.group == self._core():
            self._year().summed += credits

    def _instruct(self) -> None:
        # An elective table's instructions, read where its rows start
        text = " ".join(self.instructions)
        year = self._year()
        if found := CREDITS.search(text):
            year.credits = int(found[1])
        if found := CHOOSE.search(text):
            year.choose = COUNTS[found[1]]

    def _flush(self) -> None:
        # Loose lines become notes, one per paragraph or mark, and the codes they name join the scope
        paragraphs: list[list[int]] = []
        for at in self.loose:
            line = self.book.lines[at][1]
            if not line:
                continue
            if (
                not paragraphs
                or line.startswith(NOTE_MARKS)
                or not self.book.lines[at - 1][1]
            ):
                paragraphs.append([])
            paragraphs[-1].append(at)
        self.loose = []
        for paragraph in paragraphs:
            text = " ".join(self.book.lines[at][1] for at in paragraph)
            self.scope.update(re.findall(COURSE_CODE, text))
            page = self.book.lines[paragraph[0]][0]
            self._year().pages.add(page)
            if not text.lstrip("*† ").lower().startswith(KNOWN):
                self.notes[self.code, self.year].append(text)

    def _open(self, start: int, label: str) -> None:
        self._close(start)
        self.unit = (start, label)

    def _close(self, end: int) -> None:
        if self.unit is not None:
            start, label = self.unit
            self.units.append(
                Unit(
                    section=label,
                    page=self.book.lines[start][0],
                    line=start,
                    content=self.book.text(range(start, end)),
                    curriculum_code=self.code,
                )
            )


def _pages(pages: set[int]) -> str:
    first, last = min(pages), max(pages)
    return f"p. {first}" if first == last else f"pp. {first}-{last}"
