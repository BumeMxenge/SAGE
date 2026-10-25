# Explore Electives' bodies: each tab's courses, one card per course, with whether she can heart each
# offering and has hearted it
from uuid import UUID

from pydantic import BaseModel

from sage.shared.rules import ElectiveTab, TermCode


class Offering(BaseModel):
    code: str
    term: TermCode
    convener: str | None  # each term's own, as a course's can differ
    hearted: bool
    can_heart: bool  # it works: the engine doesn't refuse it, and it fits her plans
    # Her current set's plans, shown or hidden, whose complementary slots list it, by position
    plans: list[UUID]


class Elective(BaseModel):
    # One course, offered once or in more than one term. Hearting the card hearts every offering she
    # can heart, and unhearting it unhearts every one she hearted.
    codes: list[str]
    name: str
    credits: int
    summary: str | None  # the card's outline
    hearted: bool  # any offering is
    can_heart: bool  # any offering can be
    note: str | None  # why she can't heart it, or what to check before taking it
    offerings: list[Offering]


class Tab(BaseModel):
    key: ElectiveTab  # the tab's label lives in the frontend
    courses: list[Elective]


class Electives(BaseModel):
    tabs: list[Tab]
