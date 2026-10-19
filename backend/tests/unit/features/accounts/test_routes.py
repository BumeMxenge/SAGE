# Checks what /v1/me answers, which the frontend routes from. Who may ask is in test_guards.py.


def test_mbali_is_a_student_who_has_finished_setup(signed_in, fake_account):
    assert signed_in("mbali").get("/v1/me").json() == {
        "email": fake_account["email"],
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
