# Each student's data in one dictionary, keyed by her account id
from uuid import UUID

from sage.domain.students import Student, StudentState


class InMemoryStudentRepository:
    def __init__(self) -> None:
        self._students: dict[UUID, StudentState] = {}

    def replace(self, state: StudentState) -> None:
        self._students[state.student.id] = state

    def get(self, student_id: UUID) -> StudentState | None:
        return self._students.get(student_id)

    def profile(self, student_id: UUID) -> Student | None:
        state = self._students.get(student_id)
        return state.student if state else None
