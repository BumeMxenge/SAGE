# ATP-4's four checks, run by run, from what drive.mjs saw: results/observations.json for the
# scenarios as built and results/planted.json for the planted fault, written to results/runs.csv.
# Every question carries its run's id, and every reply names that id and the plan or pair of the chat
# the advisor was handed, so each check reads the run's own exchanges and nothing else.
import csv
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

RESULTS = Path(__file__).parent / "results"
ASKED = re.compile(r"\[(S\d-\d{2}-\d)\]")
ANSWERED = re.compile(r"(S\d-\d{2}-\d) answered for (.+)$")
# What a screen reader hears before each message, which the API doesn't store
SPOKEN = re.compile(r"^(You asked|SAGE replied): ")
CHECKS = (
    "in_right_chat",
    "exchanges_once",
    "address_matches_chat",
    "plan_set_unchanged",
)
COLUMNS = (
    "scenario",
    "run",
    "planted",
    "delay",
    "switch_at",
    "race",
    *CHECKS,
    "consistent",
)

Run = dict[str, Any]
Scope = frozenset[str]
Part = tuple[str, str]


def scope(plan_id: str, other_plan_id: str | None) -> Scope:
    return frozenset(plan for plan in (plan_id, other_plan_id) if plan)


def address_scope(address: str) -> Scope:
    # /plan/<id> opens one plan, and ?compare=<id> puts a second beside it
    path, _, query = address.partition("?")
    fields = dict(part.split("=", 1) for part in query.split("&") if "=" in part)
    return scope(path.removeprefix("/plan/"), fields.get("compare"))


def chat_scope(chat: dict[str, Any]) -> Scope:
    return scope(chat["plan_id"], chat["other_plan_id"])


def names(run: Run, where: Scope) -> frozenset[str]:
    return frozenset(run["plans"][plan] for plan in where)


def ours(run: Run, question: str) -> bool:
    return question.startswith(f"{run['scenario']}-{run['run']:02d}-")


def parts(run: Run, texts: Iterable[str]) -> list[Part]:
    # This run's messages, in order, each as a question or a reply with its question's id
    found = []
    for text in texts:
        reply, question = ANSWERED.search(text), ASKED.search(text)
        if reply and ours(run, reply.group(1)):
            found.append(("reply", reply.group(1)))
        elif question and ours(run, question.group(1)):
            found.append(("question", question.group(1)))
    return found


def asked(run: Run, where: Scope) -> list[Part]:
    # The exchanges this run asked in a plan or pair, in order, each once
    return [
        part
        for ask in run["asked"]
        if scope(ask["plan_id"], ask["other_plan_id"]) == where
        for part in (("question", ask["question"]), ("reply", ask["question"]))
    ]


def contents(chat: dict[str, Any]) -> list[str]:
    return [message["content"] for message in chat["messages"]]


def in_right_chat(run: Run) -> bool:
    # Each reply sits in a chat, and on a screen, of the plan or pair it names
    placed = [(chat_scope(chat), contents(chat)) for chat in run["chats"]]
    placed += [
        (address_scope(view["address"]), view["messages"]) for view in run["views"]
    ]
    for where, texts in placed:
        for text in texts:
            reply = ANSWERED.search(text)
            if (
                reply
                and ours(run, reply.group(1))
                and frozenset(reply.group(2).split(" | ")) != names(run, where)
            ):
                return False
    return True


def exchanges_once(run: Run) -> bool:
    # Each question sits in one chat, and a chat holds exactly the exchanges asked in it, once each,
    # or none of this run's. A screen shows the chat the rail opens: the run's own where it asked,
    # holding its exchanges whether reloaded or not, and elsewhere one holding none of them.
    held = [(chat_scope(chat), parts(run, contents(chat))) for chat in run["chats"]]
    for ask in run["asked"]:
        if sum(("question", ask["question"]) in found for _, found in held) != 1:
            return False
    if any(found and found != asked(run, where) for where, found in held):
        return False
    for view in run["views"]:
        where = address_scope(view["address"])
        if parts(run, view["messages"]) != asked(run, where):
            return False
    return True


def header(run: Run, where: Scope) -> set[str]:
    # The rail's line under its title, in either order for a pair
    plans = sorted(names(run, where))
    if len(plans) == 1:
        return {f"Reading {plans[0]}"}
    return {
        f"Comparing {plans[0]} and {plans[1]}",
        f"Comparing {plans[1]} and {plans[0]}",
    }


def address_matches_chat(run: Run) -> bool:
    # The rail names the plan or pair in the address, and the chat it shows is one of theirs
    for view in run["views"]:
        where = address_scope(view["address"])
        if view["header"] not in header(run, where):
            return False
        if not view["messages"]:
            continue
        words = [SPOKEN.sub("", text) for text in view["messages"]]
        matching = [chat for chat in run["chats"] if contents(chat) == words]
        if not matching or any(chat_scope(chat) != where for chat in matching):
            return False
    return True


def plan_set_unchanged(run: Run) -> bool:
    # Her plans as they were, except that a hidden plan a reply offered joins the shown list
    before = {plan["id"]: plan["hidden"] for plan in run["plans_before"]}
    after = {plan["id"]: plan["hidden"] for plan in run["plans_after"]}
    if run["offered"]:
        before[run["offered"]] = False
    return before == after


CHECKERS = {
    "in_right_chat": in_right_chat,
    "exchanges_once": exchanges_once,
    "address_matches_chat": address_matches_chat,
    "plan_set_unchanged": plan_set_unchanged,
}


def row(run: Run) -> dict[str, str]:
    passed = {name: checker(run) for name, checker in CHECKERS.items()}
    return {
        "scenario": run["scenario"],
        "run": str(run["run"]),
        "planted": "yes" if run["planted"] else "no",
        "delay": f"{run['delay']:.1f}",
        "switch_at": "" if run["switch_at"] is None else f"{run['switch_at']:.1f}",
        "race": "yes" if run["race"] else "no",
        **{name: "pass" if ok else "fail" for name, ok in passed.items()},
        "consistent": "yes" if all(passed.values()) else "no",
    }


def main() -> None:
    runs = []
    for name in ("observations", "planted"):
        runs += json.loads((RESULTS / f"{name}.json").read_text(encoding="utf-8"))
    with (RESULTS / "runs.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(row(run) for run in runs)
    print(f"results/runs.csv: {len(runs)} runs")


if __name__ == "__main__":
    main()
