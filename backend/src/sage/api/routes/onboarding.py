# Onboarding: the catalogue the review screen picks from, and Finish setup, which saves the lines she
# confirmed and attaches her plans
from fastapi import APIRouter, Depends

from sage.api.deps import (
    STUDENT_ERRORS,
    Generator,
    Rules,
    StudentAccount,
    Students,
    student_account,
)
from sage.api.models import Catalogue, Course, Curriculum, Me, ResultSymbol, Setup
from sage.api.problems import errors
from sage.api.routes.me import me
from sage.domain.errors import (
    InvalidRequest,
    RulebookNotLoaded,
    UnknownCurriculum,
    UnknownResult,
)
from sage.domain.students import CourseHistoryLine
from sage.services import onboarding

router = APIRouter(tags=["onboarding"])


@router.get(
    "/catalogue",
    summary="The current handbook's curricula, courses and result symbols",
    dependencies=[Depends(student_account)],
    responses=errors(*STUDENT_ERRORS, RulebookNotLoaded),
)
def get_catalogue(rulebook: Rules) -> Catalogue:
    year = rulebook.current_year()
    rules = rulebook.year(year)
    return Catalogue(
        year=year,
        curricula=[
            Curriculum(code=row.code, name=row.name)
            for row in sorted(rules.curricula, key=lambda row: row.code)
        ],
        courses=[
            Course.model_validate(row, from_attributes=True)
            for row in sorted(rules.courses, key=lambda row: row.code)
        ],
        symbols=[
            ResultSymbol.model_validate(row, from_attributes=True)
            for row in rulebook.symbols().values()
        ],
    )


@router.post(
    "/onboarding/complete",
    summary="Save the course history she confirmed, and attach her plans",
    responses=errors(
        *STUDENT_ERRORS,
        InvalidRequest,
        UnknownCurriculum,
        UnknownResult,
        RulebookNotLoaded,
    ),
)
def complete_onboarding(
    setup: Setup,
    account: StudentAccount,
    students: Students,
    rulebook: Rules,
    generator: Generator,
) -> Me:
    history = [
        CourseHistoryLine(student_id=account.id, **line.model_dump())
        for line in setup.lines
    ]
    profile = onboarding.complete(
        account.id, setup.curriculum_code, history, students, rulebook, generator
    )
    return me(account, onboarding_complete=profile.onboarding_complete)
