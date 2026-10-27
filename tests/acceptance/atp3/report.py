# Writes ATP-3's report, results/report.md, from the CSVs alone, so every number traces to their
# rows. It prints no date, so a rerun reproduces it byte for byte. make atp3-report runs it from
# backend/, after sample.py.
import csv
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from measures import cross_agreement, kappa, pair_agrees, pass_k
from resolve import ANSWERABLE, RESULTS, Row, read_prompts
from scoring import bound, wilson

TRIES = 3
OUTCOMES = (
    "correct_answer",
    "correct_referral",
    "over_referral",
    "wrong_safe",
    "unsupported",
    "unavailable",
)
ARMS = {"sage": "SAGE", "control": "Control"}
# NF-2's targets, which the verdicts hold the SAGE arm to
ANSWERED, REFERRED, SUPPORTED = 0.95, 0.90, 0.95


def load(name: str) -> list[Row]:
    with (RESULTS / f"{name}.csv").open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def percent(share: float) -> str:
    return f"{100 * share:.1f}%"


def rate(k: float, n: int) -> str:
    # k of n, its share and its 95% Wilson interval. k isn't whole for pass^1 and pass^2 at the
    # prompt level, where the interval, on n prompts, is a little conservative.
    if not n:
        return "none to count"
    low, high = wilson(k, n)
    count = f"{k:g}" if float(k).is_integer() else f"{k:.2f}"
    return f"{count} of {n}, {percent(k / n)} ({percent(low)} to {percent(high)})"


def zero_or_rate(wrong: int, n: int) -> str:
    # A count of none wrong gives the one-sided 95% upper bound instead of an interval
    if n and not wrong:
        return f"0 of {n} (95% upper bound {percent(bound(0, n))})"
    return rate(wrong, n)


def table(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    def line(cells: Sequence[object]) -> str:
        return (
            "| "
            + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells)
            + " |"
        )

    return ["", line(header), line(["---"] * len(header)), *map(line, rows)]


