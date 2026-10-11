# The interfaces the planning engine will implement. Until it exists, stand-ins in services/stubs.py
# fill them, so swapping the engine in never touches a route.
from collections.abc import Sequence
from typing import Protocol

from sage.domain.rules import RuleSet
from sage.domain.students import CourseHistoryLine, PlanSetRows, Student


class PlanGenerator(Protocol):
    # Every valid plan for the student in the rulebook's year, with the reasons behind them. The set
    # comes back unwritten and not yet complete.
    def generate(
        self, student: Student, history: Sequence[CourseHistoryLine], rules: RuleSet
    ) -> PlanSetRows: ...
