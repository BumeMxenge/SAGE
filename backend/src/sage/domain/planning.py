# The interfaces the planning engine will implement. Until it exists, stand-ins in services/stubs.py
# fill them, so swapping the engine in never touches a route.
from collections.abc import Mapping, Sequence
from typing import Literal, Protocol

from sage.domain.base import Row
from sage.domain.rules import Course, ResultSymbol, RuleSet
from sage.domain.students import CourseHistoryLine, PlanSetRows, Student


class Eligibility(Row):
    status: Literal["eligible", "check", "not_eligible"]
    reason: str | None = None  # what to tell her, when there's something to tell


class PlanGenerator(Protocol):
    # Every valid plan for the student in the rulebook's year, with the reasons behind them. The set
    # comes back unwritten and not yet complete.
    def generate(
        self, student: Student, history: Sequence[CourseHistoryLine], rules: RuleSet
    ) -> PlanSetRows: ...


class EligibilityChecker(Protocol):
    # Whether she may take each course, from her record and the year's rules, by course code
    def check(
        self,
        courses: Sequence[Course],
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
    ) -> dict[str, Eligibility]: ...
