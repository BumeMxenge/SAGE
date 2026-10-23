# Every way SAGE turns a request down: one stable code each, which the frontend switches on, with its
# HTTP status and the sentence a student reads. Services, adapters and ingestion raise these, and the
# API sends them as problem details, so this module is the one list of codes.
from collections.abc import Mapping
from enum import StrEnum
from typing import ClassVar


# The type of a problem's code in the OpenAPI schema, so the frontend's generated types list every code
class Code(StrEnum):
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    INVALID_REQUEST = "invalid_request"
    INTERNAL_ERROR = "internal_error"
    NOT_SIGNED_IN = "not_signed_in"
    UCT_ACCOUNT_REQUIRED = "uct_account_required"
    STUDENTS_ONLY = "students_only"
    RULEBOOK_NOT_LOADED = "rulebook_not_loaded"
    UNKNOWN_CURRICULUM = "unknown_curriculum"
    UNKNOWN_RESULT = "unknown_result"
    NOT_A_PDF = "not_a_pdf"
    FILE_TOO_LARGE = "file_too_large"
    TRANSCRIPT_UNREADABLE = "transcript_unreadable"
    NOT_A_TRANSCRIPT = "not_a_transcript"
    TRANSCRIPT_NOT_YOURS = "transcript_not_yours"
    TRANSCRIPT_INCOMPLETE = "transcript_incomplete"
    NO_COURSE_HISTORY = "no_course_history"
    ONBOARDING_INCOMPLETE = "onboarding_incomplete"
    PLANS_NOT_READY = "plans_not_ready"
    PLAN_NOT_FOUND = "plan_not_found"
    SAME_PLAN = "same_plan"
    QUESTIONNAIRE_NOT_NEEDED = "questionnaire_not_needed"
    QUESTIONNAIRE_ANSWERED = "questionnaire_answered"
    UNKNOWN_ANSWER = "unknown_answer"
    NO_PLAN_MATCHES = "no_plan_matches"
    COURSE_NOT_FOUND = "course_not_found"
    DIFFERENT_PLAN_SETS = "different_plan_sets"
    QUESTIONNAIRE_PENDING = "questionnaire_pending"
    CHAT_NOT_FOUND = "chat_not_found"
    ADVISOR_UNAVAILABLE = "advisor_unavailable"


class Refusal(Exception):
    status: ClassVar[int]
    code: ClassVar[Code]
    # The detail a raise gives when it has nothing more specific to say
    message: ClassVar[str]
    headers: ClassVar[Mapping[str, str] | None] = None

    def __init__(self, detail: str | None = None, **extra: str) -> None:
        self.detail = detail or self.message
        # Extension members the problem carries, such as both student numbers
        self.extra = extra
        super().__init__(self.detail)


class RouteNotFound(Refusal):
    status, code = 404, Code.NOT_FOUND
    message = "There's nothing at this address."


class MethodNotAllowed(Refusal):
    status, code = 405, Code.METHOD_NOT_ALLOWED
    message = "This address doesn't take that method."


class InvalidRequest(Refusal):
    status, code = 422, Code.INVALID_REQUEST
    message = "Part of the request isn't valid. The errors list says what and where."


class InternalError(Refusal):
    status, code = 500, Code.INTERNAL_ERROR
    message = (
        "Something went wrong on our side. Try again, and if it keeps happening, "
        "quote the reference."
    )


class NotSignedIn(Refusal):
    status, code = 401, Code.NOT_SIGNED_IN
    message = "Your sign-in is missing or has expired. Sign in again."
    # HTTP's way of saying which kind of sign-in the API wants
    headers: ClassVar[Mapping[str, str]] = {"WWW-Authenticate": "Bearer"}


class UctAccountRequired(Refusal):
    status, code = 403, Code.UCT_ACCOUNT_REQUIRED
    message = (
        "SAGE is for UCT students and staff. Sign in with your UCT Microsoft account."
    )


class StudentsOnly(Refusal):
    status, code = 403, Code.STUDENTS_ONLY
    message = "This part of SAGE is for students."


