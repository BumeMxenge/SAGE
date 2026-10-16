# Checks the drafter without calling a model: every worked example in the prompt fits Luna's schema,
# Haiku's answer is read from a code fence, and a cached reply is reused
import json

import jsonschema
from pydantic import TypeAdapter
from sage.domain.rules import EntryRule

from drafting import HAIKU, PROMPT, SCHEMA, answer, reply

ANSWER = TypeAdapter(EntryRule | None)


def test_every_example_in_the_prompt_fits_lunas_schema():
    examples = [
        json.loads(line) for line in PROMPT.splitlines() if line.startswith('{"rule"')
    ]
    assert examples, "the prompt has no worked examples"
    for example in examples:
        jsonschema.validate(example, SCHEMA)
        ANSWER.validate_python(example["rule"])


def test_haikus_answer_is_read_with_or_without_a_code_fence():
    # Haiku has no schema to hold it to plain JSON, so it may fence its answer
    rule = '{"rule": null}'
    for text in (rule, f"```json\n{rule}\n```", f"```\n{rule}\n```"):
        assert answer(HAIKU, {"content": [{"type": "text", "text": text}]}) == rule


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
