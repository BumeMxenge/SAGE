# Makes ATP-1's transcripts: made-up academic records in the layout of the one a student downloads
# from PeopleSoft, as backend/tests/fixtures/transcript.txt prints it, each with the course rows it
# prints. They're new, so they aren't the unit tests' fixture, and seed 4022 fixes every choice. Each
# record prints every kind of row: passes, a fail, a refused DP, a pending supplementary, grades in
# progress, and the repeat of a course failed the year before.
import random
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

SEED = 4022
# Made-up students, each with a number ending 999 as every invented one does, and the years their
# records cover
STUDENTS = (
    ("ATPONE999", "Example, Ayanda", (2023, 2024, 2025)),
    ("ATPTWO999", "Sample, Lerato", (2024, 2025, 2026)),
    ("ATPTRE999", "Specimen, Kagiso", (2023, 2024, 2025)),
)
# The year whose second-semester results aren't out yet, so its S courses print no result
IN_PROGRESS = 2026
PROGRAMME = "Bachelor of Science in Engineering in Electrical Engineering"
# Courses by year of study as a record prints them: code, description, NQF level and credits
FIRST = (
    ("ASL1200S", "Africa: Culture, ID & Glblsn", 5, 8),
    ("CSC1015F", "Computer Science 1015", 5, 18),
    ("CSC1016S", "Computer Science 1016", 5, 18),
    ("EEE1006F", "Intro Electronic Engineering", 5, 12),
    ("EEE1007S", "Intro Electrical Engineering", 5, 12),
    ("MAM1020F", "Mathematics 1A for Engineers", 5, 18),
    ("MAM1021S", "Mathematics 1B for Engineers", 5, 18),
    ("MEC1003F", "Engineering Drawing", 5, 8),
    ("PHY1012F", "Physics A for Engineers", 5, 18),
    ("PHY1013S", "Physics B for Engineers", 5, 18),
)
SECOND = (
    ("CON2026S", "Project Management", 6, 8),
    ("EEE2044S", "Introduction to Power Eng", 6, 16),
    ("EEE2045F", "Analogue Electronics", 6, 16),
    ("EEE2046F", "Embedded Systems I", 6, 16),
    ("EEE2047S", "Signals and Systems I", 6, 16),
    ("EEE2048F", "Prof Comm for Elec Eng", 6, 8),
    ("MAM2083F", "Vector Calculus for Engineers", 6, 16),
    ("MAM2084S", "Linear Alg & De for Engineers", 6, 16),
    ("MEC1009F", "Intro to Engineering Mechanics", 5, 16),
    ("PHY2010S", "Electromagnetism for Engineers", 6, 16),
)
THIRD = (
    ("ECO2007S", "Cooperation and Competition", 6, 18),
    ("EEE3088F", "Design Principles", 7, 8),
    ("EEE3090F", "Electronic Devices & Circuits", 7, 16),
    ("EEE3091F", "Energy Conversion I", 7, 16),
    ("EEE3092F", "Signals & Systems II", 7, 16),
    ("EEE3094S", "Control Systems Engineering", 7, 16),
    ("EEE3096S", "Embedded Systems II", 7, 16),
    ("EEE3099S", "Engineering Design: ME", 7, 8),
    ("MEC2045S", "Applied Engineering Mechanics", 6, 16),
    ("MEC2047F", "Engineering Dynamics", 6, 16),
)
# Practical training, which carries no credits and stays in progress until it's signed off
PRACTICAL = ("EEE1000X", "Practical Training", 5, 0)
BEGINNING = "– – – – – Beginning of Undergraduate Record – – – – –"
END = "– – – – – End of Academic Record – – – – –"
COLUMNS = ("Course Description NQF NQF Result", "Level Credits")
FOOTER = (
    "This copy is for the student's own use. Ask the Student Records Office about any line you",
    "think is wrong.",
    "Issued on 05/02/2026 09:30",
)
# Lines of record on a page before it breaks, which it does only between two course rows
PAGE = 32

Course = tuple[str, str, int, int]


class Row(NamedTuple):
    # A course row as the record prints it, which the reader should give back as one line
    year: int
    code: str
    name: str
    nqf: int | None  # None for a row with no result yet, which prints no NQF level
    credits: int
    mark: int | None
    result: str
    kind: str  # pass, fail, dp_refused, supp_pending, in_progress or repeat


class Record(NamedTuple):
    number: str  # the student number it prints
    text: str  # its pages, split by form feeds, as tests/pdf.py prints them
    rows: tuple[Row, ...]


def records() -> list[Record]:
    choose = random.Random(SEED)
    return [record(number, name, years, choose) for number, name, years in STUDENTS]


