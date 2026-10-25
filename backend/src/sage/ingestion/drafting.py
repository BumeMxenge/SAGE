# The interface a model that drafts rule trees implements, and the drafter that fills it on SAGE's one
# language model. translate depends only on the interface, so its tests use a fake that never calls
# a model.
import json
from pathlib import Path
from typing import Literal, Protocol

from pydantic import JsonValue

from sage.shared.language_model import LanguageModel, Said, Schema, strict_object

# E2's prompt.md, copied unchanged, sent from after its opening note for people, split as E2's
# drafting.py splits it
PROMPT = (
    Path(__file__)
    .with_name("drafting_prompt.md")
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
# The label each need is printed under, which the model reads with the text
FIELDS = {"pass": "Course entry requirements", "concurrent": "Co-requisites"}


# A tree node's children, each a node
BRANCH = {"type": "array", "items": {"$ref": "#/$defs/node"}, "minItems": 1}
# E2's reply schema: {"rule": <tree>}, or {"rule": null} where the field asks for nothing. The tree
# is recursive, and the API needs an object at the top, not a choice of nodes. A node is an all or
# any of nodes, or a leaf, and the course leaf is split in two, so a min_mark comes with a mark leaf
# and only then.
SCHEMA = Schema(
    name="entry_rule",
    shape={
        **strict_object(rule={"anyOf": [{"$ref": "#/$defs/node"}, {"type": "null"}]}),
        "$defs": {
            "node": {
                "anyOf": [
                    strict_object(all=BRANCH),
                    strict_object(any=BRANCH),
                    strict_object(
                        course={"type": "string"},
                        need={"enum": ["pass", "concurrent"]},
                    ),
                    strict_object(
                        course={"type": "string"},
                        need={"enum": ["mark"]},
                        min_mark={"type": "integer"},
                    ),
                    strict_object(
                        student_in={
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        }
                    ),
                    strict_object(min_year_of_study={"type": "integer"}),
                    strict_object(refer={"type": "string"}),
                ]
            }
        },
    },
)


class Drafter(Protocol):
    model: str  # the model's name, kept with each of its drafts

    # A rule tree, as JSON, for printed wording the grammar refused. A co-requisite's leaves need the
    # course taken alongside, the rest a pass.
    def draft(self, printed: str, need: Literal["pass", "concurrent"]) -> JsonValue: ...


class ModelDrafter:
    # Drafts on SAGE's language model, asked as E2 asked GPT-6 Luna: E2's prompt, the field's name
    # with its printed text, and the reply held to E2's schema. translate checks every draft against
    # EntryRule before keeping it.
    def __init__(self, model: LanguageModel) -> None:
        self._model = model
        self.model = model.model

    def draft(self, printed: str, need: Literal["pass", "concurrent"]) -> JsonValue:
        said = Said(role="user", text=f"{FIELDS[need]}: {printed}")
        text = self._model.respond(PROMPT, [said], schema=SCHEMA).text or ""
        try:
            answer = json.loads(text)
        except json.JSONDecodeError:
            answer = None
        if isinstance(answer, dict) and "rule" in answer:
            return answer["rule"]
        # Any other reply, such as one cut off, one that isn't JSON, or JSON that isn't an object
        # holding a rule, comes back as its text. That isn't a rule tree, so translate reports it
        # rather than keeping it, and the run goes on.
        return text
