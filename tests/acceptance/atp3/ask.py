# Runs ATP-3's two arms and records every turn. The SAGE arm asks the advisor as merged, each prompt
# three times, each in a fresh chat. The control arm asks the same model, with no tools, passages,
# plans or checks, the prompts marked for it, three times each. Both share one queue, shuffled with
# a fixed seed so no group of prompts runs together, and four turns run at a time. A timing wrapper
# around the one client times every call and saves each request body before it's sent, for ATP-6.
# make atp3 runs it from backend/, then judge.py. It costs money, so it stops past the budget, and
# it asks nothing once turns.csv is complete.
import csv
import hashlib
import itertools
import json
import random
import shutil
import threading
import time
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ask_advisor import Recorded
from resolve import RESULTS, Row, read_prompts, read_resolved
from show_plans import ACCOUNT
from students import HERE, YEAR, prepared, short_ids, store, stores

from sage.advisor.checks import REFERRAL
from sage.advisor.replies import GroundedAdvisor, answer_in
from sage.config import get_settings
from sage.engine.eligibility import EntryRuleEligibility
from sage.engine.evaluator import Record
from sage.features.chats import service as chats
from sage.shared.errors import AdvisorUnavailable
from sage.shared.language_model import (
    ModelUnavailable,
    Response,
    Said,
    Schema,
    Tokens,
    Tool,
    ToolResult,
)
from sage.shared.openai import MODEL, OpenAIModel
from sage.shared.rulebook import Rulebook
from sage.shared.students import StudentState

SEED = 4022
TRIES = 3
WORKERS = 4
BUDGET = 5.0  # USD across OpenAI and Anthropic, past which the run stops
REQUESTS = RESULTS / "requests"
# Everything in control_prompt.md after its note for people
CONTROL = (
    (HERE / "control_prompt.md")
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
TURNS = (
    "turn",
    "arm",
    "prompt",
    "student",
    "try",
    "order",
    "plans",
    "term",
    "reply",
    "referral",
    "fixed",
    "why_fixed",
    "offered",
    "offered_courses",
    "offered_hidden",
    "citations",
    "dropped",
    "unoffered",
    "flags",
    "title",
    "title_ready",
    "calls",
    "fresh",
    "cached",
    "written",
    "output",
    "cost",
    "seconds",
    "tools",
    "error",
)
CALLS = (
    "turn",
    "call",
    "kind",
    "seconds",
    "fresh",
    "cached",
    "written",
    "output",
    "cost",
)
# The name the calling thread's next request body is saved under
sending = threading.local()


@dataclass(frozen=True)
class Call:
    turn: str
    number: int
    kind: str  # reply or title for the SAGE arm, control for the control arm
    seconds: float
    tokens: Tokens


class Log:
    # Every model call from every thread, and how many are still on their way, so the run can wait
    # for a title call that outlives its turn before it writes
    def __init__(self, model: OpenAIModel) -> None:
        self.model = model
        self.calls: list[Call] = []
        self.waiting = 0
        self.lock = threading.Lock()

    def spent(self) -> float:
        return sum(self.model.cost(call.tokens) for call in list(self.calls))


class Timed:
    # The one shared client as one turn sees it: each call numbered, timed and logged, its body saved
    # under the turn's name by the client's capture
    def __init__(self, inner: OpenAIModel, turn: str, log: Log) -> None:
        self.inner = inner
        self.model = inner.model
        self.turn = turn
        self.log = log
        self.numbers = itertools.count(1)

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Said | Response | ToolResult],
        schema: Schema | None = None,
        tools: Sequence[Tool] = (),
        effort: str | None = None,
    ) -> Response:
        number = next(self.numbers)
        sending.name = f"{self.turn}-{number}"
        with self.log.lock:
            self.log.waiting += 1
        started = time.monotonic()
        try:
            response = self.inner.respond(
                instructions, conversation, schema, tools, effort
            )
            kind = schema.name if schema else "control"
            self.log.calls.append(
                Call(
                    self.turn,
                    number,
                    kind,
                    time.monotonic() - started,
                    response.tokens,
                )
            )
        finally:
            with self.log.lock:
                self.log.waiting -= 1
        return response


