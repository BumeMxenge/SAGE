# The interfaces adapters implement: one home for the rulebook, one for students' data. Services
# depend on these and never on Supabase, so unit tests can use the in-memory versions instead.
from typing import Protocol
from uuid import UUID

from sage.domain.rules import RuleSet
from sage.domain.students import StudentState


class AccountNotFound(Exception):
    # No sign-in account has this student's id, so her rows have nothing to belong to
    pass


class RuleRepository(Protocol):
    # Stores every row that isn't there yet and leaves rows already stored as they are
    def add_missing(self, rules: RuleSet) -> None: ...

    # Every stored row of one handbook year
    def get(self, year: int) -> RuleSet: ...


class StudentRepository(Protocol):
    # Makes the stored student exactly this state, removing whatever she had before
    def replace(self, state: StudentState) -> None: ...

    # The stored student, or None if there isn't one
    def get(self, student_id: UUID) -> StudentState | None: ...
