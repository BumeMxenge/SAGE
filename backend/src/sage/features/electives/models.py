# Explore Electives' bodies: each tab's courses, with whether she may take each and has hearted it
from pydantic import BaseModel

from sage.shared.api.models import Course
from sage.shared.planning import EligibilityStatus
from sage.shared.rules import ElectiveTab


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
