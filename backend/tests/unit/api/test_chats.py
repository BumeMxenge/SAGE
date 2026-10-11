# Checks chats on Mbali's seeded set: they list under their plan or pair, a pair is stored the same
# whichever way round it was sent, a question gets the advisor stand-in's fixed reply, and chats
# refuse a bad question, another student's chat, a pending questionnaire and unfinished setup
from uuid import UUID, uuid4

import pytest

from sage.domain.students import Plan, PlanSet
from sage.services.stubs import FIXED_REPLY
from tests.unit.api.accounts import MBALI

QUESTION = {"content": "Which plan has the lighter Fridays?", "term": "sem1"}


@pytest.fixture
def mbali(signed_in):
    return signed_in("mbali")


@pytest.fixture
def plan_ids(mbali) -> dict[int, str]:
    # Her plan ids by position, as the planner learns them from the set
    return {
        plan["position"]: plan["id"] for plan in mbali.get("/v1/plans").json()["plans"]
    }


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
    assert [chat["title"] for chat in one] == ["Fridays on Power & Robotics"]
    assert [chat["title"] for chat in pair] == ["Process Control or Medical Imaging"]
    assert flipped == pair  # the pair reads the same whichever way round it's asked for


def test_every_chat_has_the_fields_its_row_needs(one_plan_chat, pair_chat):
    for chat in (one_plan_chat, pair_chat):
        assert set(chat) == {"id", "plan_id", "other_plan_id", "title", "created_at"}


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


def test_another_students_plan_cant_start_a_chat(signed_in, plan_ids):
    response = signed_in("zvsorw").post("/v1/chats", json={"plan_id": plan_ids[1]})
    assert (response.status_code, response.json()["code"]) == (404, "plan_not_found")


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


def test_her_one_plan_chat_reads_as_a_question_then_its_answer(mbali, one_plan_chat):
    messages = messages_in(mbali, one_plan_chat).json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "How busy are my Fridays on this plan?"
    for message in messages:
        assert (
            message["term"],
            message["referral"],
            message["open_plan_id"],
            message["citations"],
        ) == ("sem1", False, None, [])


def test_her_pair_chat_answer_offers_to_open_plan_7(mbali, pair_chat, plan_ids):
    messages = messages_in(mbali, pair_chat).json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "What's the difference between these two plans?"
    assert messages[1]["open_plan_id"] == plan_ids[7]


def test_every_message_has_the_fields_a_chat_shows(mbali, one_plan_chat, pair_chat):
    for chat in (one_plan_chat, pair_chat):
        for message in messages_in(mbali, chat).json():
            assert set(message) == {
                "id",
                "role",
                "content",
                "term",
                "created_at",
                "referral",
                "open_plan_id",
                "citations",
            }


def test_asking_in_a_pair_chat_stores_the_question_and_the_fixed_reply(
    mbali, pair_chat
):
    response = ask(mbali, pair_chat, QUESTION)
    assert response.status_code == 201
    exchange = response.json()
    assert set(exchange) == {"question", "reply"}
    question, reply = exchange["question"], exchange["reply"]
    assert (question["role"], question["content"]) == ("user", QUESTION["content"])
    assert (question["referral"], question["open_plan_id"]) == (False, None)
    assert (reply["role"], reply["content"]) == ("assistant", FIXED_REPLY)
    # Its Open plan action points at the chat's second plan
    assert (reply["referral"], reply["open_plan_id"], reply["citations"]) == (
        True,
        pair_chat["other_plan_id"],
        [],
    )
    stored = messages_in(mbali, pair_chat).json()
    assert len(stored) == 4
    assert stored[2:] == [question, reply]


def test_a_reply_in_a_one_plan_chat_has_no_plan_to_open(mbali, one_plan_chat):
    response = ask(mbali, one_plan_chat, QUESTION)
    assert response.status_code == 201
    reply = response.json()["reply"]
    assert (reply["referral"], reply["open_plan_id"]) == (True, None)


def test_an_empty_question_is_refused(mbali, one_plan_chat):
    response = ask(mbali, one_plan_chat, {"content": ""})
    assert (response.status_code, response.json()["code"]) == (422, "invalid_request")


def test_a_question_over_2000_characters_is_refused(mbali, one_plan_chat):
    response = ask(mbali, one_plan_chat, {"content": "a" * 2001})
    assert (response.status_code, response.json()["code"]) == (422, "invalid_request")


def test_a_question_of_exactly_2000_characters_is_accepted(mbali, one_plan_chat):
    response = ask(mbali, one_plan_chat, {"content": "a" * 2000})
    assert response.status_code == 201


def test_a_question_with_an_unknown_field_is_refused(mbali, one_plan_chat):
    response = ask(mbali, one_plan_chat, {"content": "Hi", "mood": "curious"})
    assert (response.status_code, response.json()["code"]) == (422, "invalid_request")


def test_another_students_chat_is_not_found(signed_in, one_plan_chat):
    other = signed_in("zvsorw")
    for response in (
        messages_in(other, one_plan_chat),
        ask(other, one_plan_chat, QUESTION),
    ):
        assert (response.status_code, response.json()["code"]) == (
            404,
            "chat_not_found",
        )


def test_chats_wait_for_the_questionnaire(mbali, stores, plan_ids, one_plan_chat):
    # Her seeded set as it was before she answered: nothing hidden and no answers. The fixtures
    # read the plan and chat ids first, while her chats were still open.
    students = stores[1]
    state = students.get(MBALI)
    students.replace(
        state.model_copy(
            update={
                "plan_sets": tuple(
                    row.model_copy(update={"answers": None}) for row in state.plan_sets
                ),
                "plans": tuple(
                    plan.model_copy(update={"hidden": False}) for plan in state.plans
                ),
            }
        )
    )
    for response in (
        chats_on(mbali, plan_ids[1]),
        mbali.post("/v1/chats", json={"plan_id": plan_ids[1]}),
        messages_in(mbali, one_plan_chat),
        ask(mbali, one_plan_chat, QUESTION),
    ):
        assert (response.status_code, response.json()["code"]) == (
            409,
            "questionnaire_pending",
        )


def test_staff_have_no_chats(signed_in):
    response = chats_on(signed_in("staff"), str(uuid4()))
    assert (response.status_code, response.json()["code"]) == (403, "students_only")


def test_chats_wait_for_onboarding(signed_in):
    response = chats_on(signed_in("qrtilv"), str(uuid4()))
    assert (response.status_code, response.json()["code"]) == (
        409,
        "onboarding_incomplete",
    )
