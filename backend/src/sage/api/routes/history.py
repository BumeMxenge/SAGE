# Her course history, as she confirmed it at Finish setup, by year with averages
from decimal import Decimal

from fastapi import APIRouter

from sage.api.deps import ONBOARDED_ERRORS, Onboarded, Students
from sage.api.models import History, HistoryLine, HistoryYear
from sage.api.problems import errors
from sage.domain.students import average
from sage.services import history

router = APIRouter(tags=["history"])


@router.get(
    "/history",
    summary="Her course history by year, newest first, with averages",
    responses=errors(*ONBOARDED_ERRORS),
)
def get_history(student: Onboarded, students: Students) -> History:
    lines = students.record(student.id).course_history
    return History(
        cumulative_average=number(average(lines)),
        years=[
            HistoryYear(
                academic_year=year.academic_year,
                year_of_study=year.year_of_study,
                credits=year.credits,
                average=number(year.average),
                lines=[
                    HistoryLine(
                        code=line.course_code,
                        name=line.course_name,
                        term=line.term,
                        credits=line.credits,
                        nqf_level=line.nqf_level,
                        result=line.result,
                        mark=line.mark,
                    )
                    for line in year.lines
                ],
            )
            for year in history.years(lines, student.intake_year)
        ],
    )


def number(value: Decimal | None) -> float | None:
    # A plain JSON number for the frontend, worked out exactly before this
    return float(value) if value is not None else None
