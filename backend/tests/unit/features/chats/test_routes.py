# Checks chats on Mbali's seeded set: they list under their plan or pair, a pair is stored the same
# whichever way round it was sent, a question and the advisor's reply are stored together, a bad
# question or pair is refused, a question the advisor can't answer in time stores nothing, and a
# chat is named once, from its first question. Who may reach a chat is in test_guards.py.
import logging
import threading
from uuid import UUID, uuid4

import pytest

from sage.advisor import replies
from sage.advisor.replies import GroundedAdvisor
from sage.engine.eligibility import EntryRuleEligibility
from sage.shared.api import deps
from sage.shared.language_model import ModelUnavailable, Response, Said
from sage.shared.memory.language_model import ScriptedModel
from sage.shared.rulebook import Rulebook
from sage.shared.students import Plan, PlanSet
from tests.unit.accounts import MBALI

QUESTION = {"content": "Which plan has the lighter Fridays?", "term": "sem1"}


def chats_on(client, plan_id: str, other_plan_id: str | None = None):
    # The chats listed for a plan, or for a pair when a second plan is given. A missing second plan
    # is left out of the query, as the client would send None as an empty value that isn't an id.
    params = {"plan_id": plan_id}
    if other_plan_id is not None:
        params["other_plan_id"] = other_plan_id
    return client.get("/v1/chats", params=params)


def messages_in(client, chat: dict):
    return client.get(f"/v1/chats/{chat['id']}/messages")


def ask(client, chat: dict, body: dict):
    return client.post(f"/v1/chats/{chat['id']}/messages", json=body)


@pytest.fixture
def one_plan_chat(mbali, plan_ids) -> dict:
    # Her seeded chat on plan 1 alone (c1 in the seed file), as the list shows it
    (chat,) = chats_on(mbali, plan_ids[1]).json()
    return chat


@pytest.fixture
def pair_chat(mbali, plan_ids) -> dict:
    # Her seeded chat on plans 1 and 7 (c2 in the seed file), as the list shows it
    (chat,) = chats_on(mbali, plan_ids[1], plan_ids[7]).json()
    return chat


def test_her_seeded_chats_list_under_their_plan_and_their_pair(mbali, plan_ids):
    one = chats_on(mbali, plan_ids[1]).json()
    pair = chats_on(mbali, plan_ids[1], plan_ids[7]).json()
    flipped = chats_on(mbali, plan_ids[7], plan_ids[1]).json()
    assert [chat["title"] for chat in one] == ["Fridays on Power, Control & Robotics"]
    assert [chat["title"] for chat in pair] == ["Process Control or Medical Imaging"]
    assert flipped == pair  # the pair reads the same whichever way round it's asked for


@pytest.mark.parametrize("first, second", [(1, 7), (7, 1)])
def test_a_pair_is_stored_lowest_id_first_whichever_way_round_it_is_sent(
    mbali, plan_ids, first, second
):
    # Both orders, as one of them always starts with the higher id and has to be swapped
    sent = {"plan_id": plan_ids[first], "other_plan_id": plan_ids[second]}
    response = mbali.post("/v1/chats", json=sent)
    assert response.status_code == 201
    chat = response.json()
    lowest, highest = sorted(sent.values(), key=UUID)
    assert (chat["plan_id"], chat["other_plan_id"]) == (lowest, highest)
    # Newest first, so it lists ahead of the seeded chat on the same pair
    listed = chats_on(mbali, plan_ids[1], plan_ids[7]).json()
    assert len(listed) == 2
    assert listed[0]["id"] == chat["id"]


def test_a_chat_on_one_plan_has_no_second_plan(mbali, plan_ids):
    response = mbali.post("/v1/chats", json={"plan_id": plan_ids[1]})
    assert response.status_code == 201
    chat = response.json()
    assert (chat["plan_id"], chat["other_plan_id"]) == (plan_ids[1], None)


def test_a_plan_cant_be_paired_with_itself(mbali, plan_ids):
    response = mbali.post(
        "/v1/chats", json={"plan_id": plan_ids[1], "other_plan_id": plan_ids[1]}
    )
    assert (response.status_code, response.json()["code"]) == (422, "same_plan")


def test_plans_from_different_sets_cant_share_a_chat(mbali, stores, plan_ids):
    # A newer set holding one plan. It becomes her current set, and is too short to need the
    # questionnaire, which would otherwise refuse first.
    students = stores[1]
    state = students.get(MBALI)
    newer = PlanSet(id=uuid4(), student_id=MBALI, period=2026, version=2, complete=True)
    plan = Plan(
        id=uuid4(), plan_set_id=newer.id, student_id=MBALI, position=1, name="Test"
    )
    students.replace(
        state.model_copy(
            update={
                "plan_sets": (*state.plan_sets, newer),
                "plans": (*state.plans, plan),
            }
        )
    )
    response = mbali.post(
        "/v1/chats", json={"plan_id": str(plan.id), "other_plan_id": plan_ids[1]}
    )
    assert (response.status_code, response.json()["code"]) == (
        422,
        "different_plan_sets",
    )


