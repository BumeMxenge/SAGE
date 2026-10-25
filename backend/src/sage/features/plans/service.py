# Her plans as the planner shows them: the current set, one plan in full, and two side by side.
# Course names, credits, groups and meetings come from the rulebook of the plan's year.
from collections import defaultdict
from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sage.shared.errors import CourseDoesntFit, PlanNotFound, PlansNotReady, SamePlan
from sage.shared.repositories import StudentRepository
from sage.shared.rules import Course, RuleSet, TermCode
from sage.shared.slots import PlanSlot, plan_slots
from sage.shared.students import PlanCourse, PlanSetRows


def current_set(students: StudentRepository, student_id: UUID) -> PlanSetRows:
    rows = students.current_plan_set(student_id)
    if rows is None:
        raise PlansNotReady()
    return rows


def questionnaire_needed(rows: PlanSetRows) -> bool:
    # Only a long list needs narrowing, and only before she has answered
    return (
        rows.plan_set.complete and len(rows.plans) > 5 and rows.plan_set.answers is None
    )


def one_plan(
    students: StudentRepository, student_id: UUID, plan_id: UUID
) -> PlanSetRows:
    # Another student's plan is not found, rather than forbidden, so ids aren't confirmed to exist
    found = students.plans(student_id, [plan_id])
    if not found:
        raise PlanNotFound()
    return found[0]


def two_plans(
    students: StudentRepository, student_id: UUID, first: UUID, second: UUID
) -> tuple[PlanSetRows, PlanSetRows]:
    if first == second:
        raise SamePlan()
    found = {
        rows.plans[0].id: rows for rows in students.plans(student_id, [first, second])
    }
    if first not in found or second not in found:
        raise PlanNotFound()
    return found[first], found[second]


def preview(
    rows: PlanSetRows, code: str
) -> tuple[PlanSetRows, list[tuple[str, str, str]]]:
    # One plan's rows as they'd be with this course taken in the first slot that lists it, nothing
    # saved: the course on only the sections that fit, each section it forces fixed in the plan's own
    # course, and the slot it fills gone, so its credits aren't counted twice. The sections forced,
    # as (course, choice group, choice), come back too.
    filled = next(
        (
            reason
            for reason in rows.plan_reasons
            if reason.details and code in reason.details["fits"]
        ),
        None,
    )
    if filled is None:
        raise CourseDoesntFit()
    (slot,) = plan_slots([filled])
    forced = {
        (course, group): choice
        for course, groups in slot.forced.get(code, {}).items()
        for group, choice in groups.items()
    }
    (plan,) = rows.plans
    added = PlanCourse(
        plan_id=plan.id,
        course_code=code,
        student_id=plan.student_id,
        handbook_year=rows.plan_set.period,
        choices=slot.sections.get(code) or None,
    )
    held = tuple(
        row.model_copy(
            update={
                "choices": {
                    **(row.choices or {}),
                    **{
                        group: [choice]
                        for (course, group), choice in forced.items()
                        if course == row.course_code
                    },
                }
                or None
            }
        )
        for row in rows.plan_courses
    )
    taken = rows.model_copy(
        update={
            "plan_courses": (*held, added),
            "plan_reasons": tuple(
                reason for reason in rows.plan_reasons if reason is not filled
            ),
        }
    )
    return taken, [
        (course, group, choice) for (course, group), choice in forced.items()
    ]


def courses(rows: PlanSetRows, rules: RuleSet) -> dict[UUID, list[Course]]:
    # Each plan's courses from its year's rulebook, by code
    by_code = {course.code: course for course in rules.courses}
    found: dict[UUID, list[Course]] = defaultdict(list)
    for row in sorted(rows.plan_courses, key=lambda row: row.course_code):
        found[row.plan_id].append(by_code[row.course_code])
    return found


def credits_by_term(courses: Iterable[Course]) -> dict[TermCode, int]:
    totals: dict[TermCode, int] = defaultdict(int)
    for course in courses:
        totals[course.term] += course.credits
    return dict(totals)


def to_choose(slots: Iterable[PlanSlot], plan_id: UUID) -> int:
    # The credits a plan leaves her to choose, which its credit line shows beside its courses'
    return sum(slot.credits for slot in slots if slot.plan_id == plan_id)


def group_keys(rules: RuleSet, curriculum: str) -> set[str]:
    # The course groups her curriculum's rules name, found by walking each rule tree's JSON for
    # strings that are group keys, so no rule shape needs knowing here
    keys = {group.group_key for group in rules.course_groups}
    named: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, str) and node in keys:
            named.add(node)
        elif isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    for rule in rules.curriculum_rules:
        if rule.curriculum_code == curriculum:
            walk(rule.rule.model_dump(mode="json"))
    return named
