# Reads a UCT academic record, the transcript a student downloads from PeopleSoft, in two layers:
# pdf_pages turns the PDF into lines of text with pdfplumber, and read_lines turns those lines into
# her course history. It goes line by line, because table extraction failed on the real layout.
# Nothing from the file is kept or logged, and the name and birthdate printed on every page are
# never read.
import io
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Literal

import pdfplumber

from sage.shared.base import Row
from sage.shared.errors import (
    NoCourseHistory,
    NotATranscript,
    TranscriptIncomplete,
    TranscriptNotYours,
    TranscriptUnreadable,
)
from sage.shared.rules import TERM_BY_SUFFIX, TermCode
from sage.shared.students import average

logger = logging.getLogger(__name__)

HEADING = "ACADEMIC RECORD"
BEGINNING = "Beginning of Undergraduate Record"
END = "End of Academic Record"
CAMPUS_ID = re.compile(r"Campus ID:\s*([A-Z]{6}[0-9]{3})\b")  # the student number
PAGES = re.compile(r"\bPage [0-9]+ of ([0-9]+)\b")
ISSUED = re.compile(r"\bIssued on ([0-9]{2})/([0-9]{2})/([0-9]{4})\b")
YEAR = re.compile(r"[0-9]{4}")
TERM_GPA = re.compile(r"Term GPA:\s*([0-9]+\.[0-9]{2})")
# A course row: its code, printed with a space after the letters ("ASL 1200S"), then the rest
ROW = re.compile(r"([A-Z]{3}) ([0-9]{4})([A-Z])\b ?(.*)")
# The rest is read from its end, because descriptions can hold digits, colons and ampersands: the
# zero-padded NQF level, credits, the mark (or a symbol such as UP or GIP when there's no mark),
# then the result
GRADED = re.compile(r"(.+) ([0-9]{2}) ([0-9]+) ([0-9]{1,3}|[A-Z]+) (\S+)")
# A row with no result yet prints only its description and a credits column
UNGRADED = re.compile(r"(.+) ([0-9]+)")

WarningCode = Literal["term_gpa_mismatch", "recent_year_missing", "results_pending"]


class TranscriptLine(Row):
    academic_year: int
    term: TermCode
    course_code: str
    course_name: str
    credits: int  # as printed, even the 0 an ungraded row shows for a course that carries credits
    nqf_level: int | None
    result: str
    mark: int | None
    result_printed: bool  # false when the row had no result and GIP was filled in
    # The parser had to guess part of it, so the student should check it
    unverified: bool


class TranscriptWarning(Row):
    code: WarningCode
    message: str


class Transcript(Row):
    student_number: str
    programme: str | None  # the latest year's, as printed
    issued_on: date | None
    lines: tuple[TranscriptLine, ...]
    warnings: tuple[TranscriptWarning, ...] = ()


def pdf_pages(data: bytes) -> list[list[str]]:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [(page.extract_text() or "").splitlines() for page in pdf.pages]
    except Exception as error:
        # Damaged, locked with a password, or malformed in one of the many ways that crash the PDF
        # library on untrusted input, so any failure here is unreadable. Only the error's type is
        # logged, as its message can quote the file.
        logger.warning(
            "pdfplumber couldn't read a transcript: %s", type(error).__name__
        )
        raise TranscriptUnreadable() from error
    if not any(line.strip() for page in pages for line in page):
        # A scan or a photo: there's no text to read
        raise TranscriptUnreadable()
    return pages


