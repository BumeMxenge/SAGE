# Explore Electives: the current year's courses that have a tab, one card per course, with whether
# each offering works for her and whether she hearted it, and hearting itself. An offering works when
# the engine doesn't refuse it and a complementary slot in her current plan set, shown or hidden,
# lists it among the courses that fit, or, where no plan has such a slot, when the engine doesn't
# refuse it. She can heart only what works, and each card carries at most one note saying why not,
# or what to check.
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from typing import Any, get_args
from uuid import UUID

from sage.shared.base import Row
from sage.shared.errors import CourseNotFound
from sage.shared.planning import Eligibility, EligibilityChecker
from sage.shared.repositories import StudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import Course, ElectiveTab, RuleSet, TermCode, offerings
from sage.shared.students import Student

# How a note names an offering's term
TERMS: dict[TermCode, str] = {
    "q1": "quarter 1",
    "q2": "quarter 2",
    "q3": "quarter 3",
    "q4": "quarter 4",
    "sem1": "semester 1",
    "sem2": "semester 2",
    "full_year": "full-year",
    "winter": "winter",
    "summer": "summer",
    "other": "other",
}
NO_FIT = "Doesn't fit your plans' timetables."
UNTIMED = "A meeting has no printed day or time, so check its times with your advisor."


class Offering(Row):
    course: Course
    eligibility: Eligibility
    hearted: bool
    works: bool  # so she can heart it
    # The complementary slots' details that list it among the courses that fit
    listed: tuple[dict[str, Any], ...]


class Card(Row):
    # One course's offerings, by code, whose first offering's name, summary and convener stand for
    # the course
    offerings: tuple[Offering, ...]
    note: str | None

    @property
    def hearted(self) -> bool:
        return any(offering.hearted for offering in self.offerings)

    @property
    def can_heart(self) -> bool:
        return any(offering.works for offering in self.offerings)


def by_tab(
    students: StudentRepository,
    rulebook: Rulebook,
    checker: EligibilityChecker,
    student: Student,
) -> list[tuple[ElectiveTab, list[Card]]]:
    rules = rulebook.current()
    record = students.record(student.id)
    tabbed = {
        member.course_code for member in rules.course_group_members if member.category
    }
    eligibility = checker.check(
        [course for course in rules.courses if course.code in tabbed],
        record.course_history,
        rules,
        rulebook.symbols(),
        student,
    )
    # Only a complementary slot's reason has details
    plan_set = students.current_plan_set(student.id)
    slots = [r.details for r in plan_set.plan_reasons if r.details] if plan_set else []
    return cards(rules, eligibility, record.favourites, slots)


def cards(
    rules: RuleSet,
    eligibility: Mapping[str, Eligibility],
    favourites: Collection[str],
    slots: Sequence[dict[str, Any]],
) -> list[tuple[ElectiveTab, list[Card]]]:
    # The tabs in ElectiveTab's order, leaving out empty ones. A course's card sits on its first
    # offering's tab.
    tab = {m.course_code: m.category for m in rules.course_group_members if m.category}
    courses = {course.code: course for course in rules.courses if course.code in tab}
    worth = {code: course.credits for code, course in courses.items()}
    by_course: dict[str, list[Course]] = defaultdict(list)
    for code in sorted(courses):
        by_course[min(offerings(code, worth[code], worth))].append(courses[code])
    tabs: dict[str, list[Card]] = defaultdict(list)
    for first, offered in by_course.items():
        found = [
            _offering(course, eligibility[course.code], favourites, slots)
            for course in offered
        ]
        tabs[tab[first]].append(Card(offerings=tuple(found), note=_note(found)))
    return [(key, tabs[key]) for key in get_args(ElectiveTab) if tabs[key]]


def _offering(
    course: Course,
    eligibility: Eligibility,
    favourites: Collection[str],
    slots: Sequence[dict[str, Any]],
) -> Offering:
    listed = tuple(slot for slot in slots if course.code in slot["fits"])
    return Offering(
        course=course,
        eligibility=eligibility,
        hearted=course.code in favourites,
        works=eligibility.status != "not_eligible" and (not slots or bool(listed)),
        listed=listed,
    )


def _note(found: Sequence[Offering]) -> str | None:
    # Why nothing works, else what a working offering needs checked, else why one doesn't work
    working = [offering for offering in found if offering.works]
    if not working:
        return _refusal(found[0]) or NO_FIT
    checks = [check for offering in working if (check := _check(offering))]
    if checks:
        return checks[0]
    if len(working) == len(found):
        return None
    refused = next(offering for offering in found if not offering.works)
    terms = " and ".join(TERMS[offering.course.term] for offering in working)
    fits = "offering fits" if len(working) == 1 else "offerings fit"
    return _refusal(refused) or f"Only the {terms} {fits} your plans."


def _refusal(offering: Offering) -> str | None:
    # The engine's reason she can't take it, if it refuses it
    eligibility = offering.eligibility
    return eligibility.reason if eligibility.status == "not_eligible" else None


def _check(offering: Offering) -> str | None:
    # What to check before taking an offering that works: what the engine leaves to her advisor, a
    # meeting with no printed time, or fewer credits than every slot listing it needs
    if offering.eligibility.status == "check":
        return offering.eligibility.reason
    listed = offering.listed
    code = offering.course.code
    if any(code in slot["untimed"] for slot in listed):
        return UNTIMED
    if listed and all(code in slot["fewer_credits"] for slot in listed):
        needed = min(slot["credits"] for slot in listed)
        return (
            f"It's worth fewer than your plans' {needed}-credit complementary line, so check "
            "it with your advisor."
        )
    return None


def heart(
    students: StudentRepository, rulebook: Rulebook, student_id: UUID, code: str
) -> None:
    require_current_course(rulebook, code)
    students.add_favourite(student_id, code)


def unheart(
    students: StudentRepository, rulebook: Rulebook, student_id: UUID, code: str
) -> None:
    require_current_course(rulebook, code)
    students.remove_favourite(student_id, code)


def require_current_course(rulebook: Rulebook, code: str) -> None:
    year = rulebook.current_year()
    if code not in {course.code for course in rulebook.year(year).courses}:
        raise CourseNotFound(f"{code} isn't a course in the {year} handbook.")
