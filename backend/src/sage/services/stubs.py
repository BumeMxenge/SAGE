# The stand-ins the API runs on until the real components exist. Each fills an interface in shared/,
# so swapping the real one in never touches a route.
from collections.abc import Mapping, Sequence
from pathlib import Path
from uuid import UUID

from sage.shared.advisor import Reply
from sage.shared.planning import Eligibility
from sage.shared.rules import Course, Refer, ResultSymbol, RuleSet
from sage.shared.seed import load_seed
from sage.shared.students import Chat, CourseHistoryLine, PlanSetRows, Student

UNCHECKED = "SAGE can't check this requirement yet. Ask your advisor."
FIXED_REPLY = (
    "I can't answer questions yet. Your faculty advisor can help with this one."
)


class SeededPlanGenerator:
    # Gives every student Mbali's seeded plan set: her 10 plans with their courses and reasons,
    # unanswered and with nothing hidden. The engine replaces this. It needs the approved 2026
    # stored already, and makes the same ids as sage seed, so a retried onboarding finishes the
    # same set.
    def __init__(self, seed_file: Path) -> None:
        # Read once at startup, so a missing or broken file stops the app, not an onboarding
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


class FixedAdvisor:
    # One fixed reply in the final format, handing every question to a human advisor. In a pair
    # chat its Open plan action points at the second plan. The real advisor replaces this.
    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        return Reply(
            content=FIXED_REPLY, referral=True, open_plan_id=chat.other_plan_id
        )
