# What a handbook prints that its approved rules can't hold, kept here until a rule shape can: the
# degree's credit total, the 576-credit curriculum's two extra core courses and where each 2026
# curriculum places them, two notes on elective tables, and meetings the department's timetable
# leaves out. Each entry names the table whose passage prints it, and each meeting is printed in its
# course's own entry. This is the only curriculum data in the code, and docs/shortfalls.md logs it.
from datetime import time
from itertools import combinations
from uuid import UUID, uuid5

from sage.shared.base import Row
from sage.shared.rules import TERM_BY_SUFFIX, RuleSet, TimetableSlot

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

DAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
)  # a meeting's days 1 to 5
MEETING_IDS = UUID(int=2026)  # the namespace of the printed meetings' ids


def meeting(
    code: str,
    kind: str,
    day: int | None = None,
    hours: tuple[time, time] | None = None,
    choice: str | None = None,
) -> TimetableSlot:
    # A printed meeting as a timetable row, in its course's term, with an id made from what it is,
    # so the same meeting always has the same id
    start, end = hours or (None, None)
    return TimetableSlot(
        id=uuid5(MEETING_IDS, f"{code}/{kind}/{day}/{choice}"),
        handbook_year=2026,
        course_code=code,
        term=TERM_BY_SUFFIX[code[-1]],
        day=day,
        start_time=start,
        end_time=end,
        kind=kind,
        choice_group=kind if choice else None,
        choice=choice,
    )


def lectures(code: str, start: time, end: time) -> tuple[TimetableSlot, ...]:
    # A lecture every weekday
    return tuple(meeting(code, "lecture", day, (start, end)) for day in range(1, 6))


def practicals(code: str) -> tuple[TimetableSlot, ...]:
    # Two 4-hour practicals a week, 14:00 to 18:00, on two weekdays the entry leaves open. Each pair
    # of days is one alternative of a choice, so a plan picks two days that work for all of it at
    # once, and the two never share a day.
    return tuple(
        meeting(
            code,
            "practical",
            day,
            (time(14), time(18)),
            f"{DAYS[first - 1]} and {DAYS[second - 1]}",
        )
        for first, second in combinations(range(1, 6), 2)
        for day in (first, second)
    )


# 2026's meetings for the Science department's practicals and its second-semester third-year
# courses, as their entries print them (p. 171). CSC3024S's lectures follow its two entries, this
# handbook's and the Science handbook's (p. 248), where the Science handbook's Schedule of Courses
# (p. 240) prints the 4th period on Monday, Thursday and Friday.
MEETINGS = {
    2026: (
        *practicals("CSC3002F"),
        *lectures("CSC3003S", time(9), time(9, 45)),
        *practicals("CSC3003S"),
        *lectures("CSC3024S", time(10), time(10, 45)),
        meeting("CSC3024S", "practical"),  # "by arrangement", so untimed
    )
}


def timetabled(rules: RuleSet) -> RuleSet:
    # The year's rules with the meetings its course entries print beside the department's timetable
    (version,) = rules.handbook_versions
    added = MEETINGS.get(version.year, ())
    return rules.model_copy(
        update={"timetable_slots": (*rules.timetable_slots, *added)}
    )
