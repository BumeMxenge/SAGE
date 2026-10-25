# The plans' bodies: her set, one plan in full, and two side by side
from datetime import time
from typing import Literal
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
    name: str  # its electives' theme words, such as "Power, Control & Robotics"
    # Its electives' codes, such as "EEE4117F · EEE4118F · EEE4119F", which the planner prints
    # under its name; null when it has none
    combination: str | None
    hidden: bool  # hidden by the questionnaire, but still hers to open
    credits: int
    to_choose: int  # the credits of its complementary slots, not chosen yet


class PlanSet(BaseModel):
    period: int  # the year planned
    version: int
    questionnaire_needed: bool
    # A plan in it, shown or hidden, has a complementary slot or a 576-credit place, so Explore
    # Electives is hers to open
    has_slot: bool
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
    # An alternative has its group and choice, such as a letter or CSC3002F's pair of days. Only
    # the alternatives that fit her plan are listed, so a group with one is fixed.
    choice_group: str | None
    choice: str | None


class PlanCourse(Course):
    groups: list[Group]
    meetings: list[Meeting]


class Credits(BaseModel):
    total: int
    by_term: dict[TermCode, int]
    to_choose: int  # as in PlanSummary


class Slot(BaseModel):
    # A gap the plan leaves her to fill with an approved complementary studies course: a line of the
    # year's complementary credits, or a 576-credit place standing in for a course she still owes
    kind: Literal["line", "place"]
    credits: int  # the line's credits, or the fewest a place takes
    replaces: str | None  # the course a place stands in for, such as ASL1200S
    message: str  # the engine's words, which say why when nothing fits
    # The courses that fit the plan, joining a course's offerings as Explore Electives' cards do, and
    # how many of them need a check with her advisor: a meeting with no printed time, or fewer
    # credits than the line
    fit_count: int
    check_count: int


class Plan(BaseModel):
    id: UUID
    period: int
    position: int
    name: str
    combination: str | None  # as in PlanSummary
    hidden: bool
    credits: Credits
    courses: list[PlanCourse]
    reasons: list[Reason]  # the set's, then the plan's own
    slots: list[Slot]


class ForcedSection(BaseModel):
    # A section of one of the plan's own courses that a previewed course leaves as the only one
    course_code: str
    choice_group: str
    choice: str


class PlanPreview(BaseModel):
    # What the plan would look like with one course taken in its complementary slot. Nothing is
    # saved: the plan itself never changes.
    # With the course added on its fitting sections, each forced section fixed, and the slot it
    # fills left out
    plan: Plan
    course_code: str  # which of plan.courses is the preview
    forced: list[ForcedSection]


class Comparison(BaseModel):
    first: Plan
    second: Plan
    shared: list[str]  # course codes
    only_first: list[str]
    only_second: list[str]
