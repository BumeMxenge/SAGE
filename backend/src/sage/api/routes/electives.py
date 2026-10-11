# Explore Electives and hearting: the courses she can add, by tab, and her favourites
from fastapi import APIRouter

from sage.api.deps import ONBOARDED_ERRORS, Checker, Onboarded, Rules, Students
from sage.api.models import Elective, Electives, Eligibility, Tab
from sage.api.problems import errors
from sage.domain.errors import CourseNotFound, InvalidRequest, RulebookNotLoaded
from sage.services import electives

router = APIRouter(tags=["electives"])


@router.get(
    "/electives",
    summary="The current year's electives by tab, with whether she may take each",
    responses=errors(*ONBOARDED_ERRORS, RulebookNotLoaded),
)
def get_electives(
    student: Onboarded, students: Students, rulebook: Rules, checker: Checker
) -> Electives:
    return Electives(
        tabs=[
            Tab(
                key=tab,
                courses=[
                    Elective(
                        code=row.course.code,
                        name=row.course.name,
                        credits=row.course.credits,
                        term=row.course.term,
                        summary=row.course.summary,
                        convener=row.course.convener,
                        favourite=row.favourite,
                        eligibility=Eligibility.model_validate(
                            row.eligibility, from_attributes=True
                        ),
                    )
                    for row in rows
                ],
            )
            for tab, rows in electives.by_tab(students, rulebook, checker, student.id)
        ]
    )


@router.put(
    "/favourites/{course_code}",
    status_code=204,
    summary="Heart a course; hearting it again changes nothing",
    responses=errors(
        *ONBOARDED_ERRORS, InvalidRequest, CourseNotFound, RulebookNotLoaded
    ),
)
def add_favourite(
    course_code: str, student: Onboarded, students: Students, rulebook: Rules
) -> None:
    electives.heart(students, rulebook, student.id, course_code)


@router.delete(
    "/favourites/{course_code}",
    status_code=204,
    summary="Unheart a course; unhearting it again changes nothing",
    responses=errors(
        *ONBOARDED_ERRORS, InvalidRequest, CourseNotFound, RulebookNotLoaded
    ),
)
def remove_favourite(
    course_code: str, student: Onboarded, students: Students, rulebook: Rules
) -> None:
    electives.unheart(students, rulebook, student.id, course_code)
