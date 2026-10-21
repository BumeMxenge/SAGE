# Onboarding's bodies: the transcript to review, the catalogue the review screen picks from, and
# the lines she confirms at Finish setup
from datetime import date

from pydantic import BaseModel, Field, field_validator

from sage.ingestion.transcript import WarningCode
from sage.shared.api.models import Course, RequestBody
from sage.shared.rules import COURSE_CODE, Outcome, TermCode


class Curriculum(BaseModel):
    code: str
    name: str


class ResultSymbol(BaseModel):
    symbol: str
    outcome: Outcome
    label: str


class CatalogueCourse(Course):
    # Whether the handbook lists it as an approved complementary studies course, which the review's
    # course picker shows apart from the programme's own courses
    complementary: bool


class Catalogue(BaseModel):
    # What the review screen picks from: the curricula, the courses for adding a line, and the
    # results for its outcome menu
    year: int
    curricula: list[Curriculum]
    courses: list[CatalogueCourse]
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
    course_code: str = Field(pattern=rf"^{COURSE_CODE}$")
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
