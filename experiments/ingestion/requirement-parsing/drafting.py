# Asks a model for the tree a printed requirement means, in the form SAGE would ship: the shared
# prompt in prompt.md, schema-constrained output and default sampling. Every raw reply is cached in
# results/replies/, keyed by model, string and run, so a rerun never calls a provider. This is the
# only code in E2 that calls one.
import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path

import anthropic
import openai

HERE = Path(__file__).parent
REPLIES = HERE.parent / "results" / "replies"
# Everything after the opening note for people
PROMPT = (HERE / "prompt.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()

HAIKU = "claude-haiku-5-5"
LUNA = "gpt-6-luna"
# Haiku's structured output refuses a recursive schema, so its tree is unrolled to this many
# levels. The label check refuses a label this deep, so no printed tree reaches the limit.
DEPTH = 7
# Room for Haiku's thinking, which is on by default, as well as its answer
MAX_TOKENS = 16_000


def _object(**properties: dict) -> dict:
    # An object with exactly these properties, all required, as both providers' strict schemas need
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _node(children: dict | None) -> dict:
    # A tree node: a leaf, or an all or any of children with the given schema (none at the deepest
    # level). The course leaf is split in two, so a min_mark comes with a mark leaf and only then.
    nodes = [
        _object(course={"type": "string"}, need={"enum": ["pass", "concurrent"]}),
        _object(
            course={"type": "string"},
            need={"enum": ["mark"]},
            min_mark={"type": "integer"},
        ),
        _object(
            student_in={"type": "array", "items": {"type": "string"}, "minItems": 1}
        ),
        _object(min_year_of_study={"type": "integer"}),
        _object(refer={"type": "string"}),
    ]
    if children:
        branch = {"type": "array", "items": children, "minItems": 1}
        nodes += [_object(all=branch), _object(any=branch)]
    return {"anyOf": nodes}


def _answer(defs: dict, top: str) -> dict:
    # {"rule": <tree>}, or {"rule": null} where the field asks for nothing. Luna needs an object at
    # the top, not a choice of nodes.
    rule = {"anyOf": [{"$ref": f"#/$defs/{top}"}, {"type": "null"}]}
    return {**_object(rule=rule), "$defs": defs}


SCHEMAS = {
    LUNA: _answer({"node": _node({"$ref": "#/$defs/node"})}, "node"),
    HAIKU: _answer(
        {
            f"level{level}": _node(
                {"$ref": f"#/$defs/level{level + 1}"} if level < DEPTH else None
            )
            for level in range(1, DEPTH + 1)
        },
        "level1",
    ),
}


def request(model: str, field: str, text: str) -> dict:
    # The whole request for one string, with no sampling settings, so each model uses its defaults
    printed = f"{field}: {text}"
    if model == HAIKU:
        return {
            "model": HAIKU,
            "max_tokens": MAX_TOKENS,
            "system": PROMPT,
            "messages": [{"role": "user", "content": printed}],
            "output_config": {
                "format": {"type": "json_schema", "schema": SCHEMAS[HAIKU]}
            },
        }
    return {
        "model": LUNA,
        "instructions": PROMPT,
        "input": printed,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "entry_rule",
                "schema": SCHEMAS[LUNA],
                "strict": True,
            }
        },
    }


def digest(body: dict) -> str:
    # A request's fingerprint, kept with its reply so a reply can't be scored against a changed one
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def key(field: str, text: str) -> str:
    # A string's short, stable name in the cache
    return hashlib.sha256(f"{field}\n{text}".encode()).hexdigest()[:12]


def call_provider(body: dict) -> dict:
    # One request to the model's provider, which reads its key from the environment
    if body["model"] == HAIKU:
        return anthropic.Anthropic().messages.create(**body).model_dump(mode="json")
    return openai.OpenAI().responses.create(**body).model_dump(mode="json")


def reply(
    model: str,
    field: str,
    text: str,
    run: int,
    folder: Path = REPLIES,
    call: Callable[[dict], dict] = call_provider,
) -> dict:
    # This run's reply for the string, from the cache, or else from the provider and then cached,
    # with the request's fingerprint and how long the provider took
    body = request(model, field, text)
    path = folder / model / f"{key(field, text)}-{run}.json"
    if not path.exists():
        start = time.perf_counter()
        raw = call(body)
        seconds = round(time.perf_counter() - start, 2)
        entry = {"request": digest(body), "seconds": seconds, "reply": raw}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entry, indent=1) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))
