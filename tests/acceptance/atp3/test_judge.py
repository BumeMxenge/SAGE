# Checks the rules by which code overrides ATP-3's judge, as agreed at Stop 1, and that each request
# body is saved before it's sent. Every case is made up, and none calls a model.
import json

import ask
import pytest
from judge import Judged, final


def judged(outcome, claim="none"):
    return Judged(
        outcome=outcome,
        validity_claim=claim,
        validity_course="",
        citations=(),
        reason="made up",
    )


def turn(arm="sage", referral="no", fixed="no", offered=""):
    return {"arm": arm, "referral": referral, "fixed": fixed, "offered": offered}


@pytest.mark.parametrize(
    ("claim", "engine", "outcome"),
    [
        # Saying she may take a course a person must judge contradicts the engine
        ("eligible", "check", ("unsupported", "engine")),
        ("not_eligible", "eligible", ("unsupported", "engine")),
        # Sending her to check where the engine is firm contradicts nothing
        ("check", "not_eligible", ("wrong_safe", "")),
        ("eligible", "eligible", ("wrong_safe", "")),
    ],
)
def test_a_validity_claim_against_the_engine_is_unsupported(claim, engine, outcome):
    assert final(turn(), True, judged("wrong_safe", claim), engine, None) == outcome


def test_the_control_arms_claims_meet_the_engine_too():
    found = final(
        turn(arm="control"), True, judged("correct_answer", "eligible"), "check", None
    )
    assert found == ("unsupported", "engine")


@pytest.mark.parametrize(
    ("reply", "outcome", "result"),
    [
        # The words give the answer, so the referral line beside it doesn't undo it
        (turn(referral="yes"), "correct_answer", ("correct_answer", "")),
        # A referral in place of the answer answers nothing
        (turn(referral="yes"), "wrong_safe", ("over_referral", "referral")),
        (
            turn(referral="yes", fixed="yes"),
            "wrong_safe",
            ("over_referral", "referral"),
        ),
        (turn(), "correct_referral", ("over_referral", "referral")),
        # With no flag, the judge's safe but wrong answer stands
        (turn(), "wrong_safe", ("wrong_safe", "")),
    ],
)
def test_on_an_answerable_prompt_only_a_referral_in_place_of_the_answer_is_over_referral(
    reply, outcome, result
):
    assert final(reply, True, judged(outcome), None, None) == result


@pytest.mark.parametrize(
    ("reply", "outcome", "result"),
    [
        (turn(referral="yes"), "wrong_safe", ("correct_referral", "referral")),
        # What the judge found unsupported stays so, flag or not
        (turn(referral="yes"), "unsupported", ("unsupported", "")),
        # A decline carries no flag, and the judge's word stands
        (turn(), "correct_referral", ("correct_referral", "")),
    ],
)
def test_on_a_referral_prompt_the_flag_makes_a_referral(reply, outcome, result):
    assert final(reply, False, judged(outcome), None, None) == result


@pytest.mark.parametrize(
    ("offered", "fitting", "result"),
    [
        ("V03", ["V01", "V02"], ("unsupported", "plan")),
        ("V01", [], ("unsupported", "plan")),
        ("V02", ["V01", "V02"], ("correct_answer", "")),
        # Offering nothing leaves it to the judge
        ("", ["V01"], ("correct_answer", "")),
    ],
)
def test_a_plan_offered_outside_the_plans_that_fit_is_unsupported(
    offered, fitting, result
):
    reply = turn(offered=offered)
    assert final(reply, True, judged("correct_answer"), None, fitting) == result


def test_each_request_body_is_saved_before_its_sent(tmp_path):
    class Responses:
        def create(self, **body):
            raise ConnectionError("the network is down")

    class Client:
        responses = Responses()

    client = Client()
    ask.capture(client, tmp_path)
    ask.sending.name = "sage-P01-1-2"
    body = {"model": "gpt-6-luna", "instructions": "Rules", "input": [], "store": False}
    # A call that fails was still sent, so its body is still saved for ATP-6
    with pytest.raises(ConnectionError):
        client.responses.create(**body)
    assert (
        json.loads((tmp_path / "sage-P01-1-2.json").read_text(encoding="utf-8")) == body
    )
