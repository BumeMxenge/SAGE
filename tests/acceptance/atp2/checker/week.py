# The week as SEMANTICS.md reads it (Clashes): which meetings of a course she attends on her
# curriculum, when two meetings clash, and whether one section of every choice group, for every
# course at once, leaves no clash
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import time
from functools import cache
from uuid import UUID

from sage.shared.rules import RuleSet

# The quarters inside each semester. full_year overlaps both semesters and every quarter, and
# winter and summer overlap only themselves.
INSIDE = {"q1": "sem1", "q2": "sem1", "q3": "sem2", "q4": "sem2"}


@dataclass(frozen=True)
class Meeting:
    term: str
    day: int | None
    start: time | None
    end: time | None

    @property
    def timed(self) -> bool:
        return None not in (self.day, self.start, self.end)


@dataclass(frozen=True)
class Week:
    # One course's meetings on her curriculum: those she must attend, and each choice group's
    # alternatives, of which she attends one. A course with no meetings has an empty week.
    fixed: tuple[Meeting, ...] = ()
    choices: tuple[tuple[tuple[Meeting, ...], ...], ...] = ()

    @property
    def untimed(self) -> bool:
        # A meeting with no printed day or time can't clash, but makes its course conditional
        alternatives = (m for options in self.choices for o in options for m in o)
        return not all(m.timed for m in (*self.fixed, *alternatives))


def overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    if {a, b} & {"winter", "summer", "other"}:
        return False
    if "full_year" in (a, b):
        return True
    # A quarter overlaps its own semester, while two quarters or two semesters don't overlap
    return INSIDE.get(a, a) == INSIDE.get(b, b) and not (a in INSIDE and b in INSIDE)


def clash(a: Meeting, b: Meeting) -> bool:
    # They share a day, they overlap in time and their terms overlap. Meetings that only touch
    # don't clash, and one with no printed day or time can't.
    return (
        a.timed
        and b.timed
        and a.day == b.day
        and a.start < b.end
        and b.start < a.end
        and overlap(a.term, b.term)
    )


def weeks(rules: RuleSet, curriculum: str) -> dict[str, Week]:
    # Every course's week on her curriculum. A meeting linked to curricula belongs to those alone.
    only: dict[UUID, set[str]] = defaultdict(set)
    for link in rules.timetable_slot_curricula:
        only[link.slot_id].add(link.curriculum_code)
    fixed: dict[str, list[Meeting]] = defaultdict(list)
    grouped: dict[str, dict[str, dict[str, list[Meeting]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for slot in rules.timetable_slots:
        if slot.id in only and curriculum not in only[slot.id]:
            continue
        meeting = Meeting(slot.term, slot.day, slot.start_time, slot.end_time)
        if slot.choice_group is None:
            fixed[slot.course_code].append(meeting)
        else:
            grouped[slot.course_code][slot.choice_group][slot.choice].append(meeting)
    return {
        code: Week(
            fixed=tuple(fixed[code]),
            choices=tuple(
                tuple(tuple(options[choice]) for choice in sorted(options))
                for _, options in sorted(grouped[code].items())
            ),
        )
        for code in {*fixed, *grouped}
    }


def schedulable(weeks: Sequence[Week]) -> bool:
    # Whether one alternative of every choice group, for every course at once, leaves no two
    # courses' meetings clashing. Testing courses two at a time isn't enough (Alternatives).
    units = sorted(
        (
            (course, options)
            for course, week in enumerate(weeks)
            for options in ((week.fixed,), *week.choices)
        ),
        key=lambda unit: len(unit[1]),
    )
    chosen: list[tuple[int, tuple[Meeting, ...]]] = []

    def place(k: int) -> bool:
        if k == len(units):
            return True
        course, options = units[k]
        for option in options:
            if all(
                other == course or apart(option, theirs) for other, theirs in chosen
            ):
                chosen.append((course, option))
                if place(k + 1):
                    return True
                chosen.pop()
        return False

    return place(0)


@cache
def apart(a: tuple[Meeting, ...], b: tuple[Meeting, ...]) -> bool:
    return not any(clash(x, y) for x in a for y in b)
