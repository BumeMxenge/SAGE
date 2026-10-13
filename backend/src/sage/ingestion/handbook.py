# Reads a faculty handbook in two layers, like the transcript reader: pages turns the PDF into each
# page's printed number and body lines with pdfplumber, and Handbook reads course entries from those
# lines. Only the entries asked for are parsed, so a department held out of development is never read.
import re
from collections.abc import Sequence
from pathlib import Path

import pdfplumber

from sage.domain.base import Row
from sage.domain.rules import Passage, TermCode
from sage.ingestion.names import title_case
from sage.ingestion.sources import Section, SourceError, row_id

# Points from the top of a page. Every running header in both books ends above it (at 37.6) and every
# body starts below it (at 57.3), so cropping here drops the header and nothing else.
CROP = 45
# Lines of a paragraph sit at most 4.2 points apart. A wider gap, or a line set in larger type than
# the one before it (a heading, even at the top of a page), is a break, kept as an empty line.
GAP = 5

CODE = r"[A-Z]{3}\d{4}[A-Z]"
# An entry's heading: its code, with any other term it runs in (EEE4022F/S), then its title
HEADING = re.compile(rf"({CODE}(?:/[A-Z])*)\s+(\S.*)")
CREDITS = re.compile(r"(\d+) NQF credits at NQF level (\d+)(.*)")
# A rule clause's number opening a line, such as FB8.10
CLAUSE = re.compile(r"([A-Z]{2}(\d+(?:\.\d+)*))\s")
# A term printed after the credits, as in "; First-year, second semester course."
PRINTED_TERM = re.compile(r"\b(first|second)[ -]semester\b", re.IGNORECASE)
TERMS: dict[str, TermCode] = {"first": "sem1", "second": "sem2"}
LABELS = (
    "Convener:",
    "Course entry requirements:",
    "Co-requisites:",
    "Objective:",
    "Course outline:",
    "Lecture times:",
    "DP requirements:",
    "Assessment:",
)


class Page(Row):
    number: int  # as printed in the running header
    lines: tuple[str, ...]  # the body below the header, with "" for each break


class Unit(Row):
    # One printed unit, which becomes a passage: a rule clause, a course entry, a curriculum table or
    # a section the manifest lists
    section: str  # its label, such as "FB8.10" or "First Year Core Courses (EE)"
    page: int
    line: int  # where it starts among the book's lines, which orders the passages
    content: str
    curriculum_code: str | None = None
    course_code: str | None = None


class Entry(Row):
    codes: tuple[str, ...]  # every code its heading prints
    name: str
    credits: int
    nqf_level: int
    term: TermCode | None  # when the credits line prints one
    convener: str | None
    # As printed; None when the entry prints no requirement line
    requirement: str | None
    corequisite: str | None
    page: int
    content: str  # the entry word for word, from its heading


def pages(path: Path) -> list[Page]:
    read = []
    # The type size of the line above, carried over a page break. The book's first line has none.
    size = float("inf")
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            header = page.crop((0, 0, page.width, CROP)).extract_words()
            numbers = [word["text"] for word in header if word["text"].isdigit()]
            if not numbers:
                continue  # a cover, which has no running header
            (number,) = numbers  # a header with two numbers fails loudly
            lines, bottom = [], None
            body = page.crop((0, CROP, page.width, page.height))
            for line in body.extract_text_lines():
                line_size = max(char["size"] for char in line["chars"])
                if (bottom is not None and line["top"] - bottom > GAP) or (
                    line_size > size + 0.5
                ):
                    lines.append("")
                lines.append(line["text"])
                bottom, size = line["bottom"], line_size
            read.append(Page(number=int(number), lines=tuple(lines)))
    return read