def test_a_question_and_the_advisors_reply_are_stored_together(
    advisor, mbali, pair_chat
):
    response = ask(mbali, pair_chat, QUESTION)
    assert response.status_code == 201
    question, reply = response.json()["question"], response.json()["reply"]
    # The advisor got her question, and the term on her screen
    ((chat, content, term),) = advisor.asked
    assert (str(chat.id), content, term) == (
        pair_chat["id"],
        QUESTION["content"],
        "sem1",
    )
    assert (question["role"], question["content"], question["term"]) == (
        "user",
        QUESTION["content"],
        "sem1",
    )
    assert (question["referral"], question["open_plan_id"], question["citations"]) == (
        False,
        None,
        [],
    )
    assert (reply["role"], reply["content"], reply["term"]) == (
        "assistant",
        "Made-up reply",
        "sem1",
    )
    assert (reply["referral"], reply["open_plan_id"]) == (True, pair_chat["plan_id"])
    assert reply["citations"] == [
        advisor.citation.model_dump(mode="json", exclude={"passage_id"})
    ]
    # Both are stored after her seeded exchange, in order
    assert messages_in(mbali, pair_chat).json()[2:] == [question, reply]


@pytest.mark.parametrize(
    ("body", "answer"),
    [
        ({"content": ""}, (422, "invalid_request")),
        ({"content": "a"}, (201, None)),
        ({"content": "a" * 2000}, (201, None)),
        ({"content": "a" * 2001}, (422, "invalid_request")),
        ({"content": "Hi", "mood": "curious"}, (422, "invalid_request")),
    ],
    ids=[
        "empty",
        "one character",
        "2,000 characters",
        "2,001 characters",
        "an unknown field",
    ],
)
def test_a_question_is_1_to_2000_characters_and_nothing_else(
    mbali, one_plan_chat, body, answer
):
    response = ask(mbali, one_plan_chat, body)
    assert (response.status_code, response.json().get("code")) == answer


@pytest.fixture
def luna(app, stores):
    # The real advisor in the app, on her stores, with a scripted model in Luna's place
    def scripted(model: ScriptedModel) -> None:
        advisor = GroundedAdvisor(
            model, stores[1], Rulebook(stores[0]), EntryRuleEligibility()
        )
        app.dependency_overrides[deps.advisor] = lambda: advisor

    return scripted


def test_a_provider_error_stores_nothing_and_reaches_her_as_advisor_unavailable(
    luna, mbali, one_plan_chat, caplog
):
    luna(ScriptedModel({"reply": [ModelUnavailable("InternalServerError")]}))
    before = messages_in(mbali, one_plan_chat).json()
    with caplog.at_level(logging.WARNING, logger="sage.advisor.replies"):
        response = ask(mbali, one_plan_chat, QUESTION)
    assert (response.status_code, response.json()["code"]) == (
        503,
        "advisor_unavailable",
    )
    assert messages_in(mbali, one_plan_chat).json() == before
    # The log names the chat and the error's kind, nothing more
    assert [record.getMessage() for record in caplog.records] == [
        f"Advisor unavailable in chat {one_plan_chat['id']}: InternalServerError"
    ]


def test_a_turn_that_runs_over_stores_nothing_even_once_its_reply_comes(
    luna, mbali, plan_ids, monkeypatch, caplog
):
    monkeypatch.setattr(replies, "TURN_LIMIT", 0.2)
    late = Response(
        text='{"content": "Late.", "referral": false, "open_plan_id": null, "citations": []}'
    )
    titled = Response(text='{"title": "Made-Up Title"}')
    model = ScriptedModel({"reply": [late], "title": [titled]}, held={"reply"})
    luna(model)
    # A new chat, so its title is asked for too, and answers in time though the reply doesn't
    chat = mbali.post("/v1/chats", json={"plan_id": plan_ids[1]}).json()
    with caplog.at_level(logging.WARNING, logger="sage.advisor.replies"):
        response = ask(mbali, chat, QUESTION)
    assert (response.status_code, response.json()["code"]) == (
        503,
        "advisor_unavailable",
    )
    assert [record.getMessage() for record in caplog.records] == [
        f"Advisor unavailable in chat {chat['id']}: the turn ran over 0.2 s"
    ]
    # The model answers after all, and the turn it was in runs to its end
    model.release()
    for thread in threading.enumerate():
        if thread.name.startswith("advisor"):
            thread.join(5)
    assert messages_in(mbali, chat).json() == []
    assert chats_on(mbali, plan_ids[1]).json()[0]["title"] is None


def test_a_chat_is_named_once_from_its_first_question(
    luna, mbali, plan_ids, inline, caplog
):
    answered = Response(
        text='{"content": "Made up.", "referral": false, "open_plan_id": null, "citations": []}'
    )
    # The title call fails, then gives one that fails the check, then a good one. A fourth would be
    # an error, as nothing more is scripted.
    model = ScriptedModel(
        {
            "reply": [answered] * 4,
            "title": [
                ModelUnavailable("RateLimitError"),
                Response(text='{"title": "Fridays."}'),
                Response(text='{"title": "Fridays This Semester"}'),
            ],
        }
    )
    luna(model)
    chat = mbali.post("/v1/chats", json={"plan_id": plan_ids[1]}).json()
    titles = []
    with caplog.at_level(logging.WARNING, logger="sage.advisor.replies"):
        for n in range(1, 5):
            response = ask(mbali, chat, {"content": f"Question {n}", "term": "sem1"})
            assert response.status_code == 201
            titles.append(chats_on(mbali, plan_ids[1]).json()[0]["title"])
    assert titles == [None, None, "Fridays This Semester", "Fridays This Semester"]
    assert [record.getMessage() for record in caplog.records] == [
        f"Advisor left chat {chat['id']} unnamed: RateLimitError",
        f"Advisor left chat {chat['id']} unnamed: its title failed the check",
    ]
    # Each title call named the chat from its first question
    asked = [call.conversation for call in model.calls if call.schema.name == "title"]
    assert asked == [(Said(role="user", text="Question 1"),)] * 3