def read_lines(pages: list[list[str]], student_number: str) -> Transcript:
    lines = [line.strip() for page in pages for line in page]
    campus_id = first(CAMPUS_ID, lines)
    if HEADING not in lines or campus_id is None:
        raise NotATranscript()
    printed_number = campus_id[1]
    # Checked before the record is read, so no more of another student's transcript is
    if printed_number != student_number:
        raise TranscriptNotYours(
            f"This transcript is for {printed_number}, but you're signed in as {student_number}.",
            transcript_student_number=printed_number,
            account_student_number=student_number,
        )
    printed_pages = [int(found[1]) for line in lines if (found := PAGES.search(line))]
    ends = [index for index, line in enumerate(lines) if END in line]
    if len(pages) < max(printed_pages, default=0) or not ends:
        raise TranscriptIncomplete()
    begins = [index for index, line in enumerate(lines) if BEGINNING in line]
    if not begins:
        # Course history is decided by rows, not by this line: with no row before the end line
        # there's none, but rows with nothing to say where the record starts can't be placed
        if any(ROW.fullmatch(line) for line in lines[: ends[0]]):
            raise TranscriptUnreadable()
        raise NoCourseHistory()
    record = lines[begins[0] + 1 : ends[0]]

    year, programme = None, None
    printed_gpa: dict[int, Decimal] = {}
    rows: list[TranscriptLine] = []
    for index, line in enumerate(record):
        following = record[index + 1] if index + 1 < len(record) else ""
        if YEAR.fullmatch(line) and following.startswith("Programme:"):
            # A year's heading. A page break repeats only the page header, so the year carries on
            # across it, and a lone number in that header can't pass for a year.
            year = int(line)
        elif line.startswith("Programme:"):
            programme = line.removeprefix("Programme:").strip()
        elif (gpa := TERM_GPA.fullmatch(line)) and year is not None:
            printed_gpa[year] = Decimal(gpa[1])
        elif row := ROW.fullmatch(line):
            if year is None:
                raise TranscriptUnreadable()
            rows.append(course(row, year))
    if not rows:
        raise NoCourseHistory()

    lines_read, warnings = checked(rows, printed_gpa)
    return Transcript(
        student_number=printed_number,
        programme=programme,
        issued_on=issued_on(lines),
        lines=lines_read,
        warnings=warnings,
    )


def first(pattern: re.Pattern[str], lines: list[str]) -> re.Match[str] | None:
    return next((found for line in lines if (found := pattern.search(line))), None)


def issued_on(lines: list[str]) -> date | None:
    # The date the record was issued, or None when it has none or one that can't exist, such as
    # 31/02/2026
    issued = first(ISSUED, lines)
    if issued is None:
        return None
    day, month, year = (int(part) for part in issued.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def checked(
    rows: list[TranscriptLine], printed_gpa: dict[int, Decimal]
) -> tuple[tuple[TranscriptLine, ...], tuple[TranscriptWarning, ...]]:
    # Flags what the student should check. A missing result is normal in the latest year, whose
    # results aren't all out, but anywhere else it's a guess. And each year's lines should give back
    # the Term GPA printed under them: if they don't, something in that year was misread.
    latest = max(row.academic_year for row in rows)
    mismatched = set()
    for year, printed in printed_gpa.items():
        lines = [row for row in rows if row.academic_year == year]
        if lines and (average(lines) or Decimal("0.00")) != printed:
            mismatched.add(year)
    flagged = tuple(
        row.model_copy(update={"unverified": True})
        if row.academic_year in mismatched
        or (not row.result_printed and row.academic_year != latest)
        else row
        for row in rows
    )
    warnings = tuple(
        TranscriptWarning(
            code="term_gpa_mismatch",
            message=f"Your {year} lines don't add up to the Term GPA printed for {year}, "
            "so check them carefully.",
        )
        for year in sorted(mismatched)
    )
    return flagged, warnings


def course(row: re.Match[str], year: int) -> TranscriptLine:
    letters, digits, suffix, rest = row.groups()
    term = TERM_BY_SUFFIX.get(suffix)
    common = {
        "academic_year": year,
        "term": term or "other",
        "course_code": letters + digits + suffix,
        "unverified": term is None,  # a suffix outside the handbook's key
    }
    if graded := GRADED.fullmatch(rest):
        name, nqf, credits, mark, result = graded.groups()
        return TranscriptLine(
            **common,
            course_name=name,
            credits=int(credits),
            nqf_level=int(nqf),
            result=result,
            mark=int(mark) if mark.isdigit() else None,
            result_printed=True,
        )
    if ungraded := UNGRADED.fullmatch(rest):
        name, credits = ungraded.groups()
        return TranscriptLine(
            **common,
            course_name=name,
            credits=int(credits),
            nqf_level=None,
            result="GIP",
            mark=None,
            result_printed=False,
        )
    raise TranscriptUnreadable()
