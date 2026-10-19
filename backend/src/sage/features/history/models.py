# Her course history by year, as /v1/history answers with it
from pydantic import BaseModel

from sage.shared.rules import TermCode


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
    # null when no line counts towards it
    average: float | None
    lines: list[HistoryLine]


class History(BaseModel):
    cumulative_average: float | None
    years: list[HistoryYear]  # newest first
