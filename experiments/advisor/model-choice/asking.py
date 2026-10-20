# Asks each model every chosen prompt five times, as SAGE would ship it: one system prompt with the
# slice, cached; the same tools and reply schema, strict; and each provider's default sampling,
# thinking and reasoning. Each turn is cached in results/replies/, keyed by model, prompt and ask,
# with every call's fingerprint, seconds and retries, so a rerun never calls a provider. This is the
# only code in E4 that calls one.
import hashlib
import json
import random
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

import anthropic
import openai
from sage.shared.planning import Eligibility

import evidence
from check_labels import problems
from labels import Prompt, chosen, load

HERE = Path(__file__).parent
REPLIES = HERE.parent / "results" / "replies"
# Everything in prompt.md after its opening note for people, then the slice
SYSTEM = (
    (HERE / "prompt.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()
    + "\n\n"
    + evidence.slice_text()
)

HAIKU = "claude-haiku-5-5"
LUNA = "gpt-6-luna"
MODELS = {HAIKU: "Claude Haiku 5.5", LUNA: "GPT-6 Luna"}
ASKS = 5
# A turn still calling tools after this many calls is cut off, and counts as a broken reply
CALLS = 6
# Room for Haiku's thinking, which is on by default, as well as its reply, as in E2
MAX_TOKENS = 16_000
ORDER_SEED = 1

# The reply both models must give, in the shape of shared/advisor.py's Reply, with short ids
REPLY = evidence.strict_object(
    content={"type": "string"},
    referral={"type": "boolean"},
    open_plan_id={"type": ["string", "null"]},
    citations={
        "type": "array",
        "items": evidence.strict_object(
            passage_id={"type": "string"}, quote={"type": "string"}
        ),
    },
)


def question(prompt: Prompt) -> str:
    # The student's message: her details, then what she asks
    context = evidence.context(prompt.plans, prompt.term)
    return f"{context}\n\nQuestion\n{prompt.question}"


def request(model: str, conversation: list[dict]) -> dict:
    # The whole request for one call. It sets no sampling, thinking or reasoning, so each model
    # runs at its defaults, and caches the system prompt: Luna by default, Haiku by its mark.
    if model == HAIKU:
        return {
            "model": HAIKU,
            "max_tokens": MAX_TOKENS,
            "system": [
                {"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}
            ],
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["schema"],
                    "strict": True,
                }
                for tool in evidence.TOOLS
            ],
            "output_config": {"format": {"type": "json_schema", "schema": REPLY}},
            "messages": conversation,
        }
    return {
        "model": LUNA,
        "instructions": SYSTEM,
        "tools": [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["schema"],
                "strict": True,
            }
            for tool in evidence.TOOLS
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "reply",
                "schema": REPLY,
                "strict": True,
            }
        },
        "input": conversation,
    }


def tool_calls(model: str, raw: dict) -> list[tuple[str, str, dict]]:
    # The tools a reply asks for: each call's id, the tool's name and its arguments
    if model == HAIKU:
        return [
            (block["id"], block["name"], block["input"])
            for block in raw["content"]
            if block["type"] == "tool_use"
        ]
    return [
        (item["call_id"], item["name"], json.loads(item["arguments"]))
        for item in raw["output"]
        if item["type"] == "function_call"
    ]


def _echo(value: object) -> object:
    # A reply's content as its API takes it back: unchanged, less the empty fields the SDK fills
    if isinstance(value, dict):
        return {key: _echo(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_echo(item) for item in value]
    return value


def answered(
    model: str, conversation: list[dict], raw: dict, results: list[tuple[str, dict]]
) -> list[dict]:
    # The conversation with the model's reply passed back, its thinking blocks or reasoning items
    # included as each API requires, and then each tool's result
    if model == HAIKU:
        return [
            *conversation,
            {"role": "assistant", "content": _echo(raw["content"])},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": call_id,
                        "content": json.dumps(result),
                    }
                    for call_id, result in results
                ],
            },
        ]
    return [
        *conversation,
        *_echo(raw["output"]),
        *(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result),
            }
            for call_id, result in results
        ),
    ]


def reply_text(model: str, raw: dict) -> str | None:
    # The reply's JSON text, or None where the model gave none: refused, cut off, or still calling
    # tools when the turn was cut off
    if model == HAIKU:
        if raw["stop_reason"] != "end_turn":
            return None
        return "".join(
            block["text"] for block in raw["content"] if block["type"] == "text"
        )
    if raw["status"] != "completed" or tool_calls(model, raw):
        return None
    return "".join(
        part["text"]
        for item in raw["output"]
        if item["type"] == "message"
        for part in item["content"]
        if part["type"] == "output_text"
    )


