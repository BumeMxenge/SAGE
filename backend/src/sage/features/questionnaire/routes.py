# The questionnaire that narrows a long plan set: its questions, and her answers, which hide every
# plan they don't keep
from fastapi import APIRouter

from sage.features.plans.routes import get_plans
from sage.features.questionnaire import service as questionnaire
from sage.shared.api.deps import ONBOARDED_ERRORS, Onboarded, Rules, Students
from sage.shared.api.models import Answers, PlanSet, Question, Questionnaire
from sage.shared.api.problems import errors
from sage.shared.errors import (
    InvalidRequest,
    NoPlanMatches,
    QuestionnaireAnswered,
    QuestionnaireNotNeeded,
    RulebookNotLoaded,
    UnknownAnswer,
)

router = APIRouter(prefix="/questionnaire", tags=["questionnaire"])


@router.get(
    "",
    summary="Whether her plan set needs narrowing, and the questions that would",
    responses=errors(*ONBOARDED_ERRORS, RulebookNotLoaded),
)
def get_questionnaire(
    student: Onboarded, students: Students, rulebook: Rules
) -> Questionnaire:
    questions = questionnaire.current(students, rulebook, student)
    return Questionnaire(
        needed=questions is not None,
        questions=[
            Question.model_validate(question, from_attributes=True)
            for question in questions or ()
        ],
    )


@router.post(
    "",
    summary="Answer the questionnaire, hiding every plan the answers don't keep",
    responses=errors(
        *ONBOARDED_ERRORS,
        InvalidRequest,
        QuestionnaireNotNeeded,
        QuestionnaireAnswered,
        UnknownAnswer,
        NoPlanMatches,
        RulebookNotLoaded,
    ),
)
def answer_questionnaire(
    answers: Answers, student: Onboarded, students: Students, rulebook: Rules
) -> PlanSet:
    questionnaire.answer(
        students, rulebook, student, answers.model_dump(exclude_none=True)
    )
    return get_plans(student, students, rulebook)
