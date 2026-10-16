# Scores E2's arms on the labelled validation strings, then prints the three tables Chapter 3 needs,
# each with its verdict, and writes them to results/ as CSVs and tables.md. Every model reply comes
# from the cache, so scoring never calls a provider: run drafting.py first.
import csv
import json
import re
import time
from collections import Counter
from math import comb
from typing import get_args

from pydantic import TypeAdapter, ValidationError
from sage.domain.rules import EntryRule, RefusalCause
from sage.ingestion.grammar import Refused, read

from drafting import (
    HAIKU,
    LUNA,
    MODELS,
    REPLIES,
    RUNS,
    answer,
    digest,
    key,
    reply,
    request,
    tokens,
)
from extract import HERE, labels, wording

RESULTS = HERE.parent / "results"
TREE = TypeAdapter(EntryRule | None)
REFER = json.dumps({"refer": ""})
# Every node a label can hold, in table 3's order. A refer asking for a DP is also counted as a refer.
KINDS = (
    "all",
    "any",
    "course, need pass",
    "course, need concurrent",
    "course, need mark",
    "student_in",
    "min_year_of_study",
    "refer",
    "refer asking for a DP",
    "no rule (null)",
)


def upper_bound(n: int) -> float:
    # The one-sided 95% upper bound on the error rate when none of n strings is wrong
    return 1 - 0.05 ** (1 / n)


def mcnemar(b: int, c: int) -> float:
    # McNemar's exact two-sided p: how likely a split between the two kinds of disagreement at
    # least this lopsided is, if each disagreement were a coin toss
    n = b + c
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2**n)


def canonical(tree: object) -> dict | None:
    # A tree in the types' own JSON, which drops an absent min_mark. One that doesn't fit EntryRule
    # raises ValidationError.
    return TREE.dump_python(TREE.validate_python(tree), mode="json")


def normal(tree: dict | None) -> dict | None:
    # One form per meaning, for comparing trees. A refer leaf loses its wording, as the engine treats
    # every refer alike. An all inside an all, or an any inside an any, is spliced in, repeated
    # children merge, an all or an any with one child becomes that child, and the rest is sorted.
    if tree is None or "course" in tree or "min_year_of_study" in tree:
        return tree
    if "refer" in tree:
        return {"refer": ""}
    if "student_in" in tree:
        return {"student_in": sorted(set(tree["student_in"]))}
    join = "all" if "all" in tree else "any"
    children = {}
    for child in map(normal, tree[join]):
        for part in child.get(join, [child]):
            children[json.dumps(part, sort_keys=True)] = part
    if len(children) == 1:
        return next(iter(children.values()))
    return {join: [children[text] for text in sorted(children)]}


def leaves(tree: dict | None) -> Counter:
    # A tree's leaves, each as its JSON
    if tree is None:
        return Counter()
    if "all" in tree or "any" in tree:
        return sum(map(leaves, tree.get("all") or tree["any"]), Counter())
    return Counter([json.dumps(tree, sort_keys=True)])


def to_correct(draft: dict | None, label: dict | None) -> int:
    # The leaves a person must fix in a wrong draft: those in one tree but not the other, counted
    # both ways, and at least one, as a wrong draft always needs a correction
    theirs, ours = leaves(draft), leaves(label)
    return max(1, sum((theirs - ours + (ours - theirs)).values()))


def outcome(tree: dict | None, label: dict | None, valid: bool = True) -> tuple:
    # What storing a tree unseen means for one string: whether a rule is stored, whether it's wrong,
    # whether a person is needed, and the leaves that person must type. A reply that doesn't fit, or
    # a refer at the root, leaves the whole rule to a person.
    if not valid or (tree is not None and "refer" in tree):
        return False, False, True, sum(leaves(label).values())
    return True, tree != label, REFER in leaves(tree), 0


def cached(model: str, field: str, text: str, run: int) -> dict:
    # A cached reply, refused if its request has changed since it was made

    def missing(body: dict) -> dict:
        raise SystemExit(
            f"No {model} reply for {key(field, text)}-{run}: run drafting.py"
        )

    entry = reply(model, field, text, run, REPLIES, missing)
    if entry["request"] != digest(request(model, field, text)):
        raise SystemExit(
            f"{model}'s reply {key(field, text)}-{run} answers an older request: "
            "delete it and run drafting.py"
        )
    return entry


def drafted(model: str, entry: dict) -> tuple[bool, dict | None]:
    # Whether a reply gave a tree that fits EntryRule, and that tree in normal form. A refusal or a
    # reply cut short gives none.
    text = answer(model, entry["reply"])
    if text is None:
        return False, None
    try:
        return True, normal(canonical(json.loads(text)["rule"]))
    except (json.JSONDecodeError, ValidationError):
        return False, None


