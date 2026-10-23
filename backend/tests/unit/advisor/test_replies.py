# Checks a turn of the advisor on Mbali's seed, with a scripted model in Luna's place: the request is
# the one E4 measured, a plan is offered only where it may be, a turn with no answer gets the fixed
# referral, the checks that bite and each turn's tokens are logged without a student's words, what
# the tools gave back counts as heard, the earlier exchanges go in, and a chat is named without
# holding its reply up. Every expected value
# comes from her seed, print, the script or E4's own evidence.py.
import json
import logging
import re
import threading
from uuid import uuid4

import pytest

from sage.advisor.checks import CODE, REFERRED, Flag
from sage.advisor.replies import PROMPT, GroundedAdvisor
from sage.engine.eligibility import EntryRuleEligibility
from sage.shared.advisor import Reply
from sage.shared.language_model import (
    Response,
    Said,
    Tokens,
    Tool,
    ToolCall,
    ToolResult,
)
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


def short_id(evidence, section: str) -> str:
    return next(
        key
        for key, passage in evidence().passages.items()
        if passage.section == section
    )


@pytest.mark.parametrize(
    ("chosen", "own"),
    [
        ((1,), None),
        (
            (3, 7),
            "In semester 1 this plan has one class on Thursdays: CML4607F at 12:00.",
        ),
    ],
    ids=["one plan", "a pair"],
)
def test_her_request_is_the_one_e4_measured(advisor, chat_on, e4, chosen, own):
    # E4's evidence.py built every request E4 measured, so it is the oracle for Mbali's: the slice,
    # the tools and the details in her message. Only the prompt's listed changes differ, and the
    # message's order, as the stores give her courses in code order and her reasons by id.
    asked, model = advisor(answers("Made up."))
    asked.reply(chat_on(*chosen), "Made up?", "sem1")
    (call,) = model.calls
    assert call.instructions == f"{PROMPT}\n\n{e4.slice_text()}"
    assert call.tools == tuple(
        Tool(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["schema"],
        )
        for tool in e4.TOOLS
    )
    message = call.conversation[-1].text
    expected = e4.context([f"V{n:02d}" for n in chosen], "sem1")
    assert sorted(message.splitlines()) == sorted(
        f"{expected}\n\nQuestion\nMade up?".splitlines()
    )
    # The set's own reasons come first, then the open plans', such as V07's
    if own:
        reasons = message.split("Reasons behind the plan set\n")[1]
        assert reasons.split("\n\nQuestion")[0].splitlines()[-1] == f"- {own}"


@pytest.mark.parametrize(
    ("offered", "kept"),
    [("V03", 3), ("V05", None), ("V01", 1)],
    ids=["a hidden plan find_plan returned", "a plan it didn't", "the chat's own plan"],
)
def test_a_plan_is_offered_only_if_find_plan_returned_it_or_the_chat_is_on_it(
    advisor, chat_on, positions, offered, kept
):
    # On her seed, find_plan for EEE4118F without EEE4119F returns V02 to V04, all hidden
    finding = asks("find_plan", have=["EEE4118F"], avoid=["EEE4119F"])
    asked, model = advisor(finding, answers("Made up.", open_plan_id=offered))
    answered = asked.answer(chat_on(1), "Made up?", "sem1")
    # The rest of the reply stands either way, and only a plan it drops counts as dropped
    assert answered.reply == Reply(
        content="Made up.",
        referral=False,
        open_plan_id=positions[kept] if kept else None,
    )
    assert answered.checked.unoffered == (None if kept else offered)
    # The call ran as Luna asked it, and its result went back after her message and Luna's call
    (called,) = answered.turn.called
    assert (called.name, called.arguments) == (
        "find_plan",
        {"have": ["EEE4118F"], "avoid": ["EEE4119F"]},
    )
    first, second = model.calls
    assert second.conversation == (
        *first.conversation,
        finding,
        ToolResult(call_id=finding.calls[0].id, output=called.result),
    )


