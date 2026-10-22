# Checks chats on Mbali's seeded set: they list under their plan or pair, a pair is stored the same
# whichever way round it was sent, a question and the advisor's reply are stored together, and a bad
# question or pair is refused. Who may reach a chat is in test_guards.py.
from uuid import UUID, uuid4

import pytest

from sage.shared.advisor import Reply
from sage.shared.api import deps
from sage.shared.students import Chat, Citation, Plan, PlanSet
from tests.unit.accounts import MBALI

QUESTION = {"content": "Which plan has the lighter Fridays?", "term": "sem1"}
CITATION = Citation(
    passage_id=UUID(int=9),
    position=1,
    quote="Made-up quote",
    source="Made-up handbook",
    section="Test",
    page=7,
)


class Advisor:
    # Stands in for the advisor: records what it's asked, and replies with a referral, a plan to
    # open and a citation, so a test can see each one reach her
    def __init__(self) -> None:
        self.asked: list[tuple[Chat, str, str | None]] = []

    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        self.asked.append((chat, question, term))
        return Reply(
            content="Made-up reply",
            referral=True,
            open_plan_id=chat.plan_id,
            citations=(CITATION,),
        )


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


def test_a_question_and_the_advisors_reply_are_stored_together(app, mbali, pair_chat):
    advisor = Advisor()
    app.dependency_overrides[deps.advisor] = lambda: advisor
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
        CITATION.model_dump(mode="json", exclude={"passage_id"})
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
