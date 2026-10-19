# The engine's stand-ins, which the API runs on until the engine exists. Each fills an interface in
# shared/planning.py, so swapping the engine in never touches a route.
from collections.abc import Mapping, Sequence
from pathlib import Path
from uuid import UUID

from sage.shared.planning import Eligibility
from sage.shared.rules import Course, Refer, ResultSymbol, RuleSet
from sage.shared.seed import load_seed
from sage.shared.students import CourseHistoryLine, PlanSetRows, Student

UNCHECKED = "SAGE can't check this requirement yet. Ask your advisor."


class SeededPlanGenerator:
    # Gives every student Mbali's seeded plan set: her 10 plans with their courses and reasons,
    # unanswered and with nothing hidden. The engine replaces this. It needs the approved 2026
    # stored already, and makes the same ids as sage seed, so a retried onboarding finishes the
    # same set.
    def __init__(self, seed_file: Path) -> None:
        # Read at startup too, so a missing or broken file stops the app, not an onboarding
        load_seed(seed_file, UUID(int=0))
        self._seed_file = seed_file

    def generate(
        self, student: Student, history: Sequence[CourseHistoryLine], rules: RuleSet
    ) -> PlanSetRows:
        seeded = load_seed(self._seed_file, student.id)
        (plan_set,) = seeded.plan_sets
        return PlanSetRows(
            plan_set=plan_set.model_copy(update={"answers": None, "complete": False}),
            plans=tuple(
                plan.model_copy(update={"hidden": False}) for plan in seeded.plans
            ),
            plan_courses=seeded.plan_courses,
            plan_reasons=seeded.plan_reasons,
        )


class InterimEligibility:
    # Interim rules until the engine checks entry requirements, in this order: a course she has
    # passed, or passed under a code that counts as it, isn't for her; a course with no entry rule
    # is; a rule that refers her elsewhere shows its printed text; and any other rule needs checking
    # with her advisor. The engine replaces this.
    def check(
        self,
        courses: Sequence[Course],
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
    ) -> dict[str, Eligibility]:
        passed = {
            line.course_code
            for line in history
            if symbols[line.result].outcome in ("pass", "credited")
        }
        # Each code a pass also covers, and the code she passed for it
        covered = {code: code for code in passed}
        for rule in rules.equivalences:
            if rule.course_code in passed:
                covered.setdefault(rule.counts_as, rule.course_code)
        return {course.code: self._one(course, covered) for course in courses}

    def _one(self, course: Course, covered: dict[str, str]) -> Eligibility:
        if course.code in covered:
            return Eligibility(
                status="not_eligible",
                reason=f"You've already passed {covered[course.code]}.",
            )
        if course.entry_rule is None:
            return Eligibility(status="eligible")
        if isinstance(course.entry_rule, Refer):
            return Eligibility(status="check", reason=course.entry_rule.refer)
        return Eligibility(status="check", reason=UNCHECKED)
