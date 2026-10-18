# Her plans: the current set, one plan in full, and two side by side. Students never edit a plan;
# the questionnaire only hides some, and any of them still opens here.
from uuid import UUID

from fastapi import APIRouter

from sage.services import plans
from sage.shared.api.deps import ONBOARDED_ERRORS, Onboarded, Rules, Students
from sage.shared.api.models import (
    Comparison,
    Credits,
    Group,
    Meeting,
    Plan,
    PlanCourse,
    PlanSet,
    PlanSummary,
    Reason,
)
from sage.shared.api.problems import errors
from sage.shared.errors import (
    InvalidRequest,
    PlanNotFound,
    PlansNotReady,
    RulebookNotLoaded,
    SamePlan,
)
from sage.shared.rules import RuleSet
from sage.shared.students import PlanReason, PlanSetRows

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get(
    "",
    summary="Her current plan set, with hidden plans flagged",
    responses=errors(*ONBOARDED_ERRORS, PlansNotReady, RulebookNotLoaded),
)
def get_plans(student: Onboarded, students: Students, rulebook: Rules) -> PlanSet:
    rows = plans.current_set(students, student.id)
    return plan_set(rows, rulebook.year(rows.plan_set.period))


# Declared before /{plan_id}, so "compare" is never read as a plan id
@router.get(
    "/compare",
    summary="Two of her plans side by side",
    responses=errors(
        *ONBOARDED_ERRORS, InvalidRequest, PlanNotFound, SamePlan, RulebookNotLoaded
    ),
)
def compare_plans(
    first: UUID, second: UUID, student: Onboarded, students: Students, rulebook: Rules
) -> Comparison:
    one, two = plans.two_plans(students, student.id, first, second)
    a = plan(one, rulebook.year(one.plan_set.period), student.curriculum_code)
    b = plan(two, rulebook.year(two.plan_set.period), student.curriculum_code)
    codes_a = {course.code for course in a.courses}
    codes_b = {course.code for course in b.courses}
    return Comparison(
        first=a,
        second=b,
        shared=sorted(codes_a & codes_b),
        only_first=sorted(codes_a - codes_b),
        only_second=sorted(codes_b - codes_a),
    )


@router.get(
    "/{plan_id}",
    summary="One of her plans in full, from any set, hidden or not",
    responses=errors(
        *ONBOARDED_ERRORS, InvalidRequest, PlanNotFound, RulebookNotLoaded
    ),
)
def get_plan(
    plan_id: UUID, student: Onboarded, students: Students, rulebook: Rules
) -> Plan:
    rows = plans.one_plan(students, student.id, plan_id)
    return plan(rows, rulebook.year(rows.plan_set.period), student.curriculum_code)


def plan_set(rows: PlanSetRows, rules: RuleSet) -> PlanSet:
    courses = plans.courses(rows, rules)
    return PlanSet(
        period=rows.plan_set.period,
        version=rows.plan_set.version,
        questionnaire_needed=plans.questionnaire_needed(rows),
        reasons=[
            reason(row, rules) for row in rows.plan_reasons if row.plan_id is None
        ],
        plans=[
            PlanSummary(
                id=row.id,
                position=row.position,
                name=row.name,
                hidden=row.hidden,
                credits=sum(course.credits for course in courses[row.id]),
            )
            for row in rows.plans
        ],
    )


def plan(rows: PlanSetRows, rules: RuleSet, curriculum: str) -> Plan:
    (row,) = rows.plans
    courses = plans.courses(rows, rules)[row.id]
    keys = plans.group_keys(rules, curriculum)
    labels = {group.group_key: group.label for group in rules.course_groups}
    by_code = {course.course_code: course for course in rows.plan_courses}
    return Plan(
        id=row.id,
        period=rows.plan_set.period,
        position=row.position,
        name=row.name,
        hidden=row.hidden,
        credits=Credits(
            total=sum(course.credits for course in courses),
            by_term=plans.credits_by_term(courses),
        ),
        courses=[
            PlanCourse(
                code=course.code,
                name=course.name,
                credits=course.credits,
                term=course.term,
                groups=[
                    Group(key=member.group_key, label=labels[member.group_key])
                    for member in rules.course_group_members
                    if member.course_code == course.code and member.group_key in keys
                ],
                meetings=[
                    Meeting.model_validate(slot, from_attributes=True)
                    for slot in plans.meetings(by_code[course.code], rules, curriculum)
                ],
            )
            for course in courses
        ],
        reasons=[reason(reason_row, rules) for reason_row in rows.plan_reasons],
    )


def reason(row: PlanReason, rules: RuleSet) -> Reason:
    passage = next((p for p in rules.passages if p.id == row.passage_id), None)
    return Reason(
        kind=row.kind,
        message=row.message,
        course_code=row.course_code,
        source=passage.source if passage else None,
        section=passage.section if passage else None,
        page=passage.page if passage else None,
    )
