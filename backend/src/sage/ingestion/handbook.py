# Reads a faculty handbook in two layers, like the transcript reader: pages turns the PDF into each
# page's printed number and body lines with pdfplumber, and Handbook reads course entries from those
# lines. Only the entries asked for are parsed, so a department held out of development is never read.
import re
from collections.abc import Sequence
from pathlib import Path

import pdfplumber

from sage.domain.base import Row
from sage.domain.rules import TermCode
from sage.ingestion.names import title_case
from sage.ingestion.sources import SourceError

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
            content="\n".join(line for _, line in self.lines[starts[0] : end]).strip(),
        )

    def _next_heading(self, at: int) -> int:
        return next((h for h in self.headings if h > at), len(self.lines))


def _codes(printed: str) -> tuple[str, ...]:
    code, *terms = printed.split("/")
    return (code, *(code[:-1] + term for term in terms))


def _field(fields: dict[str, list[str]], label: str) -> str | None:
    return " ".join(" ".join(fields[label]).split()) if label in fields else None
