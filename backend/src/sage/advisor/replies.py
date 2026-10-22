# SAGE's advisor, filling shared/advisor.py. It answers a question in a chat about one plan or a
# pair through the language model, on the evidence SAGE chooses, with the engine's facts served as
# tools, and checks every reply before it's stored. Logs hold ids, kinds, marks, tokens and seconds,
# never a student's words.
import json
import logging
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from sage.advisor.checks import REFERRED, Answer, Checked, check
from sage.advisor.evidence import Evidence
from sage.shared.advisor import Reply
from sage.shared.errors import AdvisorUnavailable
from sage.shared.language_model import (
    LanguageModel,
    ModelUnavailable,
    Response,
    Said,
    Schema,
    Tokens,
    ToolResult,
    strict_object,
)
from sage.shared.planning import EligibilityChecker
from sage.shared.repositories import StudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.students import Chat

logger = logging.getLogger(__name__)

# Everything in prompt.md after its opening note for people, as E4's asking.py split it
PROMPT = (
    Path(__file__)
    .with_name("prompt.md")
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
# The reply Luna must give, in the shape of shared/advisor.py's Reply with short ids, as E4 asked
REPLY = Schema(
    name="reply",
    shape=strict_object(
        content={"type": "string"},
        referral={"type": "boolean"},
        open_plan_id={"type": ["string", "null"]},
        citations={
            "type": "array",
            "items": strict_object(
                passage_id={"type": "string"}, quote={"type": "string"}
            ),
        },
    ),
)
CALLS = 6  # a turn still calling tools after this many calls stops there, as in E4
EXCHANGES = 5  # the chat's latest exchanges that go before her new message
# Seconds a turn may take, so she always hears back inside the frontend's 60-second limit
TURN_LIMIT = 50


@dataclass(frozen=True)
class Called:
    # A tool Luna called, with what it asked for and what it got back
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass(frozen=True)
class Turn:
    # Luna's side of a turn: every reply it gave, every tool it called, and her message with its
    # details
    responses: tuple[Response, ...]
    called: tuple[Called, ...]
    asked: str


@dataclass(frozen=True)
class Answered:
    # A reply, with what went into it, which ask_advisor.py prints
    reply: Reply
    checked: Checked
    called: tuple[Called, ...]
    tokens: Tokens
    seconds: float


class GroundedAdvisor:
    def __init__(
        self,
        model: LanguageModel,
        students: StudentRepository,
        rulebook: Rulebook,
        checker: EligibilityChecker,
    ) -> None:
        self.model = model
        self.students = students
        self.rulebook = rulebook
        self.checker = checker

    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        return self.answer(chat, question, term).reply

    def answer(self, chat: Chat, question: str, term: str | None) -> Answered:
        started = time.monotonic()
        deadline = started + TURN_LIMIT
        evidence = Evidence(chat, term, self.students, self.rulebook, self.checker)
        earlier = [
            Said(role=row.message.role, text=row.message.content)
            for row in self.students.messages(chat.student_id, chat.id)
        ][-2 * EXCHANGES :]
        # The turn runs in a worker that only talks to the model, so the wait can end on time. A
        # turn that runs over is left behind, and as only this thread returns a reply, and only in
        # time, nothing it gives is ever stored.
        workers = ThreadPoolExecutor(max_workers=1, thread_name_prefix="advisor")
        turn = workers.submit(
            converse, self.model, evidence, earlier, question, deadline
        )
        workers.shutdown(wait=False)
        try:
            done = turn.result(timeout=max(deadline - time.monotonic(), 0))
        except ModelUnavailable as error:
            logger.warning("Advisor unavailable in chat %s: %s", chat.id, error)
            raise AdvisorUnavailable() from error
        except TimeoutError as error:
            logger.warning(
                "Advisor unavailable in chat %s: the turn ran over %s s",
                chat.id,
                TURN_LIMIT,
            )
            raise AdvisorUnavailable() from error
        checked = self._checked(chat, evidence, earlier, done)
        tokens = sum((response.tokens for response in done.responses), Tokens())
        seconds = time.monotonic() - started
        logger.info(
            "Advisor turn in chat %s: %s calls, %s tokens in (%s cached, %s written), "
            "%s out, %.1f s",
            chat.id,
            len(done.responses),
            tokens.fresh + tokens.cached + tokens.written,
            tokens.cached,
            tokens.written,
            tokens.output,
            seconds,
        )
        return Answered(checked.reply, checked, done.called, tokens, seconds)

    def _checked(
        self, chat: Chat, evidence: Evidence, earlier: Sequence[Said], done: Turn
    ) -> Checked:
        # Luna's last reply after the checks, with each check that bit logged. A turn that gave no
        # answer gets the fixed referral.
        answer = answer_in(done.responses[-1])
        if isinstance(answer, str):
            logger.warning("Advisor gave no answer in chat %s: %s", chat.id, answer)
            return Checked(REFERRED)
        # She may be offered a plan that turn's find_plan returned, or one the chat is on
        found = {
            plan["plan"]
            for called in done.called
            if called.name == "find_plan"
            for plan in called.result.get("plans", [])
        }
        heard = "\n".join(
            [
                *(said.text for said in earlier),
                done.asked,
                *(json.dumps(called.result) for called in done.called),
            ]
        )
        checked = check(answer, evidence, found | set(evidence.open), heard)
        for quote in checked.dropped:
            logger.warning(
                "Advisor dropped a quote in chat %s: it cites %s",
                chat.id,
                quote.passage_id,
            )
        if checked.unoffered:
            logger.warning(
                "Advisor dropped a plan offer in chat %s: %s",
                chat.id,
                checked.unoffered,
            )
        for flag in checked.flags:
            logger.warning(
                "Advisor flag in chat %s: %s %s", chat.id, flag.kind, flag.mark
            )
        return checked


def answer_in(last: Response) -> Answer | str:
    # Luna's answer in a turn's last reply, or why there's none
    if last.calls:
        return "still calling tools"
    if last.text is None:
        return "cut off"
    try:
        return Answer.model_validate_json(last.text)
    except ValidationError:
        return "not in the reply schema"


def converse(
    model: LanguageModel,
    evidence: Evidence,
    earlier: Sequence[Said],
    question: str,
    deadline: float,
) -> Turn:
    # Luna's calls until it replies, each running the tools it asks for, as E4 ran a turn: the
    # system prompt then the slice as instructions, and the chat's latest exchanges, their words
    # only, before her message. It stops once the turn is out of time, as no one waits for it then.
    instructions = f"{PROMPT}\n\n{evidence.slice_text()}"
    tools = evidence.tools()
    asked = f"{evidence.context()}\n\nQuestion\n{question}"
    conversation: list[Said | Response | ToolResult] = [
        *earlier,
        Said(role="user", text=asked),
    ]
    responses, called = [], []
    for number in range(CALLS):
        if time.monotonic() > deadline:
            raise TimeoutError
        response = model.respond(instructions, conversation, REPLY, tools)
        responses.append(response)
        if not response.calls or number == CALLS - 1:
            break
        results = []
        for call in response.calls:
            result = evidence.run(call.name, call.arguments)
            called.append(Called(call.name, call.arguments, result))
            results.append(ToolResult(call_id=call.id, output=result))
        conversation += [response, *results]
    return Turn(tuple(responses), tuple(called), asked)
