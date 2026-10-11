# Each student's data in Supabase. Replacing her deletes her profile row, which cascades to
# everything of hers, then writes the new state table by table in foreign-key order. Separate REST
# calls can't share a transaction, so a replace that fails part-way is repaired by running it again.
from uuid import UUID

from postgrest import APIError
from supabase import Client

from sage.adapters.supabase.tables import insert, row_type, select
from sage.domain.repositories import AccountNotFound
from sage.domain.students import Student, StudentState

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
        sid = str(student_id)
        profiles = select(self._client, "students", Student, "id", sid, ("id",))
        if not profiles:
            return None
        return StudentState(
            student=profiles[0],
            **{
                table: select(
                    self._client,
                    table,
                    row_type(StudentState, table),
                    "student_id",
                    sid,
                    order,
                )
                for table, order in ORDER.items()
            },
        )
