# The plans' bodies: her set, one plan in full, and two side by side
from datetime import time
from uuid import UUID

from pydantic import BaseModel

from sage.shared.api.models import Course
from sage.shared.rules import TermCode
from sage.shared.students import ReasonKind


class Reason(BaseModel):
    kind: ReasonKind
    message: str
    course_code: str | None
    # Where the passage it cites sits in the handbook, when it cites one
    source: str | None
    section: str | None
    page: int | None


class PlanSummary(BaseModel):
    id: UUID
    position: int
    name: str
    hidden: bool  # hidden by the questionnaire, but still hers to open
    credits: int


class PlanSet(BaseModel):
    period: int  # the year planned
    version: int
    questionnaire_needed: bool
    reasons: list[Reason]  # about the whole set
    plans: list[PlanSummary]


class Group(BaseModel):
    # A list the course is on, among those her curriculum's rules name, such as core or electives
    key: str
    label: str


class Meeting(BaseModel):
    term: TermCode
    day: int | None  # 1 is Monday; null when the handbook prints no day
    start_time: time | None  # null when the handbook prints no time
    end_time: time | None
    kind: str | None
    # An alternative she hasn't chosen between yet has its group and letter
    choice_group: str | None
    choice: str | None


class PlanCourse(Course):
    groups: list[Group]
    meetings: list[Meeting]


class Credits(BaseModel):
    total: int
    by_term: dict[TermCode, int]


class Plan(BaseModel):
    id: UUID
    period: int
    position: int
    name: str
    hidden: bool
    credits: Credits
    courses: list[PlanCourse]
    reasons: list[Reason]  # the set's, then the plan's own


class Comparison(BaseModel):
    first: Plan
    second: Plan
    shared: list[str]  # course codes
    only_first: list[str]
    only_second: list[str]
