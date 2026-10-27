# Judges every ATP-3 reply with Claude Sonnet 5.5, then lets code override it wherever a field can be
# checked exactly: the engine's verdict on a validity claim, a plan offered outside the plans that
# fit, and the referral flag a SAGE reply carries. Writes results/judge.csv. The judge can't run at
# temperature 0, as Claude Sonnet 5.5 accepts only the default, so each of its replies is cached
# under the SHA-256 of its request: that fixes its marks, a rerun spends nothing, and a crash resumes
# where it stopped. make atp3 runs it after ask.py, from backend/, with the key in atp3/.env.
import csv
import hashlib
import json
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

import anthropic
from ask import BUDGET, WORKERS, as_json, write
from pydantic_settings import BaseSettings, SettingsConfigDict
from resolve import ANSWERABLE, CODE, RESULTS, Row, read_prompts, read_resolved, verdict
from students import HERE, prepared, stores

from sage.shared.base import Row as Model
from sage.shared.language_model import strict_object

JUDGE = "claude-sonnet-5-5"
# USD per million tokens, from Anthropic's model table of 6 October 2026. Cache reads and writes are
# priced in case a request ever uses them, though a judge request is too short to cache.
PRICES = {
    "input_tokens": 2.00,
    "output_tokens": 10.00,
    "cache_read_input_tokens": 0.20,
    "cache_creation_input_tokens": 2.50,
}
CACHE = RESULTS / "judge"
# Everything in judge_prompt.md after its note for people
RULES = (
    (HERE / "judge_prompt.md")
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
Outcome = Literal[
    "correct_answer", "correct_referral", "over_referral", "wrong_safe", "unsupported"
]
Claim = Literal["eligible", "not_eligible", "check", "none"]
SCHEMA = strict_object(
    outcome={
        "type": "string",
        "enum": [
            "correct_answer",
            "correct_referral",
            "over_referral",
            "wrong_safe",
            "unsupported",
        ],
    },
    validity_claim={
        "type": "string",
        "enum": ["eligible", "not_eligible", "check", "none"],
    },
    validity_course={"type": "string"},
    citations={
        "type": "array",
        "items": strict_object(
            position={"type": "integer"}, supports={"type": "boolean"}
        ),
    },
    reason={"type": "string"},
)
COLUMNS = (
    "turn",
    "arm",
    "prompt",
    "try",
    "judge_outcome",
    "validity_claim",
    "validity_course",
    "engine_verdict",
    "marks",
    "cited",
    "supported",
    "reason",
    "outcome",
    "rule",
    "judge_seconds",
    "judge_input_tokens",
    "judge_output_tokens",
    "judge_cost",
    "key",
)


class Key(BaseSettings):
    # The judge's key, from tests/acceptance/atp3/.env, which git ignores
    model_config = SettingsConfigDict(env_file=HERE / ".env", extra="ignore")
    anthropic_api_key: str = ""


class Mark(Model):
    position: int
    supports: bool


class Judged(Model):
    outcome: Outcome
    validity_claim: Claim
    validity_course: str
    citations: tuple[Mark, ...]
    reason: str


def case(prompt: Row, resolved: Row, turn: Row) -> str:
    # What the judge sees for one reply: the question, what a right reply does and the facts behind
    # it, the reply's words, and each citation with its passage. Never the arm's name or the flag.
    lines = [
        "Question",
        prompt["prompt"],
        "",
        "What a right reply does",
        f"- Expected behaviour: {resolved['expected']}",
        f"- Expected fact: {prompt['expected_fact'] or 'none given'}",
    ]
    if prompt["quote"].strip():
        lines.append(f'- Handbook quote: "{prompt["quote"]}" (page {prompt["page"]})')
    if prompt["tempting_wrong"].strip():
        lines.append(f"- Trap to watch for: {prompt['tempting_wrong']}")
    lines += [
        "",
        "What SAGE's engine and plan data say",
        resolved["words"],
        "",
        "The reply",
    ]
    lines.append(turn["reply"])
    citations = json.loads(turn["citations"] or "[]")
    lines += ["", "Its citations"]
    if not citations:
        lines.append("None.")
    for citation in citations:
        lines += [
            (
                f'{citation["position"]}. "{citation["quote"]}" '
                f"({citation['section']}, page {citation['page']}). The passage reads:"
            ),
            citation["text"],
        ]
    return "\n".join(lines)


def request(text: str) -> dict:
    # No sampling setting, as the model takes only the default, and no refusal fallback, as an
    # instrument must stay one model
    return {
        "model": JUDGE,
        "max_tokens": 16000,
        "system": RULES,
        "messages": [{"role": "user", "content": text}],
        "thinking": {"type": "adaptive"},
        "output_config": {
            "effort": "low",
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
    }


def cost(usage: dict) -> float:
    return sum((usage.get(kind) or 0) * price for kind, price in PRICES.items()) / 1e6


def asked(client: anthropic.Anthropic, body: dict) -> dict:
    # The judge's reply to one request, from the cache when it was asked before
    key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    started = time.monotonic()
    message = client.messages.create(**body)
    if message.stop_reason != "end_turn":
        raise SystemExit(f"The judge stopped with {message.stop_reason}, request {key}")
    saved = {
        "key": key,
        "seconds": round(time.monotonic() - started, 3),
        "message": message.model_dump(mode="json"),
    }
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
    return saved


def judged(saved: dict) -> Judged:
    text = next(
        block["text"]
        for block in saved["message"]["content"]
        if block["type"] == "text"
    )
    return Judged.model_validate_json(text)


def final(
    turn: Row,
    answerable: bool,
    judge: Judged,
    engine: str | None,
    fitting: Sequence[str] | None,
) -> tuple[str, str]:
    # The outcome once code has checked what it can, and the rule that changed the judge's, if one
    # did. engine is its verdict on the claim's course, and fitting the plans a find_plan prompt
    # resolved to, empty for "no plan", or None on any other prompt.
    sage = turn["arm"] == "sage"
    claim = judge.validity_claim
    if claim in ("eligible", "not_eligible") and engine and claim != engine:
        return "unsupported", "engine"
    if (
        sage
        and fitting is not None
        and turn["offered"]
        and turn["offered"] not in fitting
    ):
        return "unsupported", "plan"
    outcome = judge.outcome
    if outcome == "unsupported":
        return outcome, ""
    flag = sage and turn["referral"] == "yes"
    if answerable:
        # The fixed referral, or a reply that refers without giving the answer, answers nothing
        referred = (sage and turn["fixed"] == "yes") or outcome == "correct_referral"
        if referred or (flag and outcome != "correct_answer"):
            return "over_referral", "" if outcome == "over_referral" else "referral"
    elif flag or outcome == "over_referral":
        return "correct_referral", "" if outcome == "correct_referral" else "referral"
    return outcome, ""


def main() -> None:
    key = Key().anthropic_api_key
    if not key:
        raise SystemExit("Put ANTHROPIC_API_KEY in tests/acceptance/atp3/.env first.")
    with (RESULTS / "turns.csv").open(encoding="utf-8", newline="") as file:
        turns = list(csv.DictReader(file))
    with (RESULTS / "calls.csv").open(encoding="utf-8", newline="") as file:
        spent = sum(float(call["cost"]) for call in csv.DictReader(file))
    prompts = {row["id"]: row for row in read_prompts()}
    resolved = read_resolved()
    rules, rulebook = stores()
    states = {
        code: prepared(code, rules, rulebook)
        for code in dict.fromkeys(row["student"] for row in prompts.values())
    }
    CACHE.mkdir(exist_ok=True)
    client = anthropic.Anthropic(api_key=key)

    def mark(turn: Row) -> Row:
        prompt, fixed = prompts[turn["prompt"]], resolved[turn["prompt"]]
        answerable = fixed["expected"] in ANSWERABLE
        if turn["error"]:
            # Nothing reached her to judge, so it counts against the arm
            return {**ids(turn), "outcome": "unavailable", "rule": "error"}
        saved = asked(client, request(case(prompt, fixed, turn)))
        judge = judged(saved)
        course = judge.validity_course.strip().upper()
        engine = (
            verdict(states[prompt["student"]], rulebook, course)
            if CODE.match(course)
            else None
        )
        fitting = (
            [plan["plan"] for plan in json.loads(fixed["data"])["plans"]]
            if fixed["kind"] == "find_plan"
            else None
        )
        outcome, rule = final(
            turn, answerable, judge, engine.status if engine else None, fitting
        )
        usage = saved["message"]["usage"]
        # A mark counts once, and only on a citation the reply has
        positions = {c["position"] for c in json.loads(turn["citations"] or "[]")}
        supported = {m.position for m in judge.citations if m.supports} & positions
        return {
            **ids(turn),
            "judge_outcome": judge.outcome,
            "validity_claim": judge.validity_claim,
            "validity_course": course,
            "engine_verdict": engine.status if engine else "",
            "marks": as_json([m.model_dump() for m in judge.citations]),
            "cited": str(len(positions)),
            "supported": str(len(supported)),
            "reason": judge.reason,
            "outcome": outcome,
            "rule": rule,
            "judge_seconds": f"{saved['seconds']:.3f}",
            "judge_input_tokens": str(usage["input_tokens"]),
            "judge_output_tokens": str(usage["output_tokens"]),
            "judge_cost": f"{cost(usage):.6f}",
            "key": saved["key"],
        }

    rows = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(mark, turn) for turn in turns]
        for future in as_completed(futures):
            # A crash stops the queue at once, so it spends nothing more
            if future.exception() is not None:
                pool.shutdown(cancel_futures=True)
            rows.append(future.result())
            total = spent + sum(float(row.get("judge_cost") or 0) for row in rows)
            if total > BUDGET:
                pool.shutdown(cancel_futures=True)
                raise SystemExit(
                    f"Stopped: the run has spent USD {total:.4f}, over USD {BUDGET}"
                )
            if len(rows) % 25 == 0 or len(rows) == len(turns):
                print(f"{len(rows)} of {len(turns)} judged, USD {total:.4f} in all")
    rows.sort(key=lambda row: (row["arm"], row["prompt"], int(row["try"])))
    write("judge", COLUMNS, rows)


def ids(turn: Row) -> Row:
    return {key: turn[key] for key in ("turn", "arm", "prompt", "try")}


if __name__ == "__main__":
    main()
