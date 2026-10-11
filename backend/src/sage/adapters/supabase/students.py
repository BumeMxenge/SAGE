# Each student's data in Supabase. Replacing her deletes her profile row, which cascades to
# everything of hers, then writes the new state table by table in foreign-key order. Separate REST
# calls can't share a transaction, so a write that fails part-way is repaired by running it again.
# Reads for the API embed related rows, so each is one request.
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from postgrest import APIError, ReturnMethod
from supabase import Client

from sage.adapters.supabase.tables import columns, insert, row_type, select
from sage.domain.repositories import AccountNotFound
from sage.domain.students import (
    CourseHistoryLine,
    Plan,
    PlanCourse,
    PlanReason,
    PlanSet,
    PlanSetRows,
    Student,
    StudentState,
)

FOREIGN_KEY_VIOLATION = "23503"

# The columns each table is read in order of, in the foreign-key order StudentState lists them.
# Messages come back in the order they were written.
ORDER = {
    "course_history": ("academic_year", "term", "course_code"),
    "favourites": ("course_code",),
    "plan_sets": ("period", "version"),
    "plans": ("plan_set_id", "position"),
    "plan_courses": ("plan_id", "course_code"),
    "plan_reasons": ("id",),
    "chats": ("id",),
    "messages": ("chat_id", "created_at", "id"),
    "message_citations": ("message_id", "position"),
}

# A plan set with its plans, their courses and its reasons, embedded in one select
PLAN_SET_ROWS = (
    f"{columns(PlanSet)},plans({columns(Plan)},plan_courses({columns(PlanCourse)})),"
    f"plan_reasons({columns(PlanReason)})"
)


class SupabaseStudentRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def replace(self, state: StudentState) -> None:
        student_id = str(state.student.id)
        self._client.table("students").delete().eq("id", student_id).execute()
        try:
            insert(self._client, "students", [state.student])
        except APIError as error:
            # Her id must be a sign-in account's id (students.id references auth.users)
            if error.code == FOREIGN_KEY_VIOLATION:
                raise AccountNotFound(student_id) from error
            raise
        for table in ORDER:
            insert(self._client, table, getattr(state, table))

    def get(self, student_id: UUID) -> StudentState | None:
        profile = self.profile(student_id)
        if profile is None:
            return None
        return StudentState(
            student=profile,
            **{
                table: select(
                    self._client,
                    table,
                    row_type(StudentState, table),
                    "student_id",
                    str(student_id),
                    order,
                )
                for table, order in ORDER.items()
            },
        )

    def profile(self, student_id: UUID) -> Student | None:
        rows = select(self._client, "students", Student, "id", str(student_id), ("id",))
        return rows[0] if rows else None

    def save_profile(self, student: Student) -> None:
        row = student.model_dump(mode="json")
        students = self._client.table("students")
        students.upsert(row, returning=ReturnMethod.minimal).execute()

    def replace_history(
        self, student_id: UUID, lines: Sequence[CourseHistoryLine]
    ) -> None:
        # The Data API can't swap a set of rows in one request, so this deletes, then inserts.
        # Onboarding marks her done only after both, so a failure between them gets retried.
        (
            self._client.table("course_history")
            .delete()
            .eq("student_id", str(student_id))
            .execute()
        )
        insert(self._client, "course_history", lines)

    def current_plan_set(self, student_id: UUID) -> PlanSetRows | None:
        rows = (
            self._client.table("plan_sets")
            .select(PLAN_SET_ROWS)
            .eq("student_id", str(student_id))
            .eq("complete", True)
            .order("period", desc=True)
            .order("version", desc=True)
            .order("position", foreign_table="plans")
            .order("course_code", foreign_table="plans.plan_courses")
            .order("id", foreign_table="plan_reasons")
            .limit(1)
            .execute()
            .data
        )
        return plan_set_rows(rows[0]) if rows else None

    def add_plan_set(self, rows: PlanSetRows) -> None:
        unfinished = rows.plan_set.model_copy(update={"complete": False})
        for table, batch in (
            ("plan_sets", [unfinished]),
            ("plans", rows.plans),
            ("plan_courses", rows.plan_courses),
            ("plan_reasons", rows.plan_reasons),
        ):
            insert(self._client, table, batch, skip_existing=True)
        (
            self._client.table("plan_sets")
            .update({"complete": True})
            .eq("id", str(rows.plan_set.id))
            .eq("student_id", str(rows.plan_set.student_id))
            .execute()
        )


def plan_set_rows(row: dict[str, Any]) -> PlanSetRows:
    # One embedded plan_sets row as domain rows, keeping the order the select asked for
    plans, reasons = row.pop("plans"), row.pop("plan_reasons")
    courses = [course for plan in plans for course in plan.pop("plan_courses")]
    return PlanSetRows(
        plan_set=PlanSet.model_validate(row),
        plans=tuple(Plan.model_validate(plan) for plan in plans),
        plan_courses=tuple(PlanCourse.model_validate(course) for course in courses),
        plan_reasons=tuple(PlanReason.model_validate(reason) for reason in reasons),
    )
