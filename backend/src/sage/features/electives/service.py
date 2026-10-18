# Explore Electives: the current year's courses that have a tab, with whether she may take each and
# whether she hearted it, and hearting itself
from collections import defaultdict
from typing import get_args
from uuid import UUID

from sage.shared.base import Row
from sage.shared.errors import CourseNotFound
from sage.shared.planning import Eligibility, EligibilityChecker
from sage.shared.repositories import StudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import Course, ElectiveTab


class Elective(Row):
    course: Course
    eligibility: Eligibility
    favourite: bool


def by_tab(
    students: StudentRepository,
    rulebook: Rulebook,
    checker: EligibilityChecker,
    student_id: UUID,
) -> list[tuple[ElectiveTab, list[Elective]]]:
    # The tabs in ElectiveTab's order, leaving out empty ones
    rules = rulebook.current()
    tabs: dict[str, set[str]] = defaultdict(set)
    for member in rules.course_group_members:
        if member.category:
            tabs[member.category].add(member.course_code)
    courses = {course.code: course for course in rules.courses}
    listed = sorted({code for codes in tabs.values() for code in codes})
    record = students.record(student_id)
    eligibility = checker.check(
        [courses[code] for code in listed],
        record.course_history,
        rules,
        rulebook.symbols(),
    )
    return [
        (
            tab,
            [
                Elective(
                    course=courses[code],
                    eligibility=eligibility[code],
                    favourite=code in record.favourites,
                )
                for code in sorted(tabs[tab])
            ],
        )
        for tab in get_args(ElectiveTab)
        if tabs[tab]
    ]


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