def capture(client: Any, folder: Path) -> None:
    # Saves each request body before it's sent, under the name its thread gave it: the body alone, as
    # OpenAIModel builds it, so no header or key is ever written
    create = client.responses.create

    def saved(**body: Any) -> Any:
        (folder / f"{sending.name}.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        return create(**body)

    client.responses.create = saved


def about(state: StudentState, rulebook: Rulebook) -> str:
    # The control arm's view of her: curriculum, year of study as the engine reads it, and record
    rules = rulebook.year(YEAR)
    student = state.student
    curriculum = next(
        row for row in rules.curricula if row.code == student.curriculum_code
    )
    year = Record(student, state.course_history, rules, rulebook.symbols()).year
    lines = [
        f"- {line.academic_year}, {line.term}: {line.course_code} {line.course_name}, "
        f"{line.credits} credits, "
        + (f"{line.mark}%, " if line.mark is not None else "")
        + line.result
        for line in sorted(
            state.course_history,
            key=lambda line: (line.academic_year, line.term, line.course_code),
        )
    ]
    return "\n".join(
        [
            "About the student",
            f"- Curriculum: {curriculum.code}, {curriculum.name}",
            f"- Year of study in {YEAR}: {year}",
            "",
            "Course record",
            *lines,
        ]
    )


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def sage_turn(
    row: Row,
    attempt: int,
    plans: Sequence[str],
    state: StudentState,
    rulebook: Rulebook,
    model: OpenAIModel,
    log: Log,
) -> Row:
    turn = f"sage-{row['id']}-{attempt}"
    students = store(state)
    keys = short_ids(state)
    ids = [keys[key].id for key in plans]
    chat = chats.start(students, ACCOUNT, ids[0], ids[1] if len(ids) == 2 else None)
    advisor = Recorded(
        GroundedAdvisor(
            Timed(model, turn, log), students, rulebook, EntryRuleEligibility()
        )
    )
    found: Row = {"turn": turn, "plans": " ".join(plans)}
    started = time.monotonic()
    try:
        chats.ask(students, advisor, ACCOUNT, chat.id, row["prompt"], row["term"])
    except AdvisorUnavailable:
        # The one failure SAGE shows her as a refusal: it counts against the arm, not as an answer
        return {
            **found,
            "seconds": f"{time.monotonic() - started:.3f}",
            "error": "advisor_unavailable",
        }
    answered = advisor.last
    reply, checked, done = answered.reply, answered.checked, answered.turn
    passages = {passage.id: passage for passage in rulebook.year(YEAR).passages}
    fixed = reply.content == REFERRAL
    why = ""
    if fixed:
        given = answer_in(done.responses[-1])
        why = given if isinstance(given, str) else "every quote dropped"
    offered = next(
        (key for key, plan in keys.items() if plan.id == reply.open_plan_id), ""
    )
    return {
        **found,
        "reply": reply.content,
        "referral": "yes" if reply.referral else "no",
        "fixed": "yes" if fixed else "no",
        "why_fixed": why,
        "offered": offered,
        "offered_courses": " ".join(
            sorted(
                course.course_code
                for course in state.plan_courses
                if offered and course.plan_id == keys[offered].id
            )
        ),
        # Whether her answers had hidden it, before this turn's reply showed it
        "offered_hidden": ("yes" if keys[offered].hidden else "no") if offered else "",
        "citations": as_json(
            [
                {
                    "position": citation.position,
                    "passage_id": str(citation.passage_id),
                    "section": citation.section,
                    "page": citation.page,
                    "quote": citation.quote,
                    "text": passages[citation.passage_id].content,
                }
                for citation in reply.citations
            ]
        ),
        "dropped": as_json([quote.model_dump() for quote in checked.dropped]),
        "unoffered": checked.unoffered or "",
        "flags": as_json([flag.model_dump() for flag in checked.flags]),
        "title": reply.title or "",
        "title_ready": "yes" if answered.named is not None else "no",
        "calls": str(len(done.responses)),
        "seconds": f"{answered.seconds:.3f}",
        "tools": as_json(
            [
                {"name": c.name, "arguments": c.arguments, "result": c.result}
                for c in done.called
            ]
        ),
        "error": "",
    }


def control_turn(
    row: Row,
    attempt: int,
    state: StudentState,
    rulebook: Rulebook,
    model: OpenAIModel,
    log: Log,
) -> Row:
    turn = f"control-{row['id']}-{attempt}"
    asked = f"{about(state, rulebook)}\n\nQuestion\n{row['prompt']}"
    started = time.monotonic()
    try:
        response = Timed(model, turn, log).respond(
            CONTROL, [Said(role="user", text=asked)]
        )
    except ModelUnavailable:
        return {
            "turn": turn,
            "seconds": f"{time.monotonic() - started:.3f}",
            "error": "model_unavailable",
        }
    return {
        "turn": turn,
        "reply": response.text or "",
        "calls": "1",
        "seconds": f"{time.monotonic() - started:.3f}",
        "error": "" if response.text is not None else "cut off",
    }


def write(name: str, columns: Sequence[str], rows: Iterable[Row]) -> None:
    rows = list(rows)
    with (RESULTS / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"results/{name}.csv: {len(rows)} rows")


def costed(turns: list[Row], log: Log) -> None:
    # Each turn's tokens and cost from every call it made, its late title call included
    by_turn: dict[str, Tokens] = {}
    for call in log.calls:
        by_turn[call.turn] = by_turn.get(call.turn, Tokens()) + call.tokens
    for turn in turns:
        tokens = by_turn.get(turn["turn"], Tokens())
        turn.update(
            {field: str(getattr(tokens, field)) for field in Tokens.model_fields}
        )
        turn["cost"] = f"{log.model.cost(tokens):.6f}"


def requests_rows() -> list[Row]:
    # Every body saved, which git leaves out, by its name, size and SHA-256
    rows = []
    for path in sorted(REQUESTS.glob("*.json")):
        turn, _, call = path.stem.rpartition("-")
        content = path.read_bytes()
        rows.append(
            {
                "turn": turn,
                "call": call,
                "file": path.name,
                "bytes": str(len(content)),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return rows


def main() -> None:
    if (RESULTS / "turns.csv").exists():
        print("results/turns.csv is complete, so ask.py asks nothing again")
        return
    settings = get_settings()
    if not settings.openai_api_key:
        raise SystemExit("Set OPENAI_API_KEY in backend/.env first.")
    prompts = read_prompts()
    resolved = read_resolved()
    rules, rulebook = stores()
    states = {
        code: prepared(code, rules, rulebook)
        for code in dict.fromkeys(row["student"] for row in prompts)
    }
    model = OpenAIModel(settings.openai_api_key, MODEL)
    if REQUESTS.exists():
        shutil.rmtree(REQUESTS)
    REQUESTS.mkdir(parents=True)
    capture(model.client, REQUESTS)
    log = Log(model)
    queue = [
        ("sage", row, attempt) for row in prompts for attempt in range(1, TRIES + 1)
    ]
    queue += [
        ("control", row, attempt)
        for row in prompts
        if row["control_arm"] == "yes"
        for attempt in range(1, TRIES + 1)
    ]
    random.Random(SEED).shuffle(queue)

    def ask(order: int, arm: str, row: Row, attempt: int) -> Row:
        state = states[row["student"]]
        if arm == "sage":
            plans = resolved[row["id"]]["plans"].split()
            found = sage_turn(row, attempt, plans, state, rulebook, model, log)
        else:
            found = control_turn(row, attempt, state, rulebook, model, log)
        return {
            **found,
            "arm": arm,
            "prompt": row["id"],
            "student": row["student"],
            "try": str(attempt),
            "order": str(order),
            "term": row["term"],
        }

    turns = []
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [
            pool.submit(ask, order, arm, row, attempt)
            for order, (arm, row, attempt) in enumerate(queue, start=1)
        ]
        for future in as_completed(futures):
            # A crash stops the queue at once, so it spends nothing more
            if future.exception() is not None:
                pool.shutdown(cancel_futures=True)
            turns.append(future.result())
            spent = log.spent()
            if spent > BUDGET:
                pool.shutdown(cancel_futures=True)
                raise SystemExit(
                    f"Stopped: OpenAI's share alone reached USD {spent:.4f}, over the "
                    f"USD {BUDGET} budget"
                )
            if len(turns) % 10 == 0 or len(turns) == len(queue):
                print(
                    f"{len(turns)} of {len(queue)} turns, USD {spent:.4f}, "
                    f"{time.monotonic() - started:.0f} s"
                )
    # A title call can outlive its turn, and its cost counts
    while log.waiting:
        time.sleep(0.1)
    costed(turns, log)
    turns.sort(key=lambda turn: (turn["arm"], int(turn["order"])))
    write("turns", TURNS, turns)
    write(
        "calls",
        CALLS,
        (
            {
                "turn": call.turn,
                "call": str(call.number),
                "kind": call.kind,
                "seconds": f"{call.seconds:.3f}",
                **{f: str(getattr(call.tokens, f)) for f in Tokens.model_fields},
                "cost": f"{model.cost(call.tokens):.6f}",
            }
            for call in sorted(log.calls, key=lambda call: (call.turn, call.number))
        ),
    )
    write("requests", ("turn", "call", "file", "bytes", "sha256"), requests_rows())
    print(f"Asked {len(turns)} turns for USD {log.spent():.4f}")


if __name__ == "__main__":
    main()
