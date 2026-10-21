# The interfaces the planning engine implements, so the routes never depend on it directly
from collections.abc import Mapping, Sequence
from typing import Literal, Protocol

from sage.shared.base import Row
from sage.shared.rules import Course, ResultSymbol, RuleSet
from sage.shared.students import CourseHistoryLine, PlanSetRows, Student

# Whether she may take a course, or needs to check with her advisor first
EligibilityStatus = Literal["eligible", "check", "not_eligible"]


class Eligibility(Row):
    status: EligibilityStatus
    reason: str | None = None  # what to tell her, when there's something to tell


class PlanGenerator(Protocol):
    # Every valid plan for the student in the rulebook's year, with the reasons behind them. The set
    # comes back unwritten and not yet complete.
    def generate(
        self,
        student: Student,
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
    ) -> PlanSetRows: ...


class EligibilityChecker(Protocol):
    # Whether she may take each course, from her record and the year's rules, by course code
    def check(
        self,
        courses: Sequence[Course],
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
        student: Student,
    ) -> dict[str, Eligibility]: ...