def cost(model: str, entry: dict) -> float:
    # A reply's price in USD
    _, full, from_cache, written = MODELS[model]
    fresh, cached_in, out = tokens(model, entry["reply"])
    return (fresh * full + cached_in * from_cache + out * written) / 1e6


def score(row: dict[str, str]) -> dict:
    # One string's label, what the grammar made of it, and each model's three runs
    field, text = row["field"], wording(row)
    label = normal(canonical(json.loads(row["tree"])))
    start = time.perf_counter()
    try:
        need = "concurrent" if field == "Co-requisites" else "pass"
        grammar, cause = normal(canonical(read(text, need))), None
    except Refused as refused:
        grammar, cause = None, refused.cause
    seconds = time.perf_counter() - start
    models = {}
    for model in MODELS:
        entries = [cached(model, field, text, run) for run in range(1, RUNS + 1)]
        runs = [drafted(model, entry) for entry in entries]
        valid, tree = runs[0]
        right = valid and tree == label
        if right:
            fix = 0
        elif valid:
            fix = to_correct(tree, label)
        else:
            fix = sum(leaves(label).values())
        models[model] = {
            "valid": valid,
            "tree": tree,
            "right": right,
            "same": valid and all(run == runs[0] for run in runs),
            "fix": fix,
            "cost": cost(model, entries[0]),
            "seconds": entries[0]["seconds"],
        }
    return {
        "row": row,
        "label": label,
        "grammar": grammar,
        "cause": cause,
        "grammar_seconds": seconds,
        "models": models,
    }


def arms(strings: list[dict]) -> list[dict]:
    # Each arm's measures, in table 1's order. The hybrid arms draft only the grammar's refusals,
    # with the same replies the model-only arms store.
    refused = [string for string in strings if string["cause"]]
    found = []

    def measure(name, outcomes, handled=(), reproducible=True, model=None) -> None:
        stored, wrong, person, typing = (
            sum(column) for column in zip(*outcomes, strict=True)
        )
        found.append(
            {
                "name": name,
                "stored": stored,
                "wrong": wrong,
                "person": person,
                "typing": typing,
                "right": sum(s["models"][model]["right"] for s in handled)
                if model
                else None,
                "same": sum(s["models"][model]["same"] for s in handled)
                if model
                else None,
                "handled": len(handled),
                "reproducible": reproducible,
                "cost": sum(s["models"][model]["cost"] for s in handled)
                if model
                else 0.0,
                "seconds": sum(s["models"][model]["seconds"] for s in handled)
                if model
                else sum(s["grammar_seconds"] for s in strings),
            }
        )

    def grammar_first(string: dict, draft: tuple | None) -> tuple:
        # A parse is stored unseen; a refusal is a referral, or a draft a person reviews
        if not string["cause"]:
            return outcome(string["grammar"], string["label"])
        if draft is None:
            return outcome({"refer": ""}, string["label"])
        return False, False, True, draft["fix"]

    measure("Grammar only", [grammar_first(s, None) for s in strings])
    for model, (name, *_) in MODELS.items():
        runs = [s["models"][model] for s in strings]
        measure(
            f"Model only: {name}",
            [
                outcome(r["tree"], s["label"], r["valid"])
                for r, s in zip(runs, strings, strict=True)
            ],
            strings,
            all(r["same"] for r in runs),
            model,
        )
    for model, (name, *_) in MODELS.items():
        measure(
            f"Grammar first, {name} drafts",
            [grammar_first(s, s["models"][model]) for s in strings],
            refused,
            model=model,
        )
    return found


def percent(part: int, whole: int) -> str:
    return f"{part / whole:.1%}" if whole else "none"


