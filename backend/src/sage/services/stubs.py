# The stand-ins the API runs on until the real components exist. Each fills an interface in domain/,
# so swapping the real one in never touches a route.
from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from sage.domain.rules import RuleSet
from sage.domain.students import CourseHistoryLine, PlanSetRows, Student
from sage.services.seed import load_seed


class SeededPlanGenerator:
    # Gives every student Mbali's seeded plan set: her 10 plans with their courses and reasons,
    # unanswered and with nothing hidden. The engine replaces this. It needs the seed's 2026
    # rulebook stored already, and makes the same ids as sage seed, so a retried onboarding
    # finishes the same set.
    def __init__(self, seed_file: Path) -> None:
        # Read once at startup, so a missing or broken file stops the app, not an onboarding
        load_seed(seed_file, UUID(int=0))
        self._seed_file = seed_file

    def generate(
        self, student: Student, history: Sequence[CourseHistoryLine], rules: RuleSet
    ) -> PlanSetRows:
        seeded = load_seed(self._seed_file, student.id).student
        (plan_set,) = seeded.plan_sets
        return PlanSetRows(
            plan_set=plan_set.model_copy(update={"answers": None, "complete": False}),
            plans=tuple(
                plan.model_copy(update={"hidden": False}) for plan in seeded.plans
            ),
            plan_courses=seeded.plan_courses,
            plan_reasons=seeded.plan_reasons,
        )
