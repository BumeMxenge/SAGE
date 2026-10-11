# Every way SAGE turns a request down: one stable code each, which the frontend switches on, with its
# HTTP status and the sentence a student reads. Services, adapters and ingestion raise these, and the
# API sends them as problem details, so this module is the one list of codes.
from enum import StrEnum
from typing import ClassVar


class Code(StrEnum):
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    INVALID_REQUEST = "invalid_request"
    INTERNAL_ERROR = "internal_error"


class Refusal(Exception):
    status: ClassVar[int]
    code: ClassVar[Code]
    # The detail a raise gives when it has nothing more specific to say
    message: ClassVar[str]

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