def record(
    number: str, name: str, years: tuple[int, int, int], choose: random.Random
) -> Record:
    # Three years: the first fails one course and has a DP refused, the second repeats the failed
    # course and has a supplementary pending, practical training is in progress in both, and an
    # unfinished last year prints its S courses with no result
    first, second, third = years
    failed, refused, *passed = choose.sample(FIRST, 7)
    rows = [
        graded(first, failed, choose.randint(30, 44), "F", "fail"),
        unmarked(first, refused, "DPR", "dp_refused"),
        unmarked(first, PRACTICAL, "GIP", "in_progress"),
        *(passing(first, course, choose, "pass") for course in passed),
    ]
    supplementary, *passed = choose.sample(SECOND, 6)
    rows += [
        passing(second, failed, choose, "repeat"),
        graded(second, supplementary, choose.randint(45, 49), "FS", "supp_pending"),
        unmarked(second, PRACTICAL, "GIP", "in_progress"),
        *(passing(second, course, choose, "pass") for course in passed),
    ]
    if third == IN_PROGRESS:
        terms = {suffix: [c for c in THIRD if c[0].endswith(suffix)] for suffix in "FS"}
        rows += [
            passing(third, c, choose, "pass") for c in choose.sample(terms["F"], 3)
        ]
        rows += [awaited(third, c) for c in choose.sample(terms["S"], 3)]
    else:
        rows += [passing(third, c, choose, "pass") for c in choose.sample(THIRD, 6)]
    return Record(number, pages(number, name, rows), tuple(rows))


def graded(year: int, course: Course, mark: int, result: str, kind: str) -> Row:
    code, name, nqf, credits = course
    return Row(year, code, name, nqf, credits, mark, result, kind)


def passing(year: int, course: Course, choose: random.Random, kind: str) -> Row:
    mark = choose.randint(50, 92)
    # A pass's class, as the record's key prints it: 1 from 75, 2+ from 70, 2- from 60, else 3
    result = "1" if mark >= 75 else "2+" if mark >= 70 else "2-" if mark >= 60 else "3"
    return graded(year, course, mark, result, kind)


def unmarked(year: int, course: Course, result: str, kind: str) -> Row:
    # A result with no mark, whose symbol the record prints where the mark would go, as in GIP GIP
    code, name, nqf, credits = course
    return Row(year, code, name, nqf, credits, None, result, kind)


def awaited(year: int, course: Course) -> Row:
    # A course whose result isn't out, which prints only its description and 0 credits
    code, name, _, _ = course
    return Row(year, code, name, None, 0, None, "GIP", "in_progress")


def pages(number: str, name: str, rows: Sequence[Row]) -> str:
    # The record's lines, each year with its rows by code and its Term GPA, cut into pages that each
    # print the record's heading and its footer. A page breaks only between two course rows, and the
    # next repeats the column headings, so a year's heading always reaches its rows.
    body = [(BEGINNING, False)]
    for year in sorted({row.year for row in rows}):
        theirs = sorted((row for row in rows if row.year == year), key=lambda r: r.code)
        body += [
            (str(year), False),
            (f"Programme: {PROGRAMME}", False),
            ("Specialisation: Electrical Engineering", False),
            *((heading, False) for heading in COLUMNS),
            *((printed(row), True) for row in theirs),
            (f"Term GPA: {gpa(theirs)}", False),
            ("Academically eligible to continue", False),
        ]
    body += [
        (END, False),
        ("________________________________", False),
        ("Registrar", False),
    ]
    cut, page = [], []
    for at, (line, is_row) in enumerate(body):
        page.append(line)
        if len(page) >= PAGE and is_row and at + 1 < len(body) and body[at + 1][1]:
            cut.append(page)
            page = list(COLUMNS)
    cut.append(page)

    def heading(number_of: int) -> list[str]:
        return [
            f"Page {number_of} of {len(cut)}",
            "ACADEMIC RECORD",
            "(RETRIEVED VIA SELF-SERVICE)",
            f"Name: {name}",
            f"Campus ID: {number} Student Records Office",
            "Birthdate: 01/01/2005 Box 1",
            "Sampletown",
            "8000",
            "Exampleland",
            "Telephone +27 00 000 0000",
        ]

    return "\f".join(
        "\n".join([*heading(at), *lines, *FOOTER]) for at, lines in enumerate(cut, 1)
    )


def printed(row: Row) -> str:
    # A course row as the record prints it: the code with a space after its letters, the
    # description, then the NQF level, credits, mark and result, or only the credits before a
    # result is out
    code = f"{row.code[:3]} {row.code[3:]}"
    if row.nqf is None:
        return f"{code} {row.name} {row.credits}"
    mark = row.result if row.mark is None else row.mark
    return f"{code} {row.name} {row.nqf:02d} {row.credits} {mark} {row.result}"


def gpa(rows: Sequence[Row]) -> str:
    # The year's Term GPA as UCT prints it: the credit-weighted mean of its marks, to two decimals,
    # half up, or 0.00 before any mark is out. No row is a supplementary pass, which counts as 50.
    marked = [row for row in rows if row.mark is not None]
    weight = sum(row.credits for row in marked)
    total = sum(row.mark * row.credits for row in marked)
    mean = Decimal(total) / weight if weight else Decimal(0)
    return str(mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