def listed(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    rows = list(rows)
    return table(header, rows) if rows else ["", "None."]


class Run:
    # The CSVs joined: each reply's turn, marks and prompt, and each prompt's resolved expectation
    def __init__(self) -> None:
        self.prompts = {row["id"]: row for row in read_prompts()}
        self.resolved = {row["prompt"]: row for row in load("resolved")}
        turns = {row["turn"]: row for row in load("turns")}
        self.replies = [
            {
                **turns[mark["turn"]],
                **mark,
                "group": self.resolved[mark["prompt"]]["group"],
            }
            for mark in load("judge")
        ]
        self.calls = load("calls")

    def answerable(self, prompt: str) -> bool:
        return self.resolved[prompt]["expected"] in ANSWERABLE

    def arm(self, arm: str, answerable: bool | None = None) -> list[Row]:
        return [
            reply
            for reply in self.replies
            if reply["arm"] == arm
            and (answerable is None or self.answerable(reply["prompt"]) == answerable)
        ]

    def by_prompt(self, replies: Iterable[Row]) -> dict[str, list[Row]]:
        found: dict[str, list[Row]] = defaultdict(list)
        for reply in replies:
            found[reply["prompt"]].append(reply)
        return found


def succeeded(reply: Row, answerable: bool) -> bool:
    return reply["outcome"] == ("correct_answer" if answerable else "correct_referral")


def pass_rates(run: Run, arm: str, answerable: bool) -> list[str]:
    # pass^1, pass^2 and pass^3 with the prompt as the unit, then pass^1 per reply
    prompts = run.by_prompt(run.arm(arm, answerable))
    counts = [
        sum(succeeded(r, answerable) for r in replies) for replies in prompts.values()
    ]
    n = len(counts)
    cells = [
        rate(pass_k(counts, TRIES, k) * n, n) if n else "none to count"
        for k in (1, 2, 3)
    ]
    replies = run.arm(arm, answerable)
    cells.append(rate(sum(succeeded(r, answerable) for r in replies), len(replies)))
    return cells


def claims(run: Run, arm: str) -> tuple[list[Row], list[Row]]:
    # The replies that make a validity claim, and those whose claim contradicts the engine
    made = [
        r for r in run.arm(arm) if r.get("validity_claim") not in (None, "", "none")
    ]
    return made, [r for r in made if r["rule"] == "engine"]


def claim_rates(run: Run, arm: str) -> tuple[str, str, bool]:
    made, against = claims(run, arm)
    prompts = run.by_prompt(made)
    bad = {r["prompt"] for r in against}
    return (
        zero_or_rate(len(bad), len(prompts)),
        zero_or_rate(len(against), len(made)),
        not against,
    )


def citations(run: Run) -> tuple[int, int, list[Row]]:
    # Every citation the SAGE arm's replies kept, and how many the judge found support their claim
    cited = [r for r in run.arm("sage") if int(r.get("cited") or 0)]
    kept = sum(int(r["cited"]) for r in cited)
    supported = sum(int(r["supported"]) for r in cited)
    return kept, supported, cited


def verdict(share: float, low: float, target: float) -> tuple[str, str]:
    return (
        "met" if share >= target else "not met",
        "yes" if low >= target else "no",
    )


def verdicts(run: Run) -> list[str]:
    rows = []
    prompts_claims, replies_claims, none_against = claim_rates(run, "sage")
    rows.append(
        (
            "Validity claims the engine doesn't support",
            prompts_claims,
            replies_claims,
            "0",
            "met" if none_against else "not met",
            "",
        )
    )
    for label, answerable, target in (
        ("Answerable prompts answered correctly (pass^1)", True, ANSWERED),
        ("The rest referred or declined (pass^1)", False, REFERRED),
    ):
        prompts = run.by_prompt(run.arm("sage", answerable))
        counts = [sum(succeeded(r, answerable) for r in rs) for rs in prompts.values()]
        replies = run.arm("sage", answerable)
        n = len(counts)
        share = pass_k(counts, TRIES, 1) if n else 0.0
        low = wilson(share * n, n)[0] if n else 0.0
        met, clears = verdict(share, low, target)
        rows.append(
            (
                label,
                rate(share * n, n),
                rate(sum(succeeded(r, answerable) for r in replies), len(replies)),
                f"at least {percent(target)}",
                met,
                clears,
            )
        )
    kept, supported, cited = citations(run)
    low = wilson(supported, kept)[0] if kept else 0.0
    met, clears = verdict(supported / kept if kept else 0.0, low, SUPPORTED)
    whole = sum(int(r["supported"]) == int(r["cited"]) for r in cited)
    rows.append(
        (
            "Citations supporting their claim",
            f"per citation: {rate(supported, kept)}",
            f"replies whose every citation does: {rate(whole, len(cited))}",
            f"at least {percent(SUPPORTED)}",
            met,
            clears,
        )
    )
    return [
        "",
        "## Verdicts",
        "",
        (
            "NF-2's four targets, for the SAGE arm. A verdict is met or not on the point estimate, the "
            "prompt-level pass^1 for the two rates, and the last column says whether the 95% "
            "interval's low end clears the target too."
        ),
        *table(
            ("Measure", "Prompts", "Replies", "Target", "Verdict", "Low end clears"),
            rows,
        ),
    ]


def outcomes(run: Run) -> list[str]:
    groups = dict.fromkeys(row["group"] for row in run.resolved.values())
    rows = []
    for group in groups:
        for arm, name in ARMS.items():
            theirs = [r for r in run.arm(arm) if r["group"] == group]
            if theirs:
                counted = Counter(r["outcome"] for r in theirs)
                rows.append([group, name, len(theirs), *(counted[o] for o in OUTCOMES)])
    answered_flagged = Counter(
        r["group"]
        for r in run.arm("sage", True)
        if r["outcome"] == "correct_answer" and r["referral"] == "yes"
    )
    return [
        "",
        "## Outcomes by group and arm",
        "",
        "Replies, three tries a prompt, by their final outcome once code has checked the judge.",
        *table(("Group", "Arm", "Replies", *OUTCOMES), rows),
        "",
        (
            "SAGE replies that answered correctly with the referral flag set, which count as answered: "
            + (
                ", ".join(
                    f"{group} {count}" for group, count in answered_flagged.items()
                )
                or "none"
            )
            + "."
        ),
    ]


def passes(run: Run) -> list[str]:
    rows = [
        [ARMS[arm], label, *pass_rates(run, arm, answerable)]
        for arm in ARMS
        for label, answerable in (("Answerable", True), ("Referral or decline", False))
        if run.arm(arm, answerable)
    ]
    return [
        "",
        "## pass^k",
        "",
        (
            "With the prompt as the unit, pass^k is the chance that k tries all succeed, C(c, k) / "
            "C(3, k) averaged over prompts. An answerable prompt succeeds with correct_answer, and "
            "the rest with correct_referral. The control arm asks only the prompts marked for it."
        ),
        *table(
            ("Arm", "Which prompts", "pass^1", "pass^2", "pass^3", "pass^1 per reply"),
            rows,
        ),
    ]


def guardrails(run: Run) -> list[str]:
    # The two arms on the prompts both asked, which is what the guardrails buy
    shared = {r["prompt"] for r in run.arm("control")}
    rows = []
    for arm, name in ARMS.items():
        theirs = [r for r in run.arm(arm) if r["prompt"] in shared]
        if not theirs:
            continue
        answerable = [r for r in theirs if run.answerable(r["prompt"])]
        rest = [r for r in theirs if not run.answerable(r["prompt"])]
        made = [r for r in theirs if r.get("validity_claim") not in (None, "", "none")]
        rows.append(
            [
                name,
                rate(sum(succeeded(r, True) for r in answerable), len(answerable)),
                rate(sum(succeeded(r, False) for r in rest), len(rest)),
                zero_or_rate(
                    sum(r["outcome"] == "unsupported" for r in theirs), len(theirs)
                ),
                zero_or_rate(sum(r["rule"] == "engine" for r in made), len(made)),
            ]
        )
    return [
        "",
        "## What the guardrails buy",
        "",
        f"Both arms on the {len(shared)} prompts the control arm asked, per reply.",
        *table(
            (
                "Arm",
                "Answerable, answered",
                "Rest, referred or declined",
                "Unsupported replies",
                "Claims against the engine",
            ),
            rows,
        ),
    ]


def checks(run: Run) -> list[str]:
    sage = run.arm("sage")
    kept, supported, _ = citations(run)
    dropped = sum(len(json.loads(r.get("dropped") or "[]")) for r in sage)
    flagged = sum(len(json.loads(r.get("flags") or "[]")) for r in sage)
    fixed = Counter(r["why_fixed"] for r in sage if r.get("fixed") == "yes")
    offered = [r for r in sage if r.get("offered")]
    return [
        "",
        "## What SAGE's checks did",
        "",
        f"- Citations kept: {kept}, of which the judge found {supported} support their claim.",
        f"- Quotes the citation check dropped: {dropped}. Flags raised: {flagged}.",
        (
            "- The fixed referral: "
            + (", ".join(f"{count} ({why})" for why, count in fixed.items()) or "none")
            + "."
        ),
        (
            f"- Plans offered: {len(offered)}, of them hidden by the questionnaire: "
            f"{sum(r['offered_hidden'] == 'yes' for r in offered)}. Dropped plan offers: "
            f"{sum(bool(r.get('unoffered')) for r in sage)}."
        ),
        f"- Titles not ready in time: {sum(r.get('title_ready') == 'no' for r in sage)}.",
    ]


def paraphrases(run: Run) -> list[str]:
    pairs = [
        (row["id"], row["paraphrase_of"])
        for row in run.prompts.values()
        if row["paraphrase_of"].strip()
    ]
    rows = []
    for arm, name in ARMS.items():
        outcomes_of = {
            prompt: [r["outcome"] for r in replies]
            for prompt, replies in run.by_prompt(run.arm(arm)).items()
        }
        asked = [(a, b) for a, b in pairs if a in outcomes_of and b in outcomes_of]
        if not asked:
            continue
        agree = sum(pair_agrees(outcomes_of[a], outcomes_of[b]) for a, b in asked)
        crossed = [cross_agreement(outcomes_of[a], outcomes_of[b]) for a, b in asked]
        rows.append(
            [
                name,
                rate(agree, len(asked)),
                rate(sum(k for k, _ in crossed), sum(n for _, n in crossed)),
            ]
        )
    return [
        "",
        "## Paraphrase pairs",
        "",
        (
            "A pair agrees when both prompts' most common outcome over their tries is the same, and a "
            "three-way split never agrees. Per reply, each try of one is set against each try of the "
            "other."
        ),
        *listed(
            ("Arm", "Pairs whose outcomes agree", "Pairs of tries that agree"), rows
        ),
    ]


def quantile(times: Sequence[float], share: int) -> str:
    if len(times) < 2:
        return f"{times[0]:.1f} s" if times else ""
    return f"{statistics.quantiles(times, n=100, method='inclusive')[share - 1]:.1f} s"


def timing(run: Run) -> list[str]:
    rows = []
    for arm, name in ARMS.items():
        answered = [r for r in run.arm(arm) if not r.get("error")]
        by_calls: dict[str, list[float]] = defaultdict(list)
        for reply in answered:
            by_calls[reply["calls"]].append(float(reply["seconds"]))
        for calls in sorted(by_calls, key=int):
            times = by_calls[calls]
            rows.append(
                [name, calls, len(times), quantile(times, 50), quantile(times, 95)]
            )
        times = [float(r["seconds"]) for r in answered]
        rows.append([name, "all", len(times), quantile(times, 50), quantile(times, 95)])
    spend = defaultdict(float)
    for call in run.calls:
        spend[call["turn"].split("-")[0]] += float(call["cost"])
    judge = sum(float(r.get("judge_cost") or 0) for r in run.replies)
    turns = Counter(r["arm"] for r in run.replies)
    ran_out = sum(r.get("why_fixed") == "still calling tools" for r in run.arm("sage"))
    unavailable = Counter(
        r["arm"] for r in run.replies if r["outcome"] == "unavailable"
    )
    return [
        "",
        "## Time and cost",
        "",
        (
            "Turn time from the advisor's own clock, four turns at a time, by the model calls a turn "
            "made, its title call aside."
        ),
        *table(("Arm", "Model calls", "Turns", "p50", "p95"), rows),
        "",
        *(
            f"- {ARMS[arm]}: USD {spend[arm]:.4f} for {turns[arm]} turns, "
            f"USD {spend[arm] / turns[arm]:.5f} a turn."
            for arm in ARMS
            if turns[arm]
        ),
        f"- The judge: USD {judge:.4f} for {sum(1 for r in run.replies if r.get('key'))} calls.",
        f"- In all: USD {sum(spend.values()) + judge:.4f}.",
        f"- SAGE turns that ran out of calls: {ran_out}.",
        (
            "- Turns that never reached her: "
            + (", ".join(f"{ARMS[a]} {n}" for a, n in unavailable.items()) or "none")
            + "."
        ),
    ]


def moves(run: Run) -> list[str]:
    rows = [
        [
            row["prompt"],
            row["group"],
            row["moved"] or "",
            row["predicted"],
            row["engine"],
        ]
        for row in run.resolved.values()
        if row["moved"] or (row["predicted"] and row["predicted"] != row["engine"])
    ]
    return [
        "",
        "## What resolve.py moved",
        "",
        (
            "Prompts whose expected behaviour moved before the run, and predicted verdicts the "
            "engine's overrode. Each was fixed in resolved.csv before any model call."
        ),
        *listed(("Prompt", "Group", "Moved", "Predicted", "Engine"), rows),
    ]


def agreement(run: Run) -> list[str]:
    path = RESULTS / "human.csv"
    marked = [r for r in load("human") if r["my_outcome"]] if path.exists() else []
    if not marked:
        return [
            "",
            "## The judge against my marks",
            "",
            "Awaiting my marks on the sample.",
        ]
    by_turn = {r["turn"]: r for r in run.replies}
    lines = ["", "## The judge against my marks", ""]
    for label, field in (
        ("the final outcome", "outcome"),
        ("the judge's own", "judge_outcome"),
    ):
        pairs = [(m["my_outcome"], by_turn[m["turn"]][field]) for m in marked]
        agreed = sum(a == b for a, b in pairs)
        found = kappa(pairs)
        lines.append(
            f"- Against {label}: {rate(agreed, len(pairs))} agree, Cohen's kappa "
            + (f"{found:.3f}" if found is not None else "undefined")
            + "."
        )
    calls = []
    for mark in marked:
        judge = {
            m["position"]: m["supports"]
            for m in json.loads(by_turn[mark["turn"]]["marks"] or "[]")
        }
        calls += [
            (m["supports"], judge[m["position"]])
            for m in json.loads(mark["my_marks"] or "[]")
            if m["position"] in judge
        ]
    lines.append(
        f"- Citations: {rate(sum(a == b for a, b in calls), len(calls))} of my calls agree with the judge's."
    )
    return lines


def wrong(run: Run) -> list[str]:
    path = RESULTS / "causes.csv"
    causes = {r["turn"]: r for r in load("causes")} if path.exists() else {}
    lines = [
        "",
        "## Every unsupported or wrong SAGE reply",
        "",
        (
            "Each with its question and the evidence. The cause is my judgement, read at Stop 3. "
            "SAGE's own causes are the wrong passage, missed evidence, a wrong tool argument, the "
            "check dropping a good quote, the model ignoring evidence, and the record-only check: "
            "check_eligibility judges her record as it stands, and the reply relays its verdict, as "
            "the advisor's rule 3 asks. Where the reply was right, the judge erred: it lacked "
            "SAGE's evidence, as it never sees the tools' results or her plan's reasons, it misread "
            "the claim, or it was stricter than the expected fact."
        ),
    ]
    found = [
        r for r in run.arm("sage") if r["outcome"] in ("unsupported", "wrong_safe")
    ]
    if not found:
        return [*lines, "", "None."]
    for reply in sorted(found, key=lambda r: (r["prompt"], int(r["try"]))):
        prompt, resolved = run.prompts[reply["prompt"]], run.resolved[reply["prompt"]]
        cited = json.loads(reply["citations"] or "[]")
        tools = json.loads(reply["tools"] or "[]")
        cause = causes.get(reply["turn"], {})
        lines += [
            "",
            f"### {reply['turn']}: {reply['outcome']}"
            + (f" ({reply['rule']})" if reply["rule"] else ""),
            "",
            f"- Question ({resolved['group']}, expects {resolved['expected']}): {prompt['prompt']}",
            f"- Expected fact: {prompt['expected_fact'] or 'none given'}",
            f"- Engine and plan facts: {resolved['words']}",
            f"- Reply: {reply['reply']}",
            f"- Judge: {reply['judge_outcome']}, claim {reply['validity_claim']}"
            + (f" on {reply['validity_course']}" if reply["validity_course"] else "")
            + (f", engine {reply['engine_verdict']}" if reply["engine_verdict"] else "")
            + f". {reply['reason']}",
            "- Citations: "
            + (
                "; ".join(f'"{c["quote"]}" (p. {c["page"]})' for c in cited)
                if cited
                else "none"
            ),
            "- Tools: "
            + (
                "; ".join(f"{t['name']} {json.dumps(t['arguments'])}" for t in tools)
                if tools
                else "none"
            ),
            f"- Cause: {cause.get('cause', 'to be classed')}"
            + (f". {cause['note']}" if cause.get("note") else ""),
        ]
    return lines


def main() -> None:
    run = Run()
    lines = [
        "# ATP-3: grounded advice",
        "",
        (
            "report.py wrote this from the CSVs beside it. The prompts and students were committed "
            "before any run, with their SHA-256 in `../HASHES.md`, and every expectation was fixed "
            "in `resolved.csv` before any model call. Each prompt was asked three times in fresh "
            "chats. The prompt is the unit, with per-reply numbers beside, and a rate carries its "
            "95% Wilson interval in brackets."
        ),
        *verdicts(run),
        *outcomes(run),
        *passes(run),
        *guardrails(run),
        *checks(run),
        *paraphrases(run),
        *timing(run),
        *moves(run),
        *agreement(run),
        *wrong(run),
    ]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("results/report.md written")


if __name__ == "__main__":
    main()
