# Checks when a plan set needs the questionnaire's narrowing, on rows built here
from uuid import UUID, uuid4

import pytest

from sage.features.plans import service as plans
from sage.shared.students import Plan, PlanSet, PlanSetRows

STUDENT = UUID(int=1)


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
