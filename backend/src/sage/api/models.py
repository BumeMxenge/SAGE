# The API's contract: every request and response body. These stay separate from the domain's row
# types, so the database can change without the frontend noticing, and the other way round.
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sage.domain.rules import Outcome, TermCode
from sage.ingestion.transcript import WarningCode


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
    onboarding_complete: (
        bool  # false until she finishes setup, and always false for staff
    )


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
    curriculum_options: list[
        Curriculum
    ]  # the current curricula that programme could be
    issued_on: date | None
    lines: list[TranscriptLine]
    warnings: list[TranscriptWarning]


class ConfirmedLine(RequestBody):
    academic_year: int = Field(ge=2000, le=2100)
    term: TermCode
    course_code: str = Field(
        pattern=r"^[A-Z]{3}[0-9]{4}[A-Z]$"
    )  # the handbook's format
    course_name: str = Field(min_length=1)
    credits: int = Field(ge=0)
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
