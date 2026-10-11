# Each student's data in one dictionary, keyed by her account id. Reads come back in the order the
# Supabase adapter returns them, so the two can be checked against each other.
from collections.abc import Callable, Collection, Iterable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sage.domain.base import Row
from sage.domain.students import (
    Chat,
    Citation,
    CitedMessage,
    CourseHistoryLine,
    Favourite,
    Message,
    MessageCitation,
    Plan,
    PlanSetRows,
    Student,
    StudentRecord,
    StudentState,
)

# Where the fake's clock starts. Each stored chat and message gets the next microsecond, so they
# keep the order they were written in, as Postgres's clock_timestamp() gives them.
EPOCH = datetime(2026, 1, 1, tzinfo=UTC)


class InMemoryStudentRepository:
    def __init__(self) -> None:
        self._students: dict[UUID, StudentState] = {}
        self._ticks = 0
        # The database joins a citation to its passage; the fake keeps what it was handed instead
        self._citations: dict[UUID, tuple[Citation, ...]] = {}

    def replace(self, state: StudentState) -> None:
        self._students[state.student.id] = state.model_copy(
            update={
                "chats": tuple(self._stamp(row) for row in state.chats),
                "messages": tuple(self._stamp(row) for row in state.messages),
            }
        )

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
        return tuple(
            _plan_rows(state, plan) for plan in state.plans if plan.id in plan_ids
        )

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

    def chats(
        self, student_id: UUID, plan_id: UUID, other_plan_id: UUID | None
    ) -> tuple[Chat, ...]:
        state = self._students.get(student_id)
        found = [
            chat
            for chat in (state.chats if state else ())
            if chat.plan_id == plan_id and chat.other_plan_id == other_plan_id
        ]
        return tuple(
            sorted(found, key=lambda chat: (chat.created_at, chat.id), reverse=True)
        )

    def chat(self, student_id: UUID, chat_id: UUID) -> Chat | None:
        state = self._students.get(student_id)
        return next(
            (chat for chat in (state.chats if state else ()) if chat.id == chat_id),
            None,
        )

    def add_chat(self, chat: Chat) -> Chat:
        stored = self._stamp(chat)
        self._change(
            chat.student_id, chats=(*self._students[chat.student_id].chats, stored)
        )
        return stored

    def messages(
        self, student_id: UUID, chat_id: UUID
    ) -> tuple[CitedMessage, ...] | None:
        if self.chat(student_id, chat_id) is None:
            return None
        found = [
            row for row in self._students[student_id].messages if row.chat_id == chat_id
        ]
        return tuple(
            CitedMessage(message=row, citations=self._citations.get(row.id, ()))
            for row in sorted(found, key=lambda row: (row.created_at, row.id))
        )

    def add_exchange(
        self, question: Message, reply: Message, citations: Sequence[Citation]
    ) -> tuple[Message, Message]:
        state = self._students[reply.student_id]
        stored = self._stamp(question), self._stamp(reply)
        cited = tuple(
            MessageCitation(
                message_id=reply.id,
                passage_id=citation.passage_id,
                student_id=reply.student_id,
                position=citation.position,
                quote=citation.quote,
            )
            for citation in citations
        )
        self._change(
            reply.student_id,
            messages=(*state.messages, *stored),
            message_citations=(*state.message_citations, *cited),
        )
        self._citations[reply.id] = tuple(citations)
        return stored

    def _stamp[T: (Chat, Message)](self, row: T) -> T:
        if row.created_at is not None:
            return row
        self._ticks += 1
        return row.model_copy(
            update={"created_at": EPOCH + timedelta(microseconds=self._ticks)}
        )

    def _change(self, student_id: UUID, **tables: tuple[Row, ...]) -> None:
        self._students[student_id] = self._students[student_id].model_copy(
            update=tables
        )


def _plan_rows(state: StudentState, plan: Plan) -> PlanSetRows:
    # The plan in its set, with its courses, then the set's reasons and the plan's own
    reasons = sorted(
        (row for row in state.plan_reasons if row.plan_set_id == plan.plan_set_id),
        key=lambda row: row.id,
    )
    courses = [row for row in state.plan_courses if row.plan_id == plan.id]
    return PlanSetRows(
        plan_set=next(row for row in state.plan_sets if row.id == plan.plan_set_id),
        plans=(plan,),
        plan_courses=tuple(sorted(courses, key=lambda row: row.course_code)),
        plan_reasons=(
            *(row for row in reasons if row.plan_id is None),
            *(row for row in reasons if row.plan_id == plan.id),
        ),
    )


def _added[T: Row](
    stored: tuple[T, ...], new: Iterable[T], key: Callable[[T], Any]
) -> tuple[T, ...]:
    # The stored rows plus each new row whose key isn't stored yet, as an insert that skips
    # existing rows would leave them
    have = {key(row) for row in stored}
    return stored + tuple(row for row in new if key(row) not in have)
