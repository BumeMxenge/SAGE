# Every error leaves the API as RFC 9457 problem details, sent as application/problem+json with the
# stable code the frontend switches on. Refusals, invalid requests, unknown addresses and crashes all
# come out in that one shape, and the OpenAPI schema says so.
import logging
import secrets
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from sage.domain.errors import (
    Code,
    InternalError,
    InvalidRequest,
    MethodNotAllowed,
    Refusal,
    RouteNotFound,
)

MEDIA_TYPE = "application/problem+json"
logger = logging.getLogger(__name__)


class FieldError(BaseModel):
    location: Literal["body", "query", "path", "header", "cookie"]
    field: str  # where inside it, such as lines.3.course_code
    detail: str


class Problem(BaseModel):
    # about:blank is RFC 9457's type for a problem with no page of its own. Its title is then the
    # status phrase, and code tells problems apart.
    type: Literal["about:blank"] = "about:blank"
    title: str
    status: int
    detail: str
    code: Code
    errors: list[FieldError] | None = None  # invalid_request only
    # internal_error only; the server log has the same reference
    reference: str | None = None


def problem(
    refusal: Refusal, headers: Mapping[str, str] | None = None, **members: Any
) -> JSONResponse:
    body = Problem(
        title=HTTPStatus(refusal.status).phrase,
        status=refusal.status,
        detail=refusal.detail,
        code=refusal.code,
        **refusal.extra,
        **members,
    )
    return JSONResponse(
        body.model_dump(mode="json", exclude_none=True),
        status_code=refusal.status,
        headers=headers,
        media_type=MEDIA_TYPE,
    )


def errors(*refusals: type[Refusal]) -> dict[int | str, dict[str, Any]]:
    # A route's declared error responses: one per status, naming every code it can send
    codes: dict[int, list[str]] = {}
    for refusal in refusals:
        codes.setdefault(refusal.status, []).append(refusal.code)
    return {
        status: {"model": Problem, "description": ", ".join(names)}
        for status, names in codes.items()
    }


async def refused(request: Request, refusal: Refusal) -> JSONResponse:
    return problem(refusal)


async def invalid(request: Request, error: RequestValidationError) -> JSONResponse:
    errors = [
        FieldError(
            location=item["loc"][0],
            field=".".join(str(part) for part in item["loc"][1:]),
            detail=item["msg"],
        )
        for item in error.errors()
    ]
    return problem(InvalidRequest(), errors=errors)


async def not_routed(request: Request, error: HTTPException) -> JSONResponse:
    # Starlette's routing raises these for an unknown address or a method the address doesn't take
    refusal = {404: RouteNotFound, 405: MethodNotAllowed}[error.status_code]()
    return problem(refusal, headers=error.headers)


class CrashesAsProblems:
    # Turns an unhandled error into a 500 problem and logs the same reference with the traceback. It
    # sits inside CORS, unlike FastAPI's handler for Exception, so the browser can read the reference.
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception:
            if scope["type"] != "http":
                raise
            reference = f"SG-{secrets.token_hex(2)}-{secrets.token_hex(2)}".upper()
            logger.exception("Unhandled error, reference %s", reference)
            await problem(InternalError(), reference=reference)(scope, receive, send)


def install(app: FastAPI) -> None:
    # Called before CORS is added, so CORS wraps the crash middleware
    app.add_exception_handler(Refusal, refused)
    app.add_exception_handler(RequestValidationError, invalid)
    app.add_exception_handler(HTTPException, not_routed)
    app.add_middleware(CrashesAsProblems)

    build = app.openapi

    def openapi() -> dict[str, Any]:
        # FastAPI files every declared response under application/json, but errors go out as
        # application/problem+json, so the schema says that instead
        if app.openapi_schema is None:
            for path in build()["paths"].values():
                for operation in path.values():
                    for status, response in operation["responses"].items():
                        if int(status) >= 400:
                            schema = response["content"].pop("application/json")
                            response["content"][MEDIA_TYPE] = schema
        return app.openapi_schema

    app.openapi = openapi
