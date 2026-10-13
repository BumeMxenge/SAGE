# Reads the requirement fields printed in course entries, "Course entry requirements" and
# "Co-requisites", with each course's code and printed page, and writes E2's data: the development
# fields the grammar was written from. Only the page ranges below are read, and none of them shares
# a page with Chemical Engineering or Construction Economics, ATP-1's held-out departments.
import csv
import re
from collections.abc import Callable
from functools import partial
from pathlib import Path

import pdfplumber

HERE = Path(__file__).parent
SOURCES = HERE.parents[2] / "data" / "sources"

# Each department holding a development course, by its printed pages in the contents: from its
# first page to the one the next department starts on, where its last entry can end. Electrical
# starts a page late, as its first page is shared with Construction Economics.
DEVELOPMENT_PAGES = {
    2023: {
        "Electrical Engineering": (126, 142),
        "Mechanical Engineering": (142, 157),
        "Human Biology": (166, 167),
        "African Studies and Linguistics": (167, 168),
        "Commercial Law": (168, 172),
        "Computer Science": (175, 179),
        "Mathematics and Applied Mathematics": (183, 189),
        "Physics": (189, 194),
    },
    2026: {
        "Electrical Engineering": (127, 142),
        "Mechanical Engineering": (142, 157),
        "Human Biology": (162, 163),
        "Commercial Law": (163, 165),
        "Computer Science": (168, 172),
        "Mathematics and Applied Mathematics": (178, 187),
        "Physics": (187, 192),
    },
}
# The courses the six Electrical curricula list each year, as (year, code), as branch A read them
# from the tables when it wrote the grammar. CON2026S is left out: its entry sits in Construction
# Economics and prints no requirement.
LISTED = {
    (int(row["year"]), row["code"])
    for row in csv.DictReader(
        (HERE / "data" / "development-courses.csv")
        .read_text(encoding="utf-8")
        .splitlines()
    )
}

# The running header sits above 38 pt and the body starts below 57 pt on every page of both books
BODY_TOP = 45
# An entry's heading: its code, any other terms it runs in (MAM2084F/S) and its title. Curriculum
# tables print codes too, but with dot leaders, and only an entry has its credits just below.
ENTRY = re.compile(r"^([A-Z]{3}\d{4})([A-Z](?:/[A-Z])*)\s+\S")
FIELD = re.compile(r"^(Course entry requirements|Co-requisites):\s*(.*)$")
# The next part of an entry, such as "Course outline:" or "DP requirements:", which ends a field
LABEL = re.compile(r"^[A-Z][A-Za-z’' ]{1,40}:")


def development_course(year: int, code: str) -> bool:
    # A course the curricula list that year, or a third-year Computer Science course
    return (year, code) in LISTED or code.startswith("CSC3")


def fields(
    pdf: pdfplumber.PDF, first: int, last: int, wanted: Callable[[str], bool]
) -> list[tuple[str, str, int, str]]:
    # The requirement fields of the wanted courses' entries on these printed pages, each as the
    # course's code, the field's name, its page and its text on one line. An entry counts if any
    # code it prints is wanted, as MAM2084F/S is for MAM2084S. Page indexes are printed pages.
    lines = []
    for number in range(first, last + 1):
        page = pdf.pages[number]
        body = page.crop((0, BODY_TOP, page.width, page.height)).extract_text()
        lines += [(number, line) for line in body.splitlines()]
    found, code, field = [], None, None
    for at, (number, line) in enumerate(lines):
        head = ENTRY.match(line)
        if (
            head
            and "..." not in line
            and any("NQF credits" in text for _, text in lines[at + 1 : at + 9])
        ):
            codes = (head[1] + term for term in head[2].split("/"))
            code, field = next(filter(wanted, codes), None), None
        elif code and (match := FIELD.match(line)):
            field = (code, match[1], number, [match[2]])
            found.append(field)
        elif field and not LABEL.match(line) and "NQF credits" not in line:
            field[3].append(line)
        else:
            field = None
    if field:
        raise ValueError(
            f"p. {last}: {field[0]}'s field may run on past the pages read"
        )
    return [
        (code, name, page, " ".join(" ".join(parts).split()))
        for code, name, page, parts in found
    ]


def development() -> dict[tuple[str, str], list[str]]:
    # The distinct fields of the development courses in both years, with the courses printing each
    printed_by: dict[tuple[str, str], list[str]] = {}
    for year, departments in DEVELOPMENT_PAGES.items():
        with pdfplumber.open(SOURCES / str(year) / f"EBE_{year}.pdf") as pdf:
            for first, last in departments.values():
                wanted = partial(development_course, year)
                for code, name, page, text in fields(pdf, first, last, wanted):
                    courses = printed_by.setdefault((name, text), [])
                    # Neighbouring ranges share a page, so an entry there is read twice
                    if f"{code} {year} p. {page}" not in courses:
                        courses.append(f"{code} {year} p. {page}")
    return printed_by


if __name__ == "__main__":
    printed_by = development()
    rows = [
        [name, text, "; ".join(courses)]
        for (name, text), courses in sorted(printed_by.items())
    ]
    with (HERE / "data" / "development.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        csv.writer(file, lineterminator="\n").writerows(
            [["field", "text", "printed_by"], *rows]
        )
    print(f"Development: {len(printed_by)} distinct fields")
