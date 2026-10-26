# What a handbook prints that its approved rules can't hold, kept here until a rule shape can: the
# degree's credit total, the 576-credit curriculum's two extra core courses and where each 2026
# curriculum places them, and two notes on elective tables. Each place and note names the table
# whose passage prints it. With the meetings in shared/printed_meetings.py and my theme words in
# themes.py, this is the only curriculum data in the code, and docs/shortfalls.md logs each.
from sage.shared.base import Row

# The curricula whose first page prints their degree's credit total, in 2023 and 2026
CURRICULA = (
    "EB009EEE01",
    "EB809EEE01",
    "EB022EEE02",
    "EB822EEE02",
    "EB011EEE05",
    "EB811EEE05",
)
# The year the 560-credit curriculum starts: a student who registered before it is on the 576-credit
# one
CHANGE = 2025
# Each year's degree total for a student registered before the change and from it. 2026 prints 560
# for "A candidate who registers in 2025" and 576 before, and 2023 prints 576 for everyone.
DEGREE_CREDITS = {
    2023: dict.fromkeys(CURRICULA, (576, 576)),
    2026: dict.fromkeys(CURRICULA, (576, 560)),
}


class Place(Row):
    # A course the 576-credit curriculum makes core, which a student who still owes it fills with an
    # approved complementary studies course of at least 8 credits instead, timetable permitting
    code: str
    year: int  # the year of study whose table carries its footnote mark
    table: str  # the table whose passage prints the footnote
    credits: int = 8


# 2026's footnotes, by the year each curriculum's marks place them. EB022 marks CON2026S on its first
# and second years' tables, so it counts from the first.
PLACES = {
    "EB009EEE01": (
        Place(code="ASL1200S", year=1, table="First Year Core Courses (EE)"),
        Place(code="CON2026S", year=1, table="Second Year Core Courses (EE)"),
    ),
    "EB022EEE02": (
        Place(code="ASL1200S", year=1, table="First Year Core Courses (EC)"),
        Place(code="CON2026S", year=1, table="Second Year Core Courses (EC)"),
    ),
    "EB011EEE05": (
        Place(code="ASL1200S", year=2, table="First Year Core Courses (ME)"),
        Place(code="CON2026S", year=2, table="Second Year Core Courses (ME)"),
    ),
    "EB809EEE01": (
        Place(code="CON2026S", year=2, table="Second Year Core Courses (EE)"),
        Place(code="ASL1200S", year=3, table="Third Year Core Courses (EE)"),
    ),
    "EB811EEE05": (
        Place(code="CON2026S", year=2, table="Second Year Core Courses (ME)"),
        Place(code="ASL1200S", year=3, table="Third Year Core Courses (ME)"),
    ),
    "EB822EEE02": (
        Place(code="CON2026S", year=2, table="Second Year Core Courses (EC)"),
        Place(code="ASL1200S", year=3, table="Third Year Core Courses (EC)"),
    ),
}
PLACES_YEAR = 2026  # the handbook whose footnotes these are


class Note(Row):
    # A note printed under a year's table, quoted as printed
    table: str
    words: str


# 2026's note on EB009's and EB809's final-year elective tables (pp. 49 and 51), which names no
# courses, and note (i) on the EC curricula's third-year elective tables (pp. 53 and 56)
SAME_SLOTS = {
    ("EB009EEE01", 4): Note(
        table="Fourth Year Elective Core Courses (EE)",
        words="Some elective core courses in the first semester are in the same timetable "
        "slots and cannot be taken concurrently.",
    ),
    ("EB809EEE01", 5): Note(
        table="Fifth Year Elective Core Courses (EE)",
        words="some elective core courses in the first semester are in the same timetable "
        "slots and cannot be taken concurrently.",
    ),
}
ALL_THREE = {
    ("EB022EEE02", 3): Note(
        table="Third Year Elective Core Courses (EC)",
        words="All three elective 3rd year core courses can be taken; however, but then the "
        "complementary studies elective should then be taken in the winter or summer term.",
    ),
    ("EB822EEE02", 4): Note(
        table="Fourth Year Elective Core Courses (EC)",
        words="All three elective 3rd year core courses can be taken, but then the "
        "complementary studies elective must be taken in the winter or summer term.",
    ),
}
