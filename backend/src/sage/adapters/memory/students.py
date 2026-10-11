# Each student's data in one dictionary, keyed by her account id. Reads come back in the order the
# Supabase adapter returns them, so the two can be checked against each other.
from collections.abc import Callable, Collection, Iterable, Sequence
from typing import Any
from uuid import UUID

from sage.domain.base import Row
from sage.domain.students import (
    CourseHistoryLine,
    Favourite,
    PlanSetRows,
    Student,
    StudentRecord,
    StudentState,
)


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

    def save_profile(self, student: Student) -> None:
        state = self._students.get(student.id)
        self._students[student.id] = (
            state.model_copy(update={"student": student})
            if state
            else StudentState(student=student)
        )

    def replace_history(
        self, student_id: UUID, lines: Sequence[CourseHistoryLine]
    ) -> None:
        self._change(student_id, course_history=tuple(lines))

    def current_plan_set(self, student_id: UUID) -> PlanSetRows | None:
        state = self._students.get(student_id)
        if state is None:
            return None
        complete = [row for row in state.plan_sets if row.complete]
        if not complete:
            return None
        latest = max(complete, key=lambda row: (row.period, row.version))
        plans = sorted(
            (plan for plan in state.plans if plan.plan_set_id == latest.id),
            key=lambda plan: plan.position,
        )
        place = {plan.id: plan.position for plan in plans}
        courses = [row for row in state.plan_courses if row.plan_id in place]
        reasons = [row for row in state.plan_reasons if row.plan_set_id == latest.id]
        return PlanSetRows(
            plan_set=latest,
            plans=tuple(plans),
            plan_courses=tuple(
                sorted(courses, key=lambda row: (place[row.plan_id], row.course_code))
            ),
            plan_reasons=tuple(sorted(reasons, key=lambda row: row.id)),
        )

    def plans(
        self, student_id: UUID, plan_ids: Sequence[UUID]
    ) -> tuple[PlanSetRows, ...]:
        state = self._students.get(student_id)
        if state is None:
            return ()
        found = []
        for plan in state.plans:
            if plan.id not in plan_ids:
                continue
            reasons = [
                row for row in state.plan_reasons if row.plan_set_id == plan.plan_set_id
            ]
            courses = [row for row in state.plan_courses if row.plan_id == plan.id]
            found.append(
                PlanSetRows(
                    plan_set=next(
                        row for row in state.plan_sets if row.id == plan.plan_set_id
                    ),
                    plans=(plan,),
                    plan_courses=tuple(
                        sorted(courses, key=lambda row: row.course_code)
                    ),
                    plan_reasons=(
                        *sorted(
                            (row for row in reasons if row.plan_id is None),
                            key=lambda row: row.id,
                        ),
                        *sorted(
                            (row for row in reasons if row.plan_id == plan.id),
                            key=lambda row: row.id,
                        ),
                    ),
                )
            )
        return tuple(found)

    def add_plan_set(self, rows: PlanSetRows) -> None:
        student_id, set_id = rows.plan_set.student_id, rows.plan_set.id
        state = self._students[student_id]
        plan_sets = _added(state.plan_sets, [rows.plan_set], lambda row: row.id)
        self._change(
            student_id,
            # Complete whether the set is new or a retry found it already stored
            plan_sets=tuple(
                row.model_copy(update={"complete": True}) if row.id == set_id else row
                for row in plan_sets
            ),
            plans=_added(state.plans, rows.plans, lambda row: row.id),
            plan_courses=_added(
                state.plan_courses,
                rows.plan_courses,
                lambda row: (row.plan_id, row.course_code),
            ),
            plan_reasons=_added(
                state.plan_reasons, rows.plan_reasons, lambda row: row.id
            ),
        )

    def hide_plans(
        self, student_id: UUID, plan_set_id: UUID, keep: Collection[UUID]
    ) -> None:
        state = self._students[student_id]
        self._change(
            student_id,
            plans=tuple(
                plan.model_copy(update={"hidden": True})
                if plan.plan_set_id == plan_set_id and plan.id not in keep
                else plan
                for plan in state.plans
            ),
        )

    def save_answers(
        self, student_id: UUID, plan_set_id: UUID, answers: dict[str, Any]
    ) -> None:
        state = self._students[student_id]
        self._change(
            student_id,
            plan_sets=tuple(
                row.model_copy(update={"answers": answers})
                if row.id == plan_set_id
                else row
                for row in state.plan_sets
            ),
        )

    def record(self, student_id: UUID) -> StudentRecord:
        state = self._students.get(student_id)
        if state is None:
            return StudentRecord()
        return StudentRecord(
            course_history=tuple(
                sorted(
                    state.course_history,
                    key=lambda line: (line.academic_year, line.term, line.course_code),
                )
            ),
            favourites=tuple(sorted(row.course_code for row in state.favourites)),
        )

    def add_favourite(self, student_id: UUID, course_code: str) -> None:
        state = self._students[student_id]
        favourite = Favourite(student_id=student_id, course_code=course_code)
        self._change(
            student_id,
            favourites=_added(
                state.favourites, [favourite], lambda row: row.course_code
            ),
        )

    def remove_favourite(self, student_id: UUID, course_code: str) -> None:
        state = self._students[student_id]
        self._change(
            student_id,
            favourites=tuple(
                row for row in state.favourites if row.course_code != course_code
            ),
        )

    def _change(self, student_id: UUID, **tables: tuple[Row, ...]) -> None:
        self._students[student_id] = self._students[student_id].model_copy(
            update=tables
        )


def _added[T: Row](
    stored: tuple[T, ...], new: Iterable[T], key: Callable[[T], Any]
) -> tuple[T, ...]:
    # The stored rows plus each new row whose key isn't stored yet, as an insert that skips
    # existing rows would leave them
    have = {key(row) for row in stored}
    return stored + tuple(row for row in new if key(row) not in have)