def arms_table(found: list[dict]) -> tuple[list[str], list[list], list[str]]:
    # Table 1, and its verdict: the plan's rule applied in order
    header = [
        "Arm",
        "Stored unseen",
        "Wrong unseen",
        "Needing a person",
        "Leaves to type or fix",
        "Model right first time",
        "Model same on 3 runs",
        "Cost per pass (USD)",
        "Time per pass (s)",
    ]
    rows = []
    for arm in found:
        if arm["wrong"]:
            wrong = f"{arm['wrong']} ({percent(arm['wrong'], arm['stored'])})"
        else:
            wrong = (
                f"0 (below {upper_bound(arm['stored']):.1%})" if arm["stored"] else "0"
            )
        handled = arm["handled"]
        rows.append(
            [
                arm["name"],
                arm["stored"],
                wrong,
                arm["person"],
                arm["typing"],
                f"{arm['right']} of {handled}" if arm["right"] is not None else "",
                f"{arm['same']} of {handled}" if arm["same"] is not None else "",
                f"{arm['cost']:.4f}",
                f"{arm['seconds']:.1f}",
            ]
        )

    def names(arms: list[dict]) -> str:
        # Semicolons, as an arm's name can hold a comma
        return "; ".join(arm["name"] for arm in arms) or "none"

    first = [arm for arm in found if not arm["wrong"]]
    second = [arm for arm in first if arm["reproducible"]]
    verdict = [
        f"Rule 1, no wrong rule stored unseen: {names(first)}.",
        f"Rule 2, whatever is stored unseen is the same on every run: {names(second)}.",
    ]
    if second:
        fewest = min((arm["person"], arm["typing"]) for arm in second)
        third = [arm for arm in second if (arm["person"], arm["typing"]) == fewest]
        verdict.append(
            "Rule 3, fewest strings needing a person, then fewest leaves to type or fix: "
            f"{names(third)}, with {fewest[0]} strings and {fewest[1]} leaves."
        )
        cheapest = min(arm["cost"] for arm in third)
        fourth = [arm for arm in third if arm["cost"] == cheapest]
        if len(third) > 1:
            verdict.append(f"Rule 4, lowest cost: {names(fourth)}.")
        verdict.append(f"Verdict: {names(fourth)}.")
    else:
        verdict.append("Verdict: no arm passes the first two rules.")
    for arm in second:
        if arm["name"].startswith("Model only"):
            verdict.append(
                f"{arm['name']} passes the first two rules on these strings. A model's error is "
                "silent and can change when the provider updates the model, while a grammar's "
                "refusal is visible, so choosing grammar first over it rests on that argument."
            )
    return header, rows, verdict


def drafting_verdict(strings: list[dict]) -> list[str]:
    # The provisional drafting model for C1, with McNemar's test on the refusals as a finding
    refused = [s for s in strings if s["cause"]]
    right = {m: sum(s["models"][m]["right"] for s in refused) for m in MODELS}
    fix = {m: sum(s["models"][m]["fix"] for s in refused) for m in MODELS}
    b = sum(
        s["models"][HAIKU]["right"] and not s["models"][LUNA]["right"] for s in refused
    )
    c = sum(
        s["models"][LUNA]["right"] and not s["models"][HAIKU]["right"] for s in refused
    )
    p = mcnemar(b, c)
    name = {model: MODELS[model][0] for model in MODELS}
    ranked = sorted(MODELS, key=lambda m: (-right[m], fix[m]))
    if (right[HAIKU], fix[HAIKU]) == (right[LUNA], fix[LUNA]):
        pick = "a tie on both, so it goes to the account I keep"
    else:
        pick = name[ranked[0]]
    lines = [
        (
            f"Drafting model, provisional for C1 until the advisor milestone: {pick}. On their "
            f"first runs over the {len(refused)} refusals, {name[HAIKU]} drafted {right[HAIKU]} "
            f"exactly right with {fix[HAIKU]} leaves to correct, and {name[LUNA]} "
            f"{right[LUNA]} with {fix[LUNA]}."
        ),
        f"McNemar's exact test, a finding rather than a decision: {b} refusals only "
        f"{name[HAIKU]} drafted right and {c} only {name[LUNA]}, p = {p:.3f}. "
        + (
            "It can't separate the models."
            if p >= 0.05
            else "A split this lopsided is unlikely by chance."
        ),
    ]
    return lines


