# Checks the harness without calling a model: a turn runs the tool the model asks for and passes
# its result back, and a cached turn is replayed with no call at all
import json

from asking import HAIKU, turn
from labels import Prompt

PROMPT = Prompt(
    id="B-test-1",
    part="B",
    stressor="not eligible",
    plans=("V06",),
    question="Can I take EEE4121F?",
)


def fake_haiku(calls: list[dict]):
    # Asks check_eligibility first, then replies, in the shape Anthropic's API replies in
    def call(body: dict) -> tuple[dict, int]:
        calls.append(body)
        if len(body["messages"]) == 1:
            asks = {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "check_eligibility",
                "input": {"code": "EEE4121F"},
            }
            return {"content": [asks], "stop_reason": "tool_use"}, 0
        reply = {
            "content": "No.",
            "referral": False,
            "open_plan_id": None,
            "citations": [],
        }
        text = {"type": "text", "text": json.dumps(reply)}
        return {"content": [text], "stop_reason": "end_turn"}, 0

    return call


def test_a_turn_runs_the_tool_asked_for_and_a_cached_turn_calls_no_model(tmp_path):
    calls = []
    first = turn(HAIKU, PROMPT, 1, {}, tmp_path, fake_haiku(calls))
    # EEE4121F is outside her plans and has no written verdict, so the stand-in says check
    result = first["tools"][0]["result"]
    assert result["status"] == "check"
    assert json.loads(calls[1]["messages"][-1]["content"][0]["content"]) == result
    assert turn(HAIKU, PROMPT, 1, {}, tmp_path, fake_haiku(calls)) == first
    assert len(calls) == 2
