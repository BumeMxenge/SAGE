# One student's data as types: one per table row, named after its columns. Timestamps the database
# stamps itself (created_at, updated_at) are left out until something reads them.
from typing import Any
from uuid import UUID

from sage.domain.base import Row


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
    choices: dict[str, str] | None = None


class PlanReason(Row):
    id: UUID
    plan_set_id: UUID
    student_id: UUID
    plan_id: UUID | None = None
    course_code: str | None = None
    passage_id: UUID | None = None
    kind: str
    message: str
    details: dict[str, Any] | None = None


class Chat(Row):
    id: UUID
    student_id: UUID
    plan_id: UUID
    other_plan_id: UUID | None = None
    title: str | None = None


class Message(Row):
    id: UUID
    chat_id: UUID
    student_id: UUID
    role: str
    content: str
    term: str | None = None


class MessageCitation(Row):
    message_id: UUID
    passage_id: UUID
    student_id: UUID
    position: int
    quote: str


class PlanSetRows(Row):
    # A plan set with some or all of its plans, their courses and the reasons, as the API reads them
    plan_set: PlanSet
    plans: tuple[Plan, ...] = ()
    plan_courses: tuple[PlanCourse, ...] = ()
    plan_reasons: tuple[PlanReason, ...] = ()


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