class Handbook:
    # The book's body lines in reading order, each with its printed page, and where every course
    # entry's heading is
    def __init__(self, pages: Sequence[Page]) -> None:
        self.lines = [(page.number, line) for page in pages for line in page.lines]
        self.headings = [
            at for at, (_, line) in enumerate(self.lines) if self._is_heading(at, line)
        ]
        self.starts: dict[str, list[int]] = {}
        for at in self.headings:
            for code in _codes(HEADING.fullmatch(self.lines[at][1])[1]):
                self.starts.setdefault(code, []).append(at)

    def _is_heading(self, at: int, line: str) -> bool:
        # A line opening with a code, whose credits line comes before any field label or another
        # code's line. A requirement's second line can open with a code too, but a label follows it.
        if not HEADING.fullmatch(line):
            return False
        for k in range(at + 1, len(self.lines)):
            later = self.lines[k][1]
            if CREDITS.match(later):
                return True
            if later.startswith(LABELS) or HEADING.fullmatch(later):
                return False
        return False

    def entry(self, code: str) -> Entry | None:
        starts = self.starts.get(code, [])
        if not starts:
            return None
        if len(starts) > 1:
            pages = ", ".join(str(self.lines[at][0]) for at in starts)
            raise SourceError(f"{code} has an entry on each of pages {pages}")
        at = starts[0]
        page, heading = self.lines[at]
        printed, title = HEADING.fullmatch(heading).groups()
        at += 1
        # A title too long for one line carries on in capitals
        while self.lines[at][1] and not re.search("[a-z]", self.lines[at][1]):
            title += " " + self.lines[at][1]
            at += 1
        while not (credits := CREDITS.match(self.lines[at][1])):
            at += 1  # a note under the title, such as who the course is for
        fields: dict[str, list[str]] = {}
        label, end = None, self._next_heading(at)
        for k in range(at + 1, end):
            line = self.lines[k][1]
            if label == "Assessment:" and not line:
                end = k  # the last field's paragraph is over
                break
            if line.startswith(LABELS):
                label = next(name for name in LABELS if line.startswith(name))
                fields[label] = [line.removeprefix(label)]
            elif label is not None:
                fields[label].append(line)
        if "Assessment:" not in fields:
            raise SourceError(
                f"{code}'s entry on page {page} prints no Assessment line"
            )
        term = PRINTED_TERM.search(credits[3])
        return Entry(
            codes=_codes(printed),
            name=title_case(title),
            credits=int(credits[1]),
            nqf_level=int(credits[2]),
            term=TERMS[term[1].lower()] if term else None,
            convener=_field(fields, "Convener:"),
            requirement=_field(fields, "Course entry requirements:"),
            corequisite=_field(fields, "Co-requisites:"),
            page=page,
            content=self.text(range(starts[0], end)),
        )

    def _next_heading(self, at: int) -> int:
        return next((h for h in self.headings if h > at), len(self.lines))

    def section(self, section: Section) -> range:
        # A listed section's lines: from its printed heading on its first page to the heading named
        # by until, or to the end of its last page
        first, last = section.pages
        start = self._find(section.section, first, first, 0)
        if section.until is not None:
            return range(start, self._find(section.until, first, last, start))
        ends = [at for at, (page, _) in enumerate(self.lines) if page == last]
        return range(start, ends[-1] + 1)

    def _find(self, heading: str, first: int, last: int, after: int) -> int:
        for at in range(after, len(self.lines)):
            page, line = self.lines[at]
            if first <= page <= last and line.casefold() == heading.casefold():
                return at
        raise SourceError(f"No heading {heading!r} between pages {first} and {last}")

    def text(self, lines: range) -> str:
        return "\n".join(self.lines[at][1] for at in lines).strip()

    def prose(self, sections: Sequence[Section]) -> list[Unit]:
        # One unit per listed section, or one per rule clause where a section prints clause
        # numbers. A section with no until heading ends where the next listed section starts, when
        # that comes before the end of its last page.
        spans = [self.section(section) for section in sections]
        units = []
        for at, (lines, section) in enumerate(zip(spans, sections, strict=True)):
            end = lines.stop
            if at + 1 < len(spans) and lines.start < spans[at + 1].start < end:
                end = spans[at + 1].start
            units += self._cut(range(lines.start, end), section.section)
        return units

    def _cut(self, lines: range, label: str) -> list[Unit]:
        # A clause runs from the paragraph its number opens, taking in any heading printed above the
        # number, to the next clause. A page's first line opens a paragraph too, so a heading at the
        # top of a page stays with the clause below it. Clause numbers only go up, so one that
        # doesn't, as in "Rule FB3.1 above also applies", refers back rather than opening a clause.
        starts = [(lines.start, label)]
        paragraph, clause, number = lines.start, -1, ()
        for at in lines:
            page, line = self.lines[at]
            if not line:
                paragraph = at + 1
            elif page != self.lines[at - 1][0]:
                paragraph = at
            found = CLAUSE.match(line)
            if found and (printed := tuple(map(int, found[2].split(".")))) > number:
                starts.append((paragraph if clause < paragraph else at, found[1]))
                clause, number = at, printed
        ends = [start for start, _ in starts[1:]] + [lines.stop]
        return [
            Unit(
                section=name,
                page=self.lines[start][0],
                line=start,
                content=self.text(range(start, end)),
            )
            for (start, name), end in zip(starts, ends, strict=True)
            if start < end
        ]


def passages(units: Sequence[Unit], year: int, source: str) -> tuple[Passage, ...]:
    # A book's units as passages, numbered in printed order
    ordered = sorted(units, key=lambda unit: unit.line)
    rows = []
    for position, unit in enumerate(ordered, start=1):
        row = {
            "handbook_year": year,
            "source": source,
            "position": position,
            **unit.model_dump(exclude={"line"}),
        }
        rows.append(Passage(id=row_id(row), **row))
    return tuple(rows)


def _codes(printed: str) -> tuple[str, ...]:
    code, *terms = printed.split("/")
    return (code, *(code[:-1] + term for term in terms))


def _field(fields: dict[str, list[str]], label: str) -> str | None:
    return " ".join(" ".join(fields[label]).split()) if label in fields else None
