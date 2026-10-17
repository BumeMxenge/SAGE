# Asks a model for the tree a printed requirement means, in the form SAGE would ship: the shared
# prompt in prompt.md and default sampling, with GPT-6 Luna held to a schema. Claude Haiku 5.5 gets
# none: its structured output compiles a rule tree only three levels deep, and printed trees go
# deeper. Every raw reply is cached in results/replies/, keyed by model, string and run, so a rerun
# never calls a provider. This is the only code in E2 that calls one.
import hashlib
import json
import re
import time
from collections.abc import Callable
from pathlib import Path

import anthropic
import openai

from extract import labels, wording

HERE = Path(__file__).parent
REPLIES = HERE.parent / "results" / "replies"
# Everything after the opening note for people
PROMPT = (HERE / "prompt.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()

HAIKU = "claude-haiku-5-5"
LUNA = "gpt-6-luna"
# Each model's name in the tables, and its USD price per million tokens in, read from the
# provider's cache, and out, for prompts this short. From the providers' pricing pages on 13 October
# 2026: platform.claude.com/docs/en/about-claude/pricing and developers.openai.com/api/docs/pricing.
MODELS = {
    HAIKU: ("Claude Haiku 5.5", 0.10, 0.01, 0.50),
    LUNA: ("GPT-6 Luna", 0.10, 0.01, 0.50),
}
RUNS = 3
# Room for Haiku's thinking, which is on by default, as well as its answer
MAX_TOKENS = 16_000
# A code fence around an answer, which Haiku may add without a schema to hold it to plain JSON
FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _object(**properties: dict) -> dict:
    # An object with exactly these properties, all required, as Luna's strict schema needs
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _node(children: dict) -> dict:
    # A tree node: an all or any of children, or a leaf. The course leaf is split in two, so a
    # min_mark comes with a mark leaf and only then.
    branch = {"type": "array", "items": children, "minItems": 1}
    return {
        "anyOf": [
            _object(all=branch),
            _object(any=branch),
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
    }


# Luna's answer: {"rule": <tree>}, or {"rule": null} where the field asks for nothing. The tree is
# recursive, and Luna needs an object at the top, not a choice of nodes.
SCHEMA = {
    **_object(rule={"anyOf": [{"$ref": "#/$defs/node"}, {"type": "null"}]}),
    "$defs": {"node": _node({"$ref": "#/$defs/node"})},
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
        }
    return {
        "model": LUNA,
        "instructions": PROMPT,
        "input": printed,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "entry_rule",
                "schema": SCHEMA,
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


def answer(model: str, raw: dict) -> str | None:
    # The text of a reply's answer, out of any code fence, or None where it has none, as when the
    # model refuses
    if model == HAIKU:
        texts = [block["text"] for block in raw["content"] if block["type"] == "text"]
    else:
        texts = [
            part["text"]
            for item in raw["output"]
            if item["type"] == "message"
            for part in item["content"]
            if part["type"] == "output_text"
        ]
    text = "".join(texts).strip()
    fenced = FENCE.match(text)
    return (fenced[1] if fenced else text) or None


def tokens(model: str, raw: dict) -> tuple[int, int, int]:
    # A reply's tokens: in at the full price, in from the provider's cache, and out, which counts
    # the model's reasoning. Anthropic counts cache reads apart from the rest, OpenAI within them.
    usage = raw["usage"]
    if model == HAIKU:
        cached = usage["cache_read_input_tokens"] or 0
        return usage["input_tokens"], cached, usage["output_tokens"]
    cached = usage["input_tokens_details"]["cached_tokens"]
    return usage["input_tokens"] - cached, cached, usage["output_tokens"]


if __name__ == "__main__":
    # Fills the cache for every string on the label sheet, three runs on each model. The labels
    # come first, so it won't start while any row is still empty.
    rows = labels()
    if any(not row["tree"].strip() for row in rows):
        raise SystemExit("Label every row of labels.csv before drafting")
    for number, row in enumerate(rows, start=1):
        for model in (HAIKU, LUNA):
            for run in range(1, RUNS + 1):
                reply(model, row["field"], wording(row), run)
        print(f"{number} of {len(rows)} strings drafted")
