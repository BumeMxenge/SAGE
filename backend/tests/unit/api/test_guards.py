# Checks the guards every route shares, in one sweep over every route the app serves, so a new route
# that forgets one fails here without a test of its own. Each route gets one valid request naming
# Mbali's seeded plans and chats, because the questionnaire and ownership checks run inside the
# services, after the request is validated.
from collections.abc import Collection

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

from sage.shared.seed import load_seed
from sage.shared.students import StudentState
from tests.unit.api.accounts import MBALI

PUBLIC = {"GET /health"}
# Who she is, which tells the frontend where to send her, and setup itself
BEFORE_SETUP = {
    "GET /v1/me",
    "GET /v1/catalogue",
    "POST /v1/onboarding/transcript",
    "POST /v1/onboarding/complete",
}
# What another student gets for a request naming Mbali's plans or chats
NOT_HERS = {
    "GET /v1/plans/{plan_id}": (404, "plan_not_found"),
    "GET /v1/plans/compare": (404, "plan_not_found"),
    "GET /v1/chats": (200, []),  # none of hers are listed
    "POST /v1/chats": (404, "plan_not_found"),
    "GET /v1/chats/{chat_id}/messages": (404, "chat_not_found"),
    "POST /v1/chats/{chat_id}/messages": (404, "chat_not_found"),
}


@pytest.fixture
def her(seed_file) -> StudentState:
    # Her rows as seeded, for the ids the requests name
    return load_seed(seed_file, MBALI)


@pytest.fixture
def requests(her) -> dict[str, tuple[str, dict]]:
    # One valid request for every route: its address, and what else TestClient.request sends
    plan = {row.position: str(row.id) for row in her.plans}
    chat = next(str(row.id) for row in her.chats if row.other_plan_id is None)
    return {
        "GET /v1/me": ("/v1/me", {}),
        "GET /v1/catalogue": ("/v1/catalogue", {}),
        "POST /v1/onboarding/transcript": (
            "/v1/onboarding/transcript",
            {"content": b"%PDF-", "headers": {"Content-Type": "application/pdf"}},
        ),
        "POST /v1/onboarding/complete": ("/v1/onboarding/complete", {"json": {}}),
        "GET /v1/plans": ("/v1/plans", {}),
        "GET /v1/plans/compare": (
            "/v1/plans/compare",
            {"params": {"first": plan[1], "second": plan[7]}},
        ),
        "GET /v1/plans/{plan_id}": (f"/v1/plans/{plan[1]}", {}),
        "GET /v1/questionnaire": ("/v1/questionnaire", {}),
        "POST /v1/questionnaire": ("/v1/questionnaire", {"json": {}}),
        "GET /v1/electives": ("/v1/electives", {}),
        "PUT /v1/favourites/{course_code}": ("/v1/favourites/ECO1007S", {}),
        "DELETE /v1/favourites/{course_code}": ("/v1/favourites/ECO1007S", {}),
        "GET /v1/history": ("/v1/history", {}),
        "GET /v1/chats": ("/v1/chats", {"params": {"plan_id": plan[1]}}),
        "POST /v1/chats": ("/v1/chats", {"json": {"plan_id": plan[1]}}),
        "GET /v1/chats/{chat_id}/messages": (f"/v1/chats/{chat}/messages", {}),
        "POST /v1/chats/{chat_id}/messages": (
            f"/v1/chats/{chat}/messages",
            {"json": {"content": "Which plan has the lighter Fridays?"}},
        ),
    }


def send(
    client: TestClient, requests: dict, names: Collection[str]
) -> dict[str, Response]:
    responses = {}
    for name in names:
        path, extra = requests[name]
        responses[name] = client.request(name.split()[0], path, **extra)
    return responses


def outcome(response: Response) -> tuple[int, object]:
    # A refusal by its problem code, anything else by its body
    if response.is_error:
        return response.status_code, response.json()["code"]
    return response.status_code, response.json() if response.content else None


def outcomes(client: TestClient, requests: dict, names: Collection[str]) -> dict:
    return {
        name: outcome(response)
        for name, response in send(client, requests, names).items()
    }


def test_the_sweep_has_a_request_for_every_route(app: FastAPI, requests):
    # From the OpenAPI schema, which lists every operation the app serves
    routes = {
        f"{method.upper()} {path}"
        for path, operations in app.openapi()["paths"].items()
        for method in operations
    }
    assert routes == PUBLIC | requests.keys()


def test_every_route_needs_a_sign_in(app, requests):
    responses = send(TestClient(app), requests, requests)
    assert {name: outcome(r) for name, r in responses.items()} == dict.fromkeys(
        requests, (401, "not_signed_in")
    )
    # So the client knows to send a token
    assert {r.headers["www-authenticate"] for r in responses.values()} == {"Bearer"}


def test_every_route_needs_a_uct_account(signed_in, requests):
    assert outcomes(signed_in("outsider"), requests, requests) == dict.fromkeys(
        requests, (403, "uct_account_required")
    )


def test_staff_may_only_ask_who_they_are(signed_in, requests):
    # Their side isn't built, and /v1/me is how the frontend learns that
    names = requests.keys() - {"GET /v1/me"}
    assert outcomes(signed_in("staff"), requests, names) == dict.fromkeys(
        names, (403, "students_only")
    )


def test_every_route_after_setup_waits_for_it(signed_in, requests):
    names = requests.keys() - BEFORE_SETUP
    assert outcomes(signed_in("qrtilv"), requests, names) == dict.fromkeys(
        names, (409, "onboarding_incomplete")
    )


def test_every_chat_route_waits_for_the_questionnaire(unanswered, mbali, requests):
    names = {name for name in requests if name.split()[1].startswith("/v1/chats")}
    assert outcomes(mbali, requests, names) == dict.fromkeys(
        names, (409, "questionnaire_pending")
    )


def test_another_student_never_reaches_her_plans_or_chats(
    signed_in, stores, her, requests
):
    ids = {str(row.id) for row in (*her.plans, *her.chats)}
    naming_her = {
        name
        for name, request in requests.items()
        if any(found in str(request) for found in ids)
    }
    # A new route that names her data needs its answer here
    assert naming_her == NOT_HERS.keys()
    before = stores[1].get(MBALI)
    assert outcomes(signed_in("zvsorw"), requests, naming_her) == NOT_HERS
    assert stores[1].get(MBALI) == before
