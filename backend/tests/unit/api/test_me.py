# Checks /v1/me: only a valid token from a UCT account gets an answer, and the answer is what the
# frontend routes from
from fastapi.testclient import TestClient


def test_no_token_is_not_signed_in(app):
    response = TestClient(app).get("/v1/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "not_signed_in"


def test_a_bad_token_is_not_signed_in(signed_in):
    response = signed_in("made-up-token").get("/v1/me")
    assert response.status_code == 401
    assert response.json()["code"] == "not_signed_in"


def test_an_account_outside_uct_is_refused(signed_in):
    response = signed_in("outsider").get("/v1/me")
    assert response.status_code == 403
    assert response.json()["code"] == "uct_account_required"


def test_mbali_is_a_student_who_has_finished_setup(signed_in, fake_account):
    assert signed_in("mbali").get("/v1/me").json() == {
        "email": fake_account["email"],
        "name": fake_account["name"],
        "account": "student",
        "student_number": "DLMMBA999",
        "onboarding_complete": True,
    }


def test_a_new_student_hasnt_finished_setup(signed_in):
    me = signed_in("qrtilv").get("/v1/me").json()
    assert me["student_number"] == "QRTILV999"
    assert me["onboarding_complete"] is False


def test_staff_get_an_answer_with_no_student_number(signed_in):
    me = signed_in("staff").get("/v1/me").json()
    assert me["account"] == "staff"
    assert me["student_number"] is None
    assert me["onboarding_complete"] is False
