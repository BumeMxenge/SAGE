# The interfaces adapters implement: one home for the rulebook, one for students' data. Services
# depend on these and never on Supabase, so unit tests can use the in-memory versions instead.
# Every student method reads or writes only the rows of the student it names.
from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sage.domain.rules import ResultSymbol, RuleSet
from sage.domain.students import CourseHistoryLine, PlanSetRows, Student, StudentState


class AccountNotFound(Exception):
    # No sign-in account has this student's id, so her rows have nothing to belong to
    pass


class RuleRepository(Protocol):
    # Stores every row that isn't there yet and leaves rows already stored as they are
    def add_missing(self, rules: RuleSet) -> None: ...

    # Every stored row of one handbook year
    def get(self, year: int) -> RuleSet: ...

    # The latest approved handbook year, or None before any is approved
    def current_year(self) -> int | None: ...

    # UCT's result symbols, which belong to no year
    def symbols(self) -> tuple[ResultSymbol, ...]: ...


class StudentRepository(Protocol):
    # Makes the stored student exactly this state, removing whatever she had before
    def replace(self, state: StudentState) -> None: ...

    # The stored student, or None if there isn't one
    def get(self, student_id: UUID) -> StudentState | None: ...

    # Her profile row alone, or None before onboarding writes one
    def profile(self, student_id: UUID) -> Student | None: ...

    # Writes her profile row, creating it the first time
    def save_profile(self, student: Student) -> None: ...

    # Makes her course history exactly these lines. Her profile must exist.
    def replace_history(
        self, student_id: UUID, lines: Sequence[CourseHistoryLine]
    ) -> None: ...

    # Her latest complete plan set (highest period, then version) with every plan, course and
    # reason, or None
    def current_plan_set(self, student_id: UUID) -> PlanSetRows | None: ...

    # Each of these plans that is hers, from any set, as its set holding just that plan, with its
    # courses, then the set's reasons and the plan's own. Another student's plan isn't returned.
    def plans(
        self, student_id: UUID, plan_ids: Sequence[UUID]
    ) -> tuple[PlanSetRows, ...]: ...

    # Writes a generated set, skipping rows already stored, and marks it complete last, so a retry
    # after a failure finishes the same set
    def add_plan_set(self, rows: PlanSetRows) -> None: ...
