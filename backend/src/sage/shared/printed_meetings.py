# Meetings a year's course entries print that the department's timetable leaves out. The rulebook
# adds them to each year it reads, and so does the show script, so every reader of a year's rules
# sees the same week: the plan generator, a plan's meetings and the questionnaire. Each meeting is
# printed in its course's own entry, and docs/shortfalls.md logs them.
from datetime import time
from itertools import combinations
from uuid import UUID, uuid5

from sage.shared.rules import TERM_BY_SUFFIX, RuleSet, TimetableSlot

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
    # A year's rules with the meetings its course entries print. One already there stays as it is,
    # so adding them twice changes nothing.
    held = {slot.id for slot in rules.timetable_slots}
    added = [
        slot
        for version in rules.handbook_versions
        for slot in MEETINGS.get(version.year, ())
        if slot.id not in held
    ]
    return rules.model_copy(
        update={"timetable_slots": (*rules.timetable_slots, *added)}
    )
