# The interfaces adapters implement: one home for the rulebook, one for students' data. Services
# depend on these and never on Supabase, so unit tests can use the in-memory versions instead.
# Every student method reads or writes only the rows of the student it names.
from collections.abc import Collection, Sequence
from typing import Any, Protocol
from uuid import UUID

from sage.shared.rules import ResultSymbol, RuleSet
from sage.shared.students import (
    Chat,
    Citation,
    CitedMessage,
    CourseHistoryLine,
    Message,
    PlanSetRows,
    Student,
    StudentRecord,
    StudentState,
)


class AccountNotFound(Exception):
    # No sign-in account has this student's id, so her rows have nothing to belong to
    pass


class YearInUse(Exception):
    # A student's plan, or a citation of a passage, uses this handbook year, so it can't be removed
    pass


class RuleRepository(Protocol):
    # Every stored row of one handbook year
    def get(self, year: int) -> RuleSet: ...

    # Makes the stored year exactly these rows, which hold one handbook year's version and rows,
    # removing whatever it held before. Raises YearInUse while a student's row uses the year.
    def replace_year(self, rules: RuleSet) -> None: ...

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

    # Shows the kept plans in the set and hides the rest, so a retry after a failure leaves exactly
    # its own answers' plans visible, whatever an earlier attempt hid
    def hide_plans(
        self, student_id: UUID, plan_set_id: UUID, keep: Collection[UUID]
    ) -> None: ...

    # Stores the questionnaire's answers on the set, which marks it answered
    def save_answers(
        self, student_id: UUID, plan_set_id: UUID, answers: dict[str, Any]
    ) -> None: ...

    # Her course history and hearted courses, in one read
    def record(self, student_id: UUID) -> StudentRecord: ...

    # Hearts a course. Hearting it again changes nothing.
    def add_favourite(self, student_id: UUID, course_code: str) -> None: ...

    # Unhearts a course. Unhearting one she never hearted changes nothing.
    def remove_favourite(self, student_id: UUID, course_code: str) -> None: ...

    # Her chats on exactly this plan, or this pair stored lowest id first, newest first
    def chats(
        self, student_id: UUID, plan_id: UUID, other_plan_id: UUID | None
    ) -> tuple[Chat, ...]: ...

    # One of her chats, or None if it isn't hers
    def chat(self, student_id: UUID, chat_id: UUID) -> Chat | None: ...

    # Stores a new chat, and returns it with the time it was stored
    def add_chat(self, chat: Chat) -> Chat: ...

    # The chat's messages in order, with what each cites, or None if the chat isn't hers
    def messages(
        self, student_id: UUID, chat_id: UUID
    ) -> tuple[CitedMessage, ...] | None: ...

    # Stores a question and its reply in one write, so neither is kept without the other, then the
    # reply's citations. Returns both with the times they were stored, the question first.
    def add_exchange(
        self, question: Message, reply: Message, citations: Sequence[Citation]
    ) -> tuple[Message, Message]: ...
