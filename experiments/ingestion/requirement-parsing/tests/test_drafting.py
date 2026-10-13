# Checks the drafter without calling a model: every worked example in the prompt fits the schema
# each model is held to, Haiku's unrolled tree stops at its depth, and a cached reply is reused
import json

import jsonschema
import pytest
from pydantic import TypeAdapter
from sage.domain.rules import EntryRule

from drafting import DEPTH, HAIKU, LUNA, PROMPT, SCHEMAS, reply

ANSWER = TypeAdapter(EntryRule | None)


@pytest.mark.parametrize("model", [HAIKU, LUNA])
def test_every_example_in_the_prompt_fits_the_schema(model):
    examples = [
        json.loads(line) for line in PROMPT.splitlines() if line.startswith('{"rule"')
    ]
    assert examples, "the prompt has no worked examples"
    for example in examples:
        jsonschema.validate(example, SCHEMAS[model])
        ANSWER.validate_python(example["rule"])


def nested(depth: int) -> dict:
    # A tree this many levels deep: alls around a leaf
    tree: dict = {"course": "EEE3091F", "need": "pass"}
    for _ in range(depth - 1):
        tree = {"all": [tree]}
    return {"rule": tree}


def test_haikus_schema_holds_a_tree_seven_levels_deep_and_no_deeper():
    jsonschema.validate(nested(DEPTH), SCHEMAS[HAIKU])
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(nested(DEPTH + 1), SCHEMAS[HAIKU])
    # Luna's schema is recursive, so it has no such limit
    jsonschema.validate(nested(DEPTH + 1), SCHEMAS[LUNA])


def test_a_cached_reply_never_calls_the_model(tmp_path):
    calls = []

    def fake_model(body):
        # Records each call and answers every string with no rule
        calls.append(body)
        return {"content": [{"type": "text", "text": '{"rule": null}'}]}

    first = reply(HAIKU, "Co-requisites", "None", 1, tmp_path, fake_model)
    assert reply(HAIKU, "Co-requisites", "None", 1, tmp_path, fake_model) == first
    # Another run of the same string asks the model afresh
    reply(HAIKU, "Co-requisites", "None", 2, tmp_path, fake_model)
    assert len(calls) == 2
