# The questionnaire's bodies: its questions, each option with the plans it keeps, and her answers
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from sage.features.questionnaire.service import QuestionId
from sage.shared.api.models import RequestBody


class Option(BaseModel):
    id: str  # a course code, or one of the week options, or no_preference
    label: str
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
