# Checks every error leaves the API as problem details: an unknown address or method, an invalid
# request, a refusal, and a crash, which hides its internals and carries a reference the log also has
import logging
import re
from typing import Annotated

import pytest
from fastapi import APIRouter, Query
from fastapi.testclient import TestClient

from sage.domain.errors import RouteNotFound
from sage.main import create_app

PROBLEM = "application/problem+json"


@pytest.fixture
def client() -> TestClient:
    # The real app with three extra routes that fail on purpose
    app = create_app()
    router = APIRouter()

    @router.get("/crash")
    def crash() -> None:
        raise RuntimeError("the database password is made-up-password")

    @router.get("/count")
    def count(number: Annotated[int, Query(ge=1)]) -> None:
        pass

    @router.get("/gone")
    def gone() -> None:
        raise RouteNotFound("That page went to a better place.")

    app.include_router(router)
    return TestClient(app)


def test_an_unknown_address_is_a_problem(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM
    assert response.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "There's nothing at this address.",
        "code": "not_found",
    }


def test_a_wrong_method_is_a_problem_that_names_the_right_one(client):
    response = client.post("/health")
    assert response.status_code == 405
    assert response.headers["allow"] == "GET"
    assert response.json()["code"] == "method_not_allowed"


def test_an_invalid_request_says_what_and_where(client):
    response = client.get("/count", params={"number": 0})
    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM
    problem = response.json()
    assert problem["code"] == "invalid_request"
    assert problem["errors"] == [
        {
            "location": "query",
            "field": "number",
            "detail": "Input should be greater than or equal to 1",
        }
    ]


def test_a_body_that_isnt_utf8_is_an_invalid_request(client):
    # FastAPI refuses it with a 400 of its own, before any sign-in check
    response = client.post(
        "/v1/chats", content=b"\xff", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM
    assert response.json()["code"] == "invalid_request"


def test_a_refusal_keeps_its_own_detail(client):
    response = client.get("/gone")
    assert response.status_code == 404
    assert response.json()["detail"] == "That page went to a better place."


def test_a_crash_hides_its_internals_and_logs_its_reference(client, caplog):
    with caplog.at_level(logging.ERROR):
        response = client.get("/crash", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 500
    assert response.headers["content-type"] == PROBLEM
    # Still readable by the frontend, so the student can see the reference
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    problem = response.json()
    assert problem["code"] == "internal_error"
    assert re.fullmatch(r"SG-[0-9A-F]{4}-[0-9A-F]{4}", problem["reference"])
    assert "password" not in response.text
    assert problem["reference"] in caplog.text
    # The traceback is in the log, never in the response
    assert "made-up-password" in caplog.text
