# Every way SAGE turns a request down: one stable code each, which the frontend switches on, with its
# HTTP status and the sentence a student reads. Services, adapters and ingestion raise these, and the
# API sends them as problem details, so this module is the one list of codes.
from collections.abc import Mapping
from enum import StrEnum
from typing import ClassVar


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
