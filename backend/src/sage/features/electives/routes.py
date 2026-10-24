# Explore Electives and hearting: the courses she can add, by tab, and her favourites
from fastapi import APIRouter

from sage.features.electives import service as electives
from sage.features.electives.models import Elective, Electives, Offering, Tab
from sage.shared.api.deps import ONBOARDED_ERRORS, Checker, Onboarded, Rules, Students
from sage.shared.api.problems import errors
from sage.shared.errors import CourseNotFound, InvalidRequest, RulebookNotLoaded

router = APIRouter(tags=["electives"])


@router.get(
    "/electives",
    summary="The current year's electives by tab, one card per course, with whether she can "
    "heart each offering",
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
                        codes=[o.course.code for o in card.offerings],
                        name=card.offerings[0].course.name,
                        credits=card.offerings[0].course.credits,
                        summary=card.offerings[0].course.summary,
                        convener=card.offerings[0].course.convener,
                        hearted=card.hearted,
                        can_heart=card.can_heart,
                        note=card.note,
                        offerings=[
                            Offering(
                                code=o.course.code,
                                term=o.course.term,
                                hearted=o.hearted,
                                can_heart=o.works,
                            )
                            for o in card.offerings
                        ],
                    )
                    for card in cards
                ],
            )
            for tab, cards in electives.by_tab(students, rulebook, checker, student)
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