def refusals_table(strings: list[dict]) -> tuple[list[str], list[list], list[str]]:
    # Table 2: refusals by the grammar's ten causes, on the development fields as development
    # evidence and on the validation strings, with how often each model drafted them right
    development = Counter()
    with (HERE / "data" / "development.csv").open(encoding="utf-8", newline="") as file:
        fields = list(csv.DictReader(file))
    for field in fields:
        try:
            read(
                field["text"],
                "concurrent" if field["field"] == "Co-requisites" else "pass",
            )
        except Refused as refused:
            development[refused.cause] += 1
    validation = Counter(s["cause"] for s in strings if s["cause"])
    right = {
        model: Counter(
            s["cause"] for s in strings if s["cause"] and s["models"][model]["right"]
        )
        for model in MODELS
    }
    header = [
        "Cause",
        f"Development (of {len(fields)})",
        f"Validation (of {len(strings)})",
        *(f"{name} drafts right" for name, *_ in MODELS.values()),
    ]
    rows = [
        [
            cause,
            development[cause],
            validation[cause],
            *(right[m][cause] for m in MODELS),
        ]
        for cause in get_args(RefusalCause)
    ]
    totals = [
        development.total(),
        validation.total(),
        *(right[m].total() for m in MODELS),
    ]
    rows.append(["All refusals", *totals])
    read_here = len(strings) - validation.total()
    top = validation.most_common(1)
    verdict = [
        f"The grammar reads {read_here} of the {len(strings)} validation strings "
        f"({percent(read_here, len(strings))}) and refuses {validation.total()}"
        + (f", most for {top[0][0]} ({top[0][1]})." if top else "."),
        (
            f"Development evidence only: it reads {len(fields) - development.total()} of the "
            f"{len(fields)} fields it was written from "
            f"({percent(len(fields) - development.total(), len(fields))})."
        ),
    ]
    return header, rows, verdict


def kinds(tree: dict | None) -> list[str]:
    # Every node of a label by its kind, a refer asking for a DP counted twice
    if tree is None:
        return ["no rule (null)"]
    for join in ("all", "any"):
        if join in tree:
            return [join] + [kind for child in tree[join] for kind in kinds(child)]
    if "course" in tree:
        return [f"course, need {tree['need']}"]
    if "refer" in tree:
        return ["refer"] + (
            ["refer asking for a DP"] if re.search(r"\bDP\b", tree["refer"]) else []
        )
    return [next(iter(tree))]


def leaves_table(strings: list[dict]) -> tuple[list[str], list[list], list[str]]:
    # Table 3: the node kinds the labels use, Chapter 3's evidence for the representation
    found = [kinds(canonical(json.loads(s["row"]["tree"]))) for s in strings]
    nodes = Counter(kind for label in found for kind in label)
    using = Counter(kind for label in found for kind in set(label))
    header = ["Node", "Strings using it", "Nodes in the labels"]
    rows = [[kind, using[kind], nodes[kind]] for kind in KINDS]
    verdict = [
        (
            f"Every one of the {len(strings)} labels fits the CP0 node types. "
            f"{using['refer']} strings ({percent(using['refer'], len(strings))}) need a refer "
            f"leaf, and {using['refer asking for a DP']} of them ask for a DP, the first leaf "
            "SAGE would need for another department."
        )
    ]
    return header, rows, verdict


def outcomes(strings: list[dict]) -> tuple[list[str], list[list]]:
    # Every string's result under each model, to look into what went wrong
    header = ["code", "field", "text", "grammar"]
    for name, *_ in MODELS.values():
        header += [f"{name} run 1", f"{name} same on 3 runs", f"{name} leaves to fix"]
    rows = []
    for s in strings:
        row = [
            s["row"]["code"],
            s["row"]["field"],
            wording(s["row"]),
            s["cause"] or "read",
        ]
        for model in MODELS:
            run = s["models"][model]
            if not run["valid"]:
                result = "no valid reply"
            else:
                result = "right" if run["right"] else "wrong"
            row += [result, "yes" if run["same"] else "no", run["fix"]]
        rows.append(row)
    return header, rows


def markdown(header: list[str], rows: list[list]) -> str:
    lines = [header, ["---"] * len(header), *rows]
    return "\n".join("| " + " | ".join(map(str, line)) + " |" for line in lines)


def write(name: str, header: list[str], rows: list[list]) -> None:
    with (RESULTS / name).open("w", encoding="utf-8", newline="") as file:
        csv.writer(file, lineterminator="\n").writerows([header, *rows])


if __name__ == "__main__":
    strings = [score(row) for row in labels()]
    header, rows, verdict = arms_table(arms(strings))
    tables = [
        ("arms.csv", "1. The arms", header, rows, verdict + drafting_verdict(strings)),
        (
            "refusals.csv",
            "2. Refusals by the grammar's ten causes",
            *refusals_table(strings),
        ),
        ("leaves.csv", "3. Node kinds in the labels", *leaves_table(strings)),
    ]
    report = [
        f"# E2 results\n\nFrom score.py, on {len(strings)} labelled validation strings."
    ]
    for name, title, header, rows, verdict in tables:
        write(name, header, rows)
        report.append(
            f"## {title}\n\n{markdown(header, rows)}\n\n" + "\n".join(verdict)
        )
    write("outcomes.csv", *outcomes(strings))
    text = "\n\n".join(report) + "\n"
    (RESULTS / "tables.md").write_text(text, encoding="utf-8")
    print(text)