@pytest.mark.parametrize(("calling", "referred"), [(5, False), (6, True)])
def test_a_turn_still_calling_tools_after_six_calls_gets_the_fixed_referral(
    advisor, chat_on, calling, referred
):
    # Five calls of tools then an answer make six calls, so the answer stands. A sixth call of tools
    # is the last call, so the turn ends with no answer, and its tools never run.
    asked, model = advisor(
        *[asks("get_course", code="EEE4113F")] * calling, answers("Made up.")
    )
    answered = asked.answer(chat_on(1), "Made up?", "sem1")
    assert answered.reply == (
        REFERRED if referred else Reply(content="Made up.", referral=False)
    )
    assert (len(model.calls), len(answered.turn.called)) == (6, 5)


@pytest.mark.parametrize(
    ("last", "why"),
    [
        (asks("get_course", code="EEE4113F"), "still calling tools"),
        (Response(text=None), "cut off"),
        (Response(text='{"content": "Made up."}'), "not in the reply schema"),
    ],
    ids=["still calling tools", "cut off", "not in the schema"],
)
def test_a_turn_with_no_answer_gets_the_fixed_referral_and_says_why(
    advisor, chat_on, caplog, last, why
):
    script = [last] * 6 if last.calls else [last]
    asked, _ = advisor(*script)
    chat = chat_on(1)
    with caplog.at_level(logging.WARNING, logger="sage.advisor.replies"):
        assert asked.reply(chat, "Made up?", "sem1") == REFERRED
    assert [record.getMessage() for record in caplog.records] == [
        f"Advisor gave no answer in chat {chat.id}: {why}"
    ]


def test_checks_that_bite_are_logged_without_her_words_and_flags_change_nothing(
    advisor, chat_on, evidence, caplog
):
    # Her slice prints EEE4022S's entry as "is not eligible for additional" then "assessment"
    # (2026, page 138), and FB9.1 as "The degree may only be" (page 21). The reply keeps both
    # quotes, but drops the first's "not", keeps the second's "only" as "Only", and gives 99, 07:15
    # and XYZ9999F, which no evidence holds. It also cites a passage outside her slice, and offers
    # V05, which no find_plan returned and the chat isn't on.
    entry = short_id(evidence, "EEE4022S Research Project")
    rule = short_id(evidence, "FB9.1")
    content = (
        "Only 99 points at 07:15 with XYZ9999F, and EEE4022S is eligible for additional "
        "assessment."
    )
    question = "Zebra question about my projects?"
    asked, _ = advisor(
        answers(
            content,
            open_plan_id="V05",
            citations=[
                (entry, "not eligible for additional assessment"),
                (rule, "The degree may only be"),
                ("P99", "Zebra lemon marmalade"),
            ],
        )
    )
    chat = chat_on(1)
    with caplog.at_level(logging.INFO, logger="sage.advisor.replies"):
        answered = asked.answer(chat, question, "sem1")
    # The flags change nothing: the words stand, with the two quotes kept and the plan dropped
    reply = answered.reply
    assert (reply.content, reply.referral, reply.open_plan_id) == (content, False, None)
    assert [cited.quote for cited in reply.citations] == [
        "not eligible for additional assessment",
        "The degree may only be",
    ]
    assert answered.checked.flags == (
        Flag(kind="unsupported_mark", mark="07:15"),
        Flag(kind="unsupported_mark", mark="99"),
        Flag(kind="unsupported_mark", mark="XYZ9999F"),
        Flag(kind="dropped_condition", mark="not"),
    )
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [
        f"Advisor dropped a quote in chat {chat.id}: it cites P99",
        f"Advisor dropped a plan offer in chat {chat.id}: V05",
        f"Advisor flag in chat {chat.id}: unsupported_mark 07:15",
        f"Advisor flag in chat {chat.id}: unsupported_mark 99",
        f"Advisor flag in chat {chat.id}: unsupported_mark XYZ9999F",
        f"Advisor flag in chat {chat.id}: dropped_condition not",
    ]
    # Not one word of hers, of the reply's or of the dropped quote in any line, course codes set
    # aside as marks
    said = f"{question} {content} Zebra lemon marmalade"
    words = set(re.findall(r"[a-z]{3,}", CODE.sub(" ", said).lower()))
    logged = " ".join(record.getMessage() for record in caplog.records).lower()
    assert [word for word in words if word in logged] == []


