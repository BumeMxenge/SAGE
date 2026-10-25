# Checks the drafter asks SAGE's model for a rule tree exactly as E2 asked GPT-6 Luna, and that a
# reply holding no rule is refused while the run goes on. A scripted model answers, so no test calls
# a real one.
import importlib
import json
from pathlib import Path

import pytest

from sage.ingestion.drafting import ModelDrafter
from sage.ingestion.translate import translate
from sage.shared.language_model import Response, Said, Schema
from sage.shared.memory.language_model import ScriptedModel
from sage.shared.rules import Refer

E2 = (
    Path(__file__).resolve().parents[4]
    / "experiments"
    / "ingestion"
    / "requirement-parsing"
)
# CSC2002S's requirement (2026, page 170), which the grammar refuses for its mark, and the tree a
# person would write from the page: a final mark of at least 45 in CSC2001F, pass or not
REFUSED = "CSC2001F (At least 45% for CSC2001F)"
MARK = {"course": "CSC2001F", "need": "mark", "min_mark": 45}
# The co-requisite E2's prompt gives as an example, which the grammar refuses for its "or equivalent"
EQUIVALENT = "MAM1020F (or equivalent)"


@pytest.fixture
def e2(monkeypatch):
    # E2's drafting.py, which builds the request it sent each model
    monkeypatch.syspath_prepend(str(E2))
    return importlib.import_module("drafting")


def replies(*texts):
    return ScriptedModel({"entry_rule": [Response(text=text) for text in texts]})


@pytest.mark.parametrize(
    ("need", "field"),
    # The labels the handbook prints each field under
    [("pass", "Course entry requirements"), ("concurrent", "Co-requisites")],
)
def test_a_draft_is_asked_for_as_e2_asked_luna(e2, need, field):
    model = replies(json.dumps({"rule": MARK}))
    drafter = ModelDrafter(model)
    # The model's name goes into the cache with each draft
    assert (drafter.model, drafter.draft(REFUSED, need)) == ("a scripted model", MARK)
    body = e2.request(e2.LUNA, field, REFUSED)
    (call,) = model.calls
    assert (call.instructions, call.conversation, call.schema) == (
        body["instructions"],
        (Said(role="user", text=body["input"]),),
        Schema(
            name=body["text"]["format"]["name"],
            shape=body["text"]["format"]["schema"],
        ),
    )
    # E2 set no sampling, reasoning or tools, so Luna ran at its defaults
    assert (call.tools, call.effort) == ((), None)


@pytest.mark.parametrize(
    "reply",
    [
        None,  # cut off, so it has no text
        "null",  # JSON, but not an object
        '["CSC2001F"]',
        json.dumps({"tree": MARK}),  # an object with no rule
    ],
)
def test_a_reply_holding_no_rule_is_refused_and_the_run_goes_on(tmp_path, reply):
    # translate asks for REFUSED first, as it drafts strings in order
    model = replies(reply, json.dumps({"rule": {"refer": EQUIVALENT}}))
    read = translate(
        [(REFUSED, "pass"), (EQUIVALENT, "concurrent")],
        tmp_path / "drafts.json",
        ModelDrafter(model),
    )
    # Never read as "no requirement", which a null rule means
    assert read.refused == (REFUSED,)
    assert [(t.printed, t.tree, t.drafted) for t in read.translations] == [
        (REFUSED, Refer(refer=REFUSED), False),
        (EQUIVALENT, Refer(refer=EQUIVALENT), True),
    ]
    assert read.calls == 2
