# Checks Luna is asked exactly as E4's asking.py asked it, with OpenAI storing nothing, that its
# replies are read rightly, and that only the errors the SDK retries mean it can't be reached. A fake
# transport answers in OpenAI's place with Luna's own replies from E4, so no test calls a model.
import json
from functools import partial
from pathlib import Path

import httpx2
import pytest
from openai import AuthenticationError, BadRequestError, OpenAI

from sage.shared import openai as adapter
from sage.shared.language_model import (
    ModelUnavailable,
    Said,
    Schema,
    Tokens,
    Tool,
    ToolCall,
    ToolResult,
)
from sage.shared.openai import OpenAIModel

# Three of Luna's replies in E4, copied unchanged from experiments/advisor/results/replies/gpt-6-luna/:
# the two calls of B-not-eligible-5-1, a check_eligibility call and then its answer, and the second
# call of B-plan-action-1-4, which asks for two tools at once
LUNA = Path(__file__).resolve().parents[2] / "fixtures" / "luna"
CODE = {
    "type": "object",
    "properties": {"code": {"type": "string"}},
    "required": ["code"],
    "additionalProperties": False,
}
CHECK = Tool(name="check_eligibility", description="Made up.", parameters=CODE)
ANSWER = Schema(name="reply", shape=CODE)
ASKED = Said(role="user", text="Can I take EEE4121F?")


def recorded(name: str) -> dict:
    return json.loads((LUNA / name).read_text(encoding="utf-8"))


@pytest.fixture
def served(monkeypatch):
    # The client sends through a fake transport, which keeps each request's body and answers with
    # the next answer given: one of Luna's replies by file name, an HTTP status, or a failure to
    # connect. With no retries, an error comes back at once.
    def serve(*answers):
        bodies, queue = [], iter(answers)

        def reply(request):
            bodies.append(json.loads(request.content))
            answer = next(queue)
            if isinstance(answer, Exception):
                raise answer
            if isinstance(answer, int):
                error = {"message": "Made up.", "type": "made_up", "code": None}
                return httpx2.Response(answer, json={"error": error})
            return httpx2.Response(200, json=recorded(answer))

        client = httpx2.Client(transport=httpx2.MockTransport(reply))
        monkeypatch.setattr(
            adapter, "OpenAI", partial(OpenAI, http_client=client, max_retries=0)
        )
        return bodies

    return serve


def test_a_turn_is_asked_as_e4_asked_and_read_from_lunas_replies(served):
    bodies = served("tool-call.json", "answer.json")
    model = OpenAIModel("made-up-key", "gpt-6-luna")
    first = model.respond("Made-up instructions", [ASKED], ANSWER, [CHECK])
    # The call its first reply prints, and no text while it calls a tool
    asked_for = ToolCall(
        id="call_ekT5aYs4uuPwVI3eZqGTMMol",
        name="check_eligibility",
        arguments={"code": "EEE4121F"},
    )
    assert (first.calls, first.text) == ((asked_for,), None)
    result = ToolResult(call_id=asked_for.id, output={"status": "not_eligible"})
    second = model.respond(
        "Made-up instructions", [ASKED, first, result], ANSWER, [CHECK]
    )
    # The answer its second reply prints, and its tokens: 14,419 in, of which 14,331 were read from
    # the cache and 85 written to it, so 3 fresh, and 52 out
    assert second.calls == ()
    assert second.text == (
        '{"content":"No. You’re not eligible for EEE4121F because it requires EEE3093S, '
        'which you haven’t passed.","referral":false,"open_plan_id":null,"citations":[]}'
    )
    assert second.tokens == Tokens(fresh=3, cached=14_331, written=85, output=52)
    # E4's request, with OpenAI told to store nothing, and no sampling or reasoning setting
    assert bodies[0] == {
        "model": "gpt-6-luna",
        "instructions": "Made-up instructions",
        "store": False,
        "tools": [
            {
                "type": "function",
                "name": "check_eligibility",
                "description": "Made up.",
                "parameters": CODE,
                "strict": True,
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "reply",
                "schema": CODE,
                "strict": True,
            }
        },
        "input": [{"role": "user", "content": "Can I take EEE4121F?"}],
    }
    # The second call passes the first reply's output back as it came, its reasoning item and its
    # encrypted reasoning included, less the empty fields the SDK fills in, then the tool's result
    reasoning, call = recorded("tool-call.json")["output"]
    assert reasoning["type"] == "reasoning" and reasoning["encrypted_content"]
    assert bodies[1]["input"] == [
        {"role": "user", "content": "Can I take EEE4121F?"},
        *(
            {key: value for key, value in item.items() if value is not None}
            for item in (reasoning, call)
        ),
        {
            "type": "function_call_output",
            "call_id": "call_ekT5aYs4uuPwVI3eZqGTMMol",
            "output": '{"status": "not_eligible"}',
        },
    ]


def test_every_tool_a_reply_asks_for_is_read(served):
    served("two-tool-calls.json")
    response = OpenAIModel("made-up-key", "gpt-6-luna").respond("Made up.", [ASKED])
    # Both calls B-plan-action-1-4's second reply prints, in its order
    assert response.calls == (
        ToolCall(
            id="call_N9oYDJ3ep7mUhJ3S4efE0LOG",
            name="find_plan",
            arguments={
                "have": [
                    "EEE4118F",
                    "EEE4117F",
                    "EEE4119F",
                    "EEE4113F",
                    "CML4607F",
                    "EEE4124C",
                    "EEE4125C",
                    "EEE4022S",
                ],
                "avoid": ["EEE4120F"],
            },
        ),
        ToolCall(
            id="call_5HDakJfdIodJ8tqiSjz9uEih",
            name="check_eligibility",
            arguments={"code": "EEE4118F"},
        ),
    )


@pytest.mark.parametrize(
    ("answer", "raised"),
    [
        (httpx2.ConnectError("Made up."), ModelUnavailable),
        (httpx2.ReadTimeout("Made up."), ModelUnavailable),
        (429, ModelUnavailable),
        (503, ModelUnavailable),
        (401, AuthenticationError),
        (400, BadRequestError),
    ],
    ids=[
        "no connection",
        "a timeout",
        "too many requests",
        "a server error",
        "a bad key",
        "a malformed request",
    ],
)
def test_only_the_errors_the_sdk_retries_mean_luna_cant_be_reached(
    served, answer, raised
):
    served(answer)
    with pytest.raises(raised):
        OpenAIModel("made-up-key", "gpt-6-luna").respond("Made up.", [ASKED])