def tokens(model: str, raw: dict) -> dict[str, int]:
    # A call's tokens: fresh input, input read from the cache, input written to it, and output,
    # thinking included. Anthropic counts each kind of input apart, OpenAI all within input.
    usage = raw["usage"]
    if model == HAIKU:
        return {
            "fresh": usage["input_tokens"],
            "read": usage["cache_read_input_tokens"] or 0,
            "written": usage["cache_creation_input_tokens"] or 0,
            "out": usage["output_tokens"],
        }
    details = usage["input_tokens_details"]
    read, written = details["cached_tokens"], details.get("cache_write_tokens") or 0
    return {
        "fresh": usage["input_tokens"] - read - written,
        "read": read,
        "written": written,
        "out": usage["output_tokens"],
    }


def digest(body: dict) -> str:
    # A request's fingerprint, kept with its reply so a reply can't be scored against a changed one
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


@cache
def _client(model: str) -> anthropic.Anthropic | openai.OpenAI:
    # One client per provider for the whole run, so calls reuse a connection, as SAGE's would
    return anthropic.Anthropic() if model == HAIKU else openai.OpenAI()


def call_provider(body: dict) -> tuple[dict, int]:
    # One request to the model's provider, which reads its key from the environment, and the
    # retries its SDK took to get the reply
    model = body["model"]
    if model == HAIKU:
        response = _client(model).messages.with_raw_response.create(**body)
    else:
        response = _client(model).responses.with_raw_response.create(**body)
    return response.parse().model_dump(mode="json"), response.retries_taken


def turn(
    model: str,
    prompt: Prompt,
    ask: int,
    verdicts: Mapping[str, Eligibility],
    folder: Path = REPLIES,
    call: Callable[[dict], tuple[dict, int]] = call_provider,
) -> dict:
    # One ask: the model's calls until it replies, each running the tools it asks for. A turn comes
    # from the cache, or else from the provider and is then cached whole. Replaying a cached turn
    # rebuilds each request and checks its fingerprint, so no reply is scored against a request
    # that has changed since.
    path = folder / model / f"{prompt.id}-{ask}.json"
    cached = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    started = datetime.now(UTC).isoformat(timespec="seconds")
    conversation = [{"role": "user", "content": question(prompt)}]
    calls, tools = [], []
    for number in range(CALLS):
        body = request(model, conversation)
        if cached is None:
            begin = time.perf_counter()
            raw, retries = call(body)
            seconds = round(time.perf_counter() - begin, 2)
            entry = {
                "request": digest(body),
                "seconds": seconds,
                "retries": retries,
                "reply": raw,
            }
        else:
            known = cached["calls"]
            entry = known[number] if number < len(known) else None
            if entry is None or entry["request"] != digest(body):
                raise SystemExit(
                    f"{model}'s turn {path.stem} answers an older request: "
                    "delete it and run asking.py"
                )
        calls.append(entry)
        wanted = tool_calls(model, entry["reply"])
        if not wanted or number == CALLS - 1:
            break
        results = []
        for call_id, name, arguments in wanted:
            result = evidence.run_tool(name, arguments, verdicts)
            tools.append({"name": name, "arguments": arguments, "result": result})
            results.append((call_id, result))
        conversation = answered(model, conversation, entry["reply"], results)
    if cached is None:
        cached = {"at": started, "calls": calls}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cached, indent=1) + "\n", encoding="utf-8")
    elif len(cached["calls"]) != len(calls):
        raise SystemExit(
            f"{model}'s turn {path.stem} holds calls its replay never makes"
        )
    return {"at": cached["at"], "calls": calls, "tools": tools}


def order(prompts: list[Prompt]) -> list[tuple[str, Prompt, int]]:
    # Every turn, shuffled by a fixed seed so the time of day can't favour either model
    turns = [
        (model, prompt, ask)
        for prompt in prompts
        for model in MODELS
        for ask in range(1, ASKS + 1)
    ]
    random.Random(ORDER_SEED).shuffle(turns)
    return turns


if __name__ == "__main__":
    # Fills the cache, one turn at a time. The labels come first, so it won't start while any
    # label doesn't fit.
    if problems():
        raise SystemExit("Some labels don't fit: run check_labels.py")
    sheet = load()
    turns = order(chosen(sheet))
    for number, (model, prompt, ask) in enumerate(turns, start=1):
        turn(model, prompt, ask, sheet.verdicts)
        print(f"{number} of {len(turns)} turns asked")
