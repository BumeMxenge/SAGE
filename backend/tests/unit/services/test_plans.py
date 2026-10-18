# Checks the plan rules the planner and questionnaire lean on, on rows built here: when a set needs
# narrowing, and which of a course's meetings a plan shows
from uuid import UUID, uuid4

import pytest

from sage.services import plans
from sage.shared.rules import RuleSet, TimetableSlot, TimetableSlotCurriculum
from sage.shared.students import Plan, PlanCourse, PlanSet, PlanSetRows

STUDENT = UUID(int=1)
HERS, THEIRS = "EB011EEE05", "EB999XYZ99"  # her curriculum, and a made-up second one


def plan_set(size: int) -> PlanSetRows:
    # A complete set of this many plans, not yet narrowed
    plan_set = PlanSet(
        id=uuid4(), student_id=STUDENT, period=2026, version=1, complete=True
    )
    return PlanSetRows(
        plan_set=plan_set,
        plans=tuple(
            Plan(
                id=uuid4(),
                plan_set_id=plan_set.id,
                student_id=STUDENT,
                position=position,
                name=f"Plan {position}",
            )
            for position in range(1, size + 1)
        ),
    )


# My report's Section 4.1.1: "A questionnaire filters this set when more than five plans exist;
# otherwise the planner opens directly."
@pytest.mark.parametrize(("size", "needed"), [(5, False), (6, True)])
def test_more_than_five_plans_need_the_questionnaire(size, needed):
    assert plans.questionnaire_needed(plan_set(size)) is needed


def meeting(day: int, **fields) -> TimetableSlot:
    # One meeting of a made-up course
    return TimetableSlot(
        id=uuid4(),
        handbook_year=2026,
        course_code="TST4000F",
        term="sem1",
        day=day,
        **fields,
    )


def course(choices: dict[str, str] | None = None) -> PlanCourse:
    # The made-up course in a plan, with the alternatives chosen so far
    return PlanCourse(
        plan_id=uuid4(),
        course_code="TST4000F",
        student_id=STUDENT,
        handbook_year=2026,
        choices=choices,
    )


def test_a_meeting_linked_to_curricula_shows_only_in_theirs():
    everyone, hers, theirs = meeting(1), meeting(2), meeting(3)
    rules = RuleSet(
        timetable_slots=(everyone, hers, theirs),
        timetable_slot_curricula=tuple(
            TimetableSlotCurriculum(
                slot_id=slot.id, handbook_year=2026, curriculum_code=curriculum
            )
            for slot, curriculum in ((hers, HERS), (theirs, THEIRS))
        ),
    )
    assert plans.meetings(course(), rules, HERS) == [everyone, hers]


def test_every_alternative_shows_until_one_is_chosen():
    lecture = meeting(1)
    tutorial_a = meeting(2, choice_group="tutorial", choice="A")
    tutorial_b = meeting(3, choice_group="tutorial", choice="B")
    rules = RuleSet(timetable_slots=(lecture, tutorial_a, tutorial_b))
    assert plans.meetings(course(), rules, HERS) == [lecture, tutorial_a, tutorial_b]
    chosen = course({"tutorial": "B"})
    assert plans.meetings(chosen, rules, HERS) == [lecture, tutorial_b]
