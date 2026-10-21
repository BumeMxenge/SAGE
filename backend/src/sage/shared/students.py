# One student's data as types: one per table row, named after its columns. Timestamps the database
# stamps itself (created_at, updated_at) are left out until something reads them, and then are
# read-only: excluded from every dump, so a write never sends one.
from collections.abc import Iterable
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal, Protocol
from uuid import UUID

from pydantic import Field

from sage.shared.base import Row


class Student(Row):
    id: UUID  # the sign-in account's id
    curriculum_code: str | None = None
    intake_year: int | None = None
    onboarding_complete: bool = False


class CourseHistoryLine(Row):
    student_id: UUID
    academic_year: int
    term: str
    course_code: str
    course_name: str
    credits: int
    nqf_level: int | None = None
    result: str
    mark: int | None = None


class Favourite(Row):
    student_id: UUID
    course_code: str


class PlanSet(Row):
    id: UUID
    student_id: UUID
    period: int
    version: int
    complete: bool = False
    answers: dict[str, Any] | None = None


class Plan(Row):
    id: UUID
    plan_set_id: UUID
    student_id: UUID
    position: int
    name: str
    hidden: bool = False


class PlanCourse(Row):
    plan_id: UUID
    course_code: str
    student_id: UUID
    handbook_year: int
    # Each choice group's alternatives that fit the rest of the plan, sorted, such as
    # {"lab": ["A", "B"]}. One left is fixed, and a group not here shows every alternative.
    choices: dict[str, list[str]] | None = None


# What a reason explains, as plan_reasons.kind allows
ReasonKind = Literal["excluded", "conflict", "conditional", "included"]


class PlanReason(Row):
    id: UUID
    plan_set_id: UUID
    student_id: UUID
    plan_id: UUID | None = None
    course_code: str | None = None
    passage_id: UUID | None = None
    kind: ReasonKind
    message: str
    details: dict[str, Any] | None = None


class Chat(Row):
    id: UUID
    student_id: UUID
    plan_id: UUID
    other_plan_id: UUID | None = None
    title: str | None = None
    created_at: datetime | None = Field(default=None, exclude=True)


class Message(Row):
    id: UUID
    chat_id: UUID
    student_id: UUID
    role: Literal["user", "assistant"]
    content: str
    term: str | None = None
    referral: bool = False  # the reply hands the question to a human advisor
    open_plan_id: UUID | None = None  # a plan the reply offers to open
    created_at: datetime | None = Field(default=None, exclude=True)


class MessageCitation(Row):
    message_id: UUID
    passage_id: UUID
    student_id: UUID
    position: int
    quote: str


class Citation(Row):
    # A handbook passage an answer cites: the words quoted and where the passage sits
    passage_id: UUID
    position: int
    quote: str
    source: str
    section: str
    page: int


class CitedMessage(Row):
    # A message as a chat shows it, with the passages it cites
    message: Message
    citations: tuple[Citation, ...] = ()


class PlanSetRows(Row):
    # A plan set with some or all of its plans, their courses and the reasons, as the API reads them
    plan_set: PlanSet
    plans: tuple[Plan, ...] = ()
    plan_courses: tuple[PlanCourse, ...] = ()
    plan_reasons: tuple[PlanReason, ...] = ()


class StudentRecord(Row):
    # Her course history and the codes of the courses she hearted, which the planner reads together
    course_history: tuple[CourseHistoryLine, ...] = ()
    favourites: tuple[str, ...] = ()


class StudentState(Row):
    # Her profile, then her rows named after their tables, in foreign-key order
    student: Student
    course_history: tuple[CourseHistoryLine, ...] = ()
    favourites: tuple[Favourite, ...] = ()
    plan_sets: tuple[PlanSet, ...] = ()
    plans: tuple[Plan, ...] = ()
    plan_courses: tuple[PlanCourse, ...] = ()
    plan_reasons: tuple[PlanReason, ...] = ()
    chats: tuple[Chat, ...] = ()
    messages: tuple[Message, ...] = ()
    message_citations: tuple[MessageCitation, ...] = ()


class Graded(Protocol):
    # Anything with a line's credits, mark and result: a stored line, or one read off a transcript
    credits: int
    mark: int | None
    result: str


def final_mark(line: Graded) -> int | None:
    # A line's final mark as the transcript's Term GPA reads it: a supplementary pass (SP) counts as
    # 50, and any other line printed without a mark has none
    return 50 if line.result == "SP" else line.mark


def average(lines: Iterable[Graded]) -> Decimal | None:
    # The credit-weighted mean of final marks, worked out as the transcript's Term GPA is. A line
    # without one is left out. Two decimals, half up, and None when no line counts.
    total = weight = 0
    for line in lines:
        mark = final_mark(line)
        if mark is not None:
            total += mark * line.credits
            weight += line.credits
    if not weight:
        return None
    return (Decimal(total) / weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def message_citations(
    reply: Message, citations: Iterable[Citation]
) -> tuple[MessageCitation, ...]:
    # The rows that store what a reply cites
    return tuple(
        MessageCitation(
            message_id=reply.id,
            passage_id=citation.passage_id,
            student_id=reply.student_id,
            position=citation.position,
            quote=citation.quote,
        )
        for citation in citations
    )