def test_what_the_tools_gave_back_counts_as_heard_even_an_error(advisor, chat_on):
    # find_plan asked for no course gives back an error and no plans. check_eligibility says she has
    # passed EEE3096S Embedded Systems II, as her record shows for 2025. The reply names EEE3096S,
    # which only that result holds, so it stands with no flag.
    content = "You've already passed EEE3096S."
    asked, model = advisor(
        asks("find_plan", have=[], avoid=[]),
        asks("check_eligibility", code="EEE3096S"),
        answers(content),
    )
    answered = asked.answer(chat_on(1), "Made up?", "sem1")
    assert "EEE3096S" not in model.calls[0].conversation[-1].text
    assert answered.reply == Reply(content=content, referral=False)
    assert answered.checked.flags == ()


def test_each_turn_logs_its_calls_tokens_and_seconds(advisor, chat_on, caplog):
    # Luna asks check_eligibility, which the engine's checker answers from her record, then answers
    checking = Response(
        calls=(
            ToolCall(
                id="call_1", name="check_eligibility", arguments={"code": "EEE3096S"}
            ),
        ),
        tokens=Tokens(fresh=14_000, written=400, output=30),
    )
    answering = Response(
        text=answers("Made up.").text,
        tokens=Tokens(fresh=100, cached=14_300, written=20, output=60),
    )
    asked, _ = advisor(checking, answering)
    chat = chat_on(1)
    with caplog.at_level(logging.INFO, logger="sage.advisor.replies"):
        answered = asked.answer(chat, "Made up?", "sem1")
    # Her record shows EEE3096S Embedded Systems II passed in 2025 with 80%
    assert answered.turn.called[0].result == {
        "status": "not_eligible",
        "reason": "You've already passed EEE3096S.",
    }
    # In: 14,000 + 400 on the first call and 100 + 14,300 + 20 on the second, 28,820 in all, with
    # 14,300 read from the cache and 420 written to it. Out: 30 + 60 = 90.
    (line,) = [record.getMessage() for record in caplog.records]
    assert line.startswith(
        f"Advisor turn in chat {chat.id}: 2 calls, 28820 tokens in (14300 cached, "
        "420 written), 90 out, "
    )
    assert line.endswith(f" {answered.seconds:.1f} s") and answered.seconds < 10


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


def test_a_new_chat_is_named_at_low_effort_from_one_strict_field(
    advisor, chat_on, inline
):
    titled = Response(text='{"title": "Made-Up Title"}')
    asked, model = advisor(answers("Made up."), titles=(titled,))
    answered = asked.answer(chat_on(1, title=None), "Made up?", "sem1")
    assert (answered.reply.title, answered.named) == ("Made-Up Title", titled)
    (call,) = [call for call in model.calls if call.schema.name == "title"]
    assert (call.conversation, call.tools, call.effort) == (
        (Said(role="user", text="Made up?"),),
        (),
        "low",
    )
    assert call.schema.shape == {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "additionalProperties": False,
    }
    assert "2 to 6 words" in call.instructions


def test_the_reply_never_waits_for_its_title(advisor, chat_on, caplog):
    titled = Response(text='{"title": "Made-Up Title"}')
    asked, model = advisor(answers("Made up."), titles=(titled,), held={"title"})
    chat = chat_on(1, title=None)
    with caplog.at_level(logging.INFO, logger="sage.advisor.replies"):
        reply = asked.reply(chat, "Made up?", "sem1")
    # The title came too late for this reply, so the chat stays unnamed until its next exchange
    assert (reply.content, reply.title) == ("Made up.", None)
    assert f"Advisor left chat {chat.id} unnamed: its title wasn't ready" in [
        record.getMessage() for record in caplog.records
    ]
    model.release()
    for thread in threading.enumerate():
        if thread.name.startswith("advisor"):
            thread.join(5)
