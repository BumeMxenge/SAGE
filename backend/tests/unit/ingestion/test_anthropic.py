# Checks Claude is asked for a draft exactly as E2 asked it, and its answer is read past its thinking
# and any code fence. A fake transport answers in the API's place, so no test calls a model.
import json
from functools import partial
from pathlib import Path

import httpx2
import pytest
from anthropic import Anthropic

from sage.ingestion import anthropic as adapter
from sage.ingestion.anthropic import ClaudeDrafter

# What E2 sent as the system prompt: its prompt.md from after the opening note for people, split as
# its drafting.py splits it
E2_PROMPT = (
    (
        Path(__file__).resolve().parents[4]
        / "experiments"
        / "ingestion"
        / "requirement-parsing"
        / "prompt.md"
    )
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
# CSC2002S's requirement (2026, page 170), which the grammar refuses for its mark, and the tree a
# person would write from the page: a final mark of at least 45 in CSC2001F, pass or not
REFUSED = "CSC2001F (At least 45% for CSC2001F)"
MARK = {"course": "CSC2001F", "need": "mark", "min_mark": 45}
# E2's prompt's own example for this co-requisite
EQUIVALENT = {
    "any": [{"course": "MAM1020F", "need": "concurrent"}, {"refer": "or equivalent"}]
}


@pytest.fixture
def served(monkeypatch):
    # The drafter's client sends through a fake transport, which keeps each request's body and
    # answers with the next text given, after a thinking block, as Haiku answers
    def serve(*texts):
        bodies, answers = [], iter(texts)

        def reply(request):
            bodies.append(json.loads(request.content))
            content = [
                {"type": "thinking", "thinking": "Made up.", "signature": "made-up"},
                {"type": "text", "text": next(answers)},
            ]
            return httpx2.Response(
                200,
                json={
                    "id": "msg_made_up",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-haiku-5-5",
                    "content": content,
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": 3000, "output_tokens": 200},
                },
            )

        client = httpx2.Client(transport=httpx2.MockTransport(reply))
        monkeypatch.setattr(
            adapter, "Anthropic", partial(Anthropic, http_client=client)
        )
        return bodies

    return serve


@pytest.mark.parametrize(
    ("need", "field"),
    # The labels the handbook prints each field under
    [("pass", "Course entry requirements"), ("concurrent", "Co-requisites")],
)
def test_a_draft_is_asked_for_as_e2_asked(served, need, field):
    bodies = served(json.dumps({"rule": MARK}))
    ClaudeDrafter("made-up-key", "claude-haiku-5-5").draft(REFUSED, need)
    # E2's request and nothing more: no thinking setting, so thinking is on by default, and no
    # output_config
    assert bodies == [
        {
            "model": "claude-haiku-5-5",
            "max_tokens": 16_000,
            "system": E2_PROMPT,
            "messages": [{"role": "user", "content": f"{field}: {REFUSED}"}],
        }
    ]


def test_an_answer_is_read_past_its_thinking_and_any_code_fence(served):
    served(
        json.dumps({"rule": MARK}),
        "```json\n" + json.dumps({"rule": EQUIVALENT}) + "\n```",
    )
    drafter = ClaudeDrafter("made-up-key", "claude-haiku-5-5")
    assert drafter.draft(REFUSED, "pass") == MARK
    assert drafter.draft("MAM1020F (or equivalent)", "concurrent") == EQUIVALENT
    # Two replies of 3,000 tokens in and 200 out, at USD 0.10 and 0.50 a million:
    # (6,000 x 0.10 + 400 x 0.50) / 1,000,000 = USD 0.0008
    assert drafter.tokens == {"input": 6000, "cached": 0, "output": 400}
    assert drafter.cost == pytest.approx(0.0008)


def test_an_answer_that_is_not_json_comes_back_as_its_text(served):
    # A comma missing, as in one of 2026's replies. The text fails EntryRule, so translate reports
    # it, and the run goes on.
    broken = '{"rule": {"any": [{"course": "MAM1020F", "need": "pass"} {"refer": "or equivalent"}]}}'
    served(broken)
    drafter = ClaudeDrafter("made-up-key", "claude-haiku-5-5")
    assert drafter.draft("MAM1020F or equivalent", "pass") == broken
