# Her course history, as she confirmed it at Finish setup, by year with averages
from decimal import Decimal

from fastapi import APIRouter

from sage.services import history
from sage.shared.api.deps import ONBOARDED_ERRORS, Onboarded, Students
from sage.shared.api.models import History, HistoryLine, HistoryYear
from sage.shared.api.problems import errors

router = APIRouter(tags=["history"])


@router.get(
    "/history",
    summary="Her course history by year, newest first, with averages",
    responses=errors(*ONBOARDED_ERRORS),
)
def get_history(student: Onboarded, students: Students) -> History:
    found = history.summary(
        students.record(student.id).course_history, student.intake_year
    )
    return History(
        cumulative_average=number(found.cumulative_average),
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
            for year in found.years
        ],
    )


def number(value: Decimal | None) -> float | None:
    # A plain JSON number for the frontend, worked out exactly before this
    return float(value) if value is not None else None
