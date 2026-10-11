# The API's contract: every request and response body. These stay separate from the domain's row
# types, so the database can change without the frontend noticing, and the other way round.
from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sage.domain.electives import ElectiveTab
from sage.domain.planning import EligibilityStatus
from sage.domain.rules import Outcome, TermCode
from sage.domain.students import ReasonKind
from sage.ingestion.transcript import WarningCode
from sage.services.questionnaire import QuestionId


class RequestBody(BaseModel):
    # A request body refuses keys it doesn't know, so a misspelt field is an error, not ignored
    model_config = ConfigDict(extra="forbid")


class Health(BaseModel):
    status: Literal["ok"]
    commit: str  # the commit the image was built from; "dev" on a laptop


class Me(BaseModel):
    email: str
    name: str | None
    account: Literal["student", "staff"]
    student_number: str | None  # students only
    # False until she finishes setup, and always false for staff
    onboarding_complete: bool


class Curriculum(BaseModel):
    code: str
    name: str


class Course(BaseModel):
    code: str
    name: str
    credits: int
    term: TermCode


class ResultSymbol(BaseModel):
    symbol: str
    outcome: Outcome
    label: str


class Catalogue(BaseModel):
    # What the review screen picks from: the curricula, the courses for adding a line, and the
    # results for its outcome menu
    year: int
    curricula: list[Curriculum]
    courses: list[Course]
    symbols: list[ResultSymbol]


class TranscriptLine(BaseModel):
    academic_year: int
    term: TermCode
    course_code: str
    course_name: str
    credits: int
    nqf_level: int | None
    result: str
    mark: int | None
    unverified: bool  # part of it was guessed, so the review screen flags it


class TranscriptWarning(BaseModel):
    code: WarningCode
    message: str


class Transcript(BaseModel):
    # What the review screen starts from. Nothing of it is stored until Finish setup.
    student_number: str
    programme: str | None  # the latest year's, as printed
    # The current curricula that programme could be
    curriculum_options: list[Curriculum]
    issued_on: date | None
    lines: list[TranscriptLine]
    warnings: list[TranscriptWarning]


class ConfirmedLine(RequestBody):
    academic_year: int = Field(ge=2000, le=2100)
    term: TermCode
    # The handbook's format
    course_code: str = Field(pattern=r"^[A-Z]{3}[0-9]{4}[A-Z]$")
    course_name: str = Field(min_length=1)
    credits: int = Field(ge=0, le=32767)  # course_history.credits is a smallint
    nqf_level: int | None = Field(ge=5, le=10)
    result: str
    mark: int | None = Field(ge=0, le=100)


class Setup(RequestBody):
    curriculum_code: str
    lines: list[ConfirmedLine] = Field(min_length=1)

    @field_validator("lines")
    @classmethod
    def one_line_per_course_and_term(
        cls, lines: list[ConfirmedLine]
    ) -> list[ConfirmedLine]:
        # Her history keeps one line per course in each year and term
        seen = set()
        for line in lines:
            key = (line.academic_year, line.term, line.course_code)
            if key in seen:
                raise ValueError(
                    f"{line.course_code} is listed twice for {line.academic_year} {line.term}"
                )
            seen.add(key)
        return lines


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


class Option(BaseModel):
    id: str  # a course code, or one of the week options, or no_preference
    label: str
    hearted: bool  # a course she hearted, listed first
    keeps: list[UUID]  # the plans this answer keeps


class Question(BaseModel):
    id: QuestionId
    prompt: str
    hint: str | None
    options: list[Option]


class Questionnaire(BaseModel):
    needed: bool
    questions: list[Question]  # empty when it isn't needed


class Answers(RequestBody):
    # An option id per question. A question left out doesn't narrow her plans.
    course: str | None = None
    week: Literal["fewest_8am", "lunch_free", "no_preference"] | None = None


class Eligibility(BaseModel):
    status: EligibilityStatus
    reason: str | None


class Elective(Course):
    summary: str | None  # the card's outline
    convener: str | None
    favourite: bool
    eligibility: Eligibility


class Tab(BaseModel):
    key: ElectiveTab  # the tab's label lives in the frontend
    courses: list[Elective]


class Electives(BaseModel):
    tabs: list[Tab]


class HistoryLine(BaseModel):
    code: str
    name: str
    term: TermCode
    credits: int
    nqf_level: int | None
    result: str
    mark: int | None


class HistoryYear(BaseModel):
    academic_year: int
    year_of_study: int  # her first year is 1
    credits: int
    # The credit-weighted mean of marks to two decimals, as the transcript's Term GPA works it out;
    # null when no line has a mark
    average: float | None
    lines: list[HistoryLine]


class History(BaseModel):
    cumulative_average: float | None
    years: list[HistoryYear]  # newest first


class Chat(BaseModel):
    id: UUID
    plan_id: UUID
    # The second plan of a compared pair, stored lowest id first
    other_plan_id: UUID | None
    title: str | None  # named after the first exchange; null until then
    created_at: datetime


class NewChat(RequestBody):
    plan_id: UUID
    other_plan_id: UUID | None = None  # set to chat about a pair, in either order


class Citation(BaseModel):
    position: int  # its number in the answer
    quote: str
    source: str
    section: str
    page: int


class Message(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    term: TermCode | None  # the term on screen when she asked
    created_at: datetime
    referral: bool  # the reply hands the question to a human advisor
    open_plan_id: UUID | None  # a plan the reply offers to open
    citations: list[Citation]


class NewMessage(RequestBody):
    content: str = Field(min_length=1, max_length=2000)
    term: TermCode | None = None


class Exchange(BaseModel):
    question: Message
    reply: Message
