# Checks a turn of the advisor on Mbali's seed, with a scripted model in Luna's place: the plan it
# may offer, the six-call limit, the flags it logs without a student's words, and the earlier
# exchanges it sends. Every expected value comes from her seed or the script.
import json
import logging
import re
import threading
from uuid import uuid4

import pytest

from sage.advisor.checks import CODE, REFERRED
from sage.advisor.replies import GroundedAdvisor
from sage.engine.eligibility import EntryRuleEligibility
from sage.shared.advisor import Reply
from sage.shared.language_model import Response, Said, ToolCall
from sage.shared.memory.language_model import ScriptedModel
from sage.shared.rulebook import Rulebook
from sage.shared.students import Message
from tests.unit.accounts import MBALI


def asks(name: str, **arguments) -> Response:
    # Luna asking for one tool
    return Response(
        calls=(ToolCall(id=f"call_{uuid4()}", name=name, arguments=arguments),)
    )


def answers(content: str, open_plan_id: str | None = None, citations=()) -> Response:
    # Luna's answer, in the reply schema
    answer = {
        "content": content,
        "referral": False,
        "open_plan_id": open_plan_id,
        "citations": [
            {"passage_id": passage, "quote": quote} for passage, quote in citations
        ],
    }
    return Response(text=json.dumps(answer))


@pytest.fixture
def advisor(stores):
    rules, students = stores

    def build(
        *replies: Response, titles: tuple[Response, ...] = (), held=()
    ) -> tuple[GroundedAdvisor, ScriptedModel]:
        model = ScriptedModel({"reply": replies, "title": titles}, held=held)
        return GroundedAdvisor(
            model, students, Rulebook(rules), EntryRuleEligibility()
        ), model

    return build


@pytest.fixture
def positions(stores) -> dict[int, object]:
    return {plan.position: plan.id for plan in stores[1].get(MBALI).plans}


@pytest.mark.parametrize(
    ("offered", "kept"),
    [("V03", 3), ("V05", None), ("V01", 1)],
    ids=["a hidden plan find_plan returned", "a plan it didn't", "the chat's own plan"],
)
def test_a_plan_is_offered_only_if_find_plan_returned_it_or_the_chat_is_on_it(
    advisor, chat_on, positions, offered, kept
):
    # On her seed, find_plan for EEE4118F without EEE4119F returns V02 to V04, all hidden
    asked, _ = advisor(
        asks("find_plan", have=["EEE4118F"], avoid=["EEE4119F"]),
        answers("Made up.", open_plan_id=offered),
    )
    reply = asked.reply(chat_on(1), "Made up?", "sem1")
    # The rest of the reply stands either way
    assert reply == Reply(
        content="Made up.",
        referral=False,
        open_plan_id=positions[kept] if kept else None,
    )


@pytest.mark.parametrize(("calling", "referred"), [(5, False), (6, True)])
def test_a_turn_still_calling_tools_after_six_calls_gets_the_fixed_referral(
    advisor, chat_on, calling, referred
):
    # Five calls of tools then an answer make six calls, so the answer stands. A sixth call of tools
    # is the last call, so the turn ends with no answer.
    asked, model = advisor(
        *[asks("get_course", code="EEE4113F")] * calling, answers("Made up.")
    )
    reply = asked.reply(chat_on(1), "Made up?", "sem1")
    assert reply == (
        REFERRED if referred else Reply(content="Made up.", referral=False)
    )
    assert len(model.calls) == 6


def test_flags_are_logged_without_her_words_and_the_reply_goes_out_unchanged(
    advisor, chat_on, evidence, caplog
):
    # Her slice prints EEE4022S's entry as "is not eligible for additional" then "assessment"
    # (2026, page 138). The reply keeps that quote but drops its "not", and gives 99, which no
    # evidence holds, as her context, a new chat and the quote hold no 99.
    entry = next(
        key
        for key, passage in evidence().passages.items()
        if passage.section == "EEE4022S Research Project"
    )
    content = "Yes: 99 points, and EEE4022S is eligible for additional assessment."
    question = "Zebra question about my projects?"
    asked, _ = advisor(
        answers(content, citations=[(entry, "not eligible for additional assessment")])
    )
    chat = chat_on(1)
    with caplog.at_level(logging.INFO, logger="sage.advisor.replies"):
        reply = asked.reply(chat, question, "sem1")
    assert (reply.content, reply.referral, len(reply.citations)) == (content, False, 1)
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [
        f"Advisor flag in chat {chat.id}: unsupported_mark 99",
        f"Advisor flag in chat {chat.id}: dropped_condition not",
    ]
    # Not one of her words, or the reply's, in any line, course codes set aside as marks
    words = set(
        re.findall(r"[a-z]{3,}", CODE.sub(" ", f"{question} {content}").lower())
    )
    logged = " ".join(record.getMessage() for record in caplog.records).lower()
    assert [word for word in words if word in logged] == []


def test_only_the_last_five_exchanges_go_in_oldest_first_and_only_their_words(
    advisor, chat_on, stores
):
    chat = chat_on(1)
    for n in range(1, 7):
        question = Message(
            id=uuid4(),
            chat_id=chat.id,
            student_id=MBALI,
            role="user",
            content=f"Question {n}",
            term="sem1",
        )
        reply = question.model_copy(
            update={
                "id": uuid4(),
                "role": "assistant",
                "content": f"Reply {n}",
                "referral": True,
            }
        )
        stores[1].add_exchange(question, reply, [])
    asked, model = advisor(answers("Made up."))
    asked.reply(chat, "Seventh?", "sem1")
    *earlier, latest = model.calls[0].conversation
    assert earlier == [
        Said(role=role, text=f"{word} {n}")
        for n in range(2, 7)
        for role, word in (("user", "Question"), ("assistant", "Reply"))
    ]
    assert latest.text.startswith("About the student\n")
    assert latest.text.endswith("\n\nQuestion\nSeventh?")


def test_the_reply_never_waits_for_its_title(advisor, chat_on):
    titled = Response(text='{"title": "Made-Up Title"}')
    asked, model = advisor(answers("Made up."), titles=(titled,), held={"title"})
    reply = asked.reply(chat_on(1, title=None), "Made up?", "sem1")
    # The title came too late for this reply, so the chat stays unnamed until its next exchange
    assert (reply.content, reply.title) == ("Made up.", None)
    model.release()
    for thread in threading.enumerate():
        if thread.name.startswith("advisor"):
            thread.join(5)