class RulebookNotLoaded(Refusal):
    status, code = 503, Code.RULEBOOK_NOT_LOADED
    message = "The handbook rules aren't loaded yet. Try again later."


class UnknownCurriculum(Refusal):
    status, code = 422, Code.UNKNOWN_CURRICULUM
    message = "That curriculum isn't in the current handbook."


class UnknownResult(Refusal):
    status, code = 422, Code.UNKNOWN_RESULT
    message = "A result isn't one of UCT's result symbols."


class NotAPdf(Refusal):
    status, code = 415, Code.NOT_A_PDF
    message = "That file isn't a PDF. Export your transcript as a PDF and try again."


class FileTooLarge(Refusal):
    status, code = 413, Code.FILE_TOO_LARGE
    message = "That file is over 10 MB. Upload a smaller PDF of your transcript."


class TranscriptUnreadable(Refusal):
    status, code = 422, Code.TRANSCRIPT_UNREADABLE
    message = (
        "SAGE couldn't read this transcript. Download it again from PeopleSoft and "
        "upload the new copy."
    )


class NotATranscript(Refusal):
    status, code = 422, Code.NOT_A_TRANSCRIPT
    message = (
        "This PDF isn't a UCT academic record. Upload the academic record you "
        "downloaded from PeopleSoft."
    )


class TranscriptNotYours(Refusal):
    status, code = 422, Code.TRANSCRIPT_NOT_YOURS
    message = "This transcript belongs to another student."


class TranscriptIncomplete(Refusal):
    status, code = 422, Code.TRANSCRIPT_INCOMPLETE
    message = (
        "This transcript is missing pages. Download your whole academic record from "
        "PeopleSoft again."
    )


class NoCourseHistory(Refusal):
    status, code = 422, Code.NO_COURSE_HISTORY
    message = (
        "Your academic record has no courses on it yet. SAGE plans from your course "
        "history, so there's nothing to plan from. First-year registration follows "
        "the fixed first-year curriculum in the handbook."
    )


class OnboardingIncomplete(Refusal):
    status, code = 409, Code.ONBOARDING_INCOMPLETE
    message = "Finish setting up your account first."


class PlansNotReady(Refusal):
    status, code = 409, Code.PLANS_NOT_READY
    message = "Your plans aren't ready yet."


class PlanNotFound(Refusal):
    status, code = 404, Code.PLAN_NOT_FOUND
    message = "There's no plan with that id on your account."


class SamePlan(Refusal):
    status, code = 422, Code.SAME_PLAN
    message = "Choose two different plans."


class QuestionnaireNotNeeded(Refusal):
    status, code = 409, Code.QUESTIONNAIRE_NOT_NEEDED
    message = "Your plan set is short enough that it doesn't need the questionnaire."


class QuestionnaireAnswered(Refusal):
    status, code = 409, Code.QUESTIONNAIRE_ANSWERED
    message = "You've already answered the questionnaire."


class UnknownAnswer(Refusal):
    status, code = 422, Code.UNKNOWN_ANSWER
    message = "That answer isn't one of the options."


class NoPlanMatches(Refusal):
    status, code = 422, Code.NO_PLAN_MATCHES
    message = "No plan matches all of those answers. Change one and try again."


class CourseNotFound(Refusal):
    status, code = 404, Code.COURSE_NOT_FOUND
    message = "That course isn't in the current handbook."


class DifferentPlanSets(Refusal):
    status, code = 422, Code.DIFFERENT_PLAN_SETS
    message = "Those plans come from different plan sets, so they can't share a chat."


class QuestionnairePending(Refusal):
    status, code = 409, Code.QUESTIONNAIRE_PENDING
    message = "Answer the questionnaire before you start chatting about your plans."


class ChatNotFound(Refusal):
    status, code = 404, Code.CHAT_NOT_FOUND
    message = "There's no chat with that id on your account."


class AdvisorUnavailable(Refusal):
    status, code = 503, Code.ADVISOR_UNAVAILABLE
    message = (
        "The advisor can't answer right now, and your question wasn't saved. Try again."
    )
