# Writes ATP-2's report, results/report.md, and the two CSVs behind the thesis's figures,
# failure_cost.csv and scaling.csv, from the CSVs run.py writes and the causes written by hand,
# and nothing else, so every number traces to their rows. It prints no date. make atp2 runs it
# after run.py, from backend/.
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from csv import DictReader, DictWriter
from pathlib import Path
from statistics import median, quantiles

from scoring import bound, wilson

RESULTS = Path(__file__).resolve().parent / "results"
# The held-out labelled records lead, then the failure sweep, then the in-sample base records
SETS = {"labelled": "Held out", "failure": "Failure sweep", "base": "In-sample base"}
# The verdicts' columns: the held-out records with and without the labels' judgement calls, then
# the failure sweep and the in-sample base records
COLUMNS = {
    "labelled": "Held out",
    "clear": "Held out, without judgement calls",
    "failure": "Failure sweep",
    "base": "In-sample base",
}
# The labelled fields each verdict on the labels reads. F-2's rests on a decision's status and
# deciding codes, and its page is reported beside it, as is a decision that cites none.
DECIDED = ("status", "deciding_codes")
NO_CITATION = "no citation"
PLANNED = ("expected_plans", "expected_combinations")
STANDING = ("year_of_study", "owed_core", "excluded_core")
LIMIT = 10.0  # NF-4's seconds for one session's plans
RELATIONS = ("reordered history", "section removed", "pass added")

Row = dict[str, str]


def load(name: str) -> list[Row]:
    with (RESULTS / f"{name}.csv").open(encoding="utf-8", newline="") as file:
        return list(DictReader(file))


def causes() -> list[Row]:
    # Each disagreement's cause, written by hand after the first run. Before then there are none.
    path = RESULTS / "causes.csv"
    return load("causes") if path.exists() else []


def percent(share: float) -> str:
    return f"{100 * share:.1f}%"


def rate(k: int, n: int) -> str:
    # k of n, its share and its 95% Wilson interval
    if not n:
        return "none to count"
    low, high = wilson(k, n)
    return f"{k} of {n}, {percent(k / n)} ({percent(low)} to {percent(high)})"


def wrong(k: int, n: int) -> str:
    # How many of n are wrong, with the one-sided 95% upper bound when none is
    if not n:
        return "none to count"
    upper = bound(k, n)
    return (
        rate(k, n) if upper is None else f"0 of {n} (95% upper bound {percent(upper)})"
    )


def p95(values: Sequence[float]) -> float:
    return (
        quantiles(values, n=20, method="inclusive")[18]
        if len(values) > 1
        else values[0]
    )


def seconds(value: float) -> str:
    return f"{value:.3f} s"


def table(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    def line(cells: Sequence[object]) -> str:
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"

    return ["", line(header), line(["---"] * len(header)), *map(line, rows)]


def listed(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    rows = list(rows)
    return table(header, rows) if rows else ["", "None."]


def total(rows: Iterable[Row], key: str) -> int:
    return sum(int(row[key]) for row in rows)


def by_set(rows: Iterable[Row]) -> dict[str, list[Row]]:
    # Rows by the verdicts' columns, the held-out ones again without the judgement calls
    found: dict[str, list[Row]] = {name: [] for name in COLUMNS}
    for row in rows:
        found[row["set"]].append(row)
        if row["set"] == "labelled" and row["judgement_call"] == "no":
            found["clear"].append(row)
    return found


def without(rows: Iterable[Row]) -> list[Row]:
    return [row for row in rows if row["judgement_call"] == "no"]


def matched(rows: Sequence[Row], side: str = "engine") -> str:
    # How many labelled items one side matches, of those it gives a value for. A decision citing
    # no page has no value to match.
    theirs = [row for row in rows if row[f"{side}_match"] in ("yes", "no")]
    return rate(sum(row[f"{side}_match"] == "yes" for row in theirs), len(theirs))


def runs(timings: Iterable[Row]) -> list[float]:
    return [float(row[f"generate_{i}"]) for row in timings for i in range(1, 6)]


def verdicts(
    labelled: list[Row],
    sweep: list[Row],
    decisions: list[Row],
    metamorphic: list[Row],
    timings: list[Row],
    found: list[Row],
) -> list[str]:
    records, statuses = by_set(sweep), by_set(decisions)
    times, relations = by_set(timings), by_set(metamorphic)
    confirmed = with_slips(labelled, found)

    def on_labels(rows: list[Row]) -> dict[str, list[Row]]:
        return {"labelled": rows, "clear": without(rows), "failure": [], "base": []}

    def measured(
        groups: dict[str, list[Row]], measure: Callable[[list[Row]], str]
    ) -> list[str]:
        return [measure(groups[s]) if groups[s] else "none to count" for s in COLUMNS]

    def met(done: bool) -> str:
        return "met" if done else "not met"

    # Every labelled field but the page, which is reported beside the verdicts
    judged = {row["field"] for row in labelled} - {"page"}

    def against(fields: Sequence[str] = ()) -> Callable[[list[Row]], str]:
        # The engine against the labels, on the fields given or on every field judged
        return lambda rows: matched(
            [r for r in rows if r["field"] in (fields or judged)]
        )

    def all_match(fields: Sequence[str] = ()) -> Callable[[list[Row]], str]:
        return lambda rows: met(
            all(
                row["engine_match"] == "yes"
                for row in rows
                if row["field"] in (fields or judged)
            )
        )

    def labelled_line(
        requirement: str,
        measure: str,
        rule: Callable[[list[Row]], str],
        target: str,
        verdict: Callable[[list[Row]], str],
    ) -> list[tuple[str, ...]]:
        # A line on the labels, and below it the same line with the label slips confirmed after
        # the run, where they change it
        line = (requirement, measure, *measured(on_labels(labelled), rule))
        twin = (
            requirement,
            f"{measure}, with the label slips confirmed after the run",
            *measured(on_labels(confirmed), rule),
        )
        lines = [(*line, target, verdict(labelled))]
        if twin[2:] != line[2:]:
            lines.append((*twin, target, verdict(confirmed)))
        return lines

    def reported(rows: list[Row]) -> str:
        return "reported"

    def uncited(rows: list[Row]) -> str:
        pages = [row for row in rows if row["field"] == "page"]
        return rate(
            sum(row["engine_match"] == NO_CITATION for row in pages), len(pages)
        )

    def broken(rows: list[Row]) -> tuple[int, int]:
        applies = [row for row in rows if row["applies"] == "yes"]
        return sum(row["held"] == "no" for row in applies), len(applies)

    every_run = runs(timings)
    rows = [
        *labelled_line(
            "F-2, F-3, NF-1",
            "Every labelled item but the pages matches its label: the pass criterion",
            against(),
            "100%",
            all_match(),
        ),
        *labelled_line(
            "F-2, NF-1",
            "Focal decisions whose status and deciding codes match the label",
            against(DECIDED),
            "100%",
            all_match(DECIDED),
        ),
        *labelled_line(
            "F-2",
            "Citing the handbook: cited pages that are the label's, of decisions citing one",
            against(("page",)),
            "",
            reported,
        ),
        *labelled_line(
            "F-2",
            "Citing the handbook: decisions citing no page, in check() or a plan reason",
            uncited,
            "",
            reported,
        ),
        *labelled_line(
            "F-3, NF-1",
            "Plan counts and combinations that match the labels",
            against(PLANNED),
            "100%",
            all_match(PLANNED),
        ),
        *labelled_line(
            "F-3",
            "Plans whose slots match the labels",
            against(("expected_slots",)),
            "100%",
            all_match(("expected_slots",)),
        ),
        *labelled_line(
            "NF-1",
            "Years of study, and owed and excluded core, that match the labels",
            against(STANDING),
            "100%",
            all_match(STANDING),
        ),
        *labelled_line(
            "NF-1",
            "Set-level reasons print requires that the engine gives, by kind and codes",
            against(("set_reason",)),
            "100%",
            all_match(("set_reason",)),
        ),
        (
            "F-2, NF-1",
            "Statuses the engine and the checker agree on",
            *measured(
                statuses,
                lambda r: rate(sum(x["match"] == "yes" for x in r), len(r)),
            ),
            "100%",
            met(all(row["match"] == "yes" for row in decisions)),
        ),
        (
            "F-3, NF-1",
            "Records whose plan set is exactly the checker's",
            *measured(
                records,
                lambda r: rate(sum(x["plans_match"] == "yes" for x in r), len(r)),
            ),
            "100%",
            met(all(row["plans_match"] == "yes" for row in sweep)),
        ),
        (
            "F-3, NF-1",
            "Valid plans the engine leaves out, of the checker's",
            *measured(
                records,
                lambda r: wrong(total(r, "missing"), total(r, "checker_plans")),
            ),
            "0",
            met(not total(sweep, "missing")),
        ),
        (
            "F-3, NF-1",
            "Plans the engine gives that aren't valid, of the engine's",
            *measured(
                records,
                lambda r: wrong(total(r, "extra"), total(r, "engine_plans")),
            ),
            "0",
            met(not total(sweep, "extra")),
        ),
        (
            "F-3, NF-1",
            "Plans the engine lists twice, of the engine's",
            *measured(
                records,
                lambda r: wrong(total(r, "duplicate"), total(r, "engine_plans")),
            ),
            "0",
            met(not total(sweep, "duplicate")),
        ),
        (
            "F-3",
            "Slots whose credits, owed course and fitting courses agree, in plans both hold",
            *measured(
                records,
                lambda r: rate(
                    total(r, "slots") - total(r, "slots_wrong"), total(r, "slots")
                ),
            ),
            "100%",
            met(not total(sweep, "slots_wrong")),
        ),
        (
            "NF-1",
            "Plans resting on judgement whose every open or untimed course has a conditional reason",
            *measured(
                records,
                lambda r: rate(
                    total(r, "judged_plans") - total(r, "judged_wrong"),
                    total(r, "judged_plans"),
                ),
            ),
            "100%",
            met(not total(sweep, "judged_wrong")),
        ),
        (
            "NF-4",
            "Generate's p95 over every run, one session at a time",
            *measured(
                times, lambda r: f"{seconds(p95(runs(r)))} over {len(runs(r))} runs"
            ),
            "within 10 s",
            met(p95(every_run) <= LIMIT),
        ),
        (
            "F-2, F-3",
            "Metamorphic relations broken, of the instances where they apply",
            *measured(relations, lambda r: wrong(*broken(r))),
            "0",
            met(not broken(metamorphic)[0]),
        ),
    ]
    return [
        "",
        "## Verdicts",
        "",
        (
            "ATP-2's pass criterion (Table 3.4): \"Every decision matches its label, and plan sets "
            "hold every valid plan once and nothing else.\" It verifies F-2, F-3 and NF-1, and NF-4's "
            "single-session 10 s. The sweep's records have no labels, so there the checker is the "
            "oracle. F-3's ranking is left out, as the checker doesn't rank. Two label slips were "
            "confirmed after the run, so each line they touch is given twice: as labelled, and with "
            "the slips confirmed, counted as the engine's matches."
        ),
        *table(
            ("Requirement", "Measure", *COLUMNS.values(), "Target", "Verdict"), rows
        ),
    ]


def cause_row(found: list[Row], kind: str, record: str, course: str) -> Row | None:
    # A disagreement's row in causes.csv, whose rows name a kind and, where a cause covers only
    # some, a record and a course. The first that fits is the cause.
    return next(
        (
            row
            for row in found
            if row["kind"] == kind
            and row["record"] in ("", record)
            and row["course"] in ("", course)
        ),
        None,
    )


def cause_of(found: list[Row], kind: str, record: str, course: str) -> str:
    row = cause_row(found, kind, record, course)
    if row is None:
        return "not yet classified"
    confirmed = f", confirmed {row['confirmed']}" if row["confirmed"] else ""
    return f"{row['cause']}{confirmed}: {row['evidence']}"


def with_slips(labelled: list[Row], found: list[Row]) -> list[Row]:
    # The labelled items again, with each miss a label slip confirmed after the run explains counted
    # as the engine's match, as the label was wrong there and the engine right
    def confirmed(row: Row) -> bool:
        cause = cause_row(found, f"label {row['field']}", row["record"], row["item"])
        return bool(cause and cause["cause"] == "label slip" and cause["confirmed"])

    return [
        row | {"engine_match": "yes"}
        if row["engine_match"] == "no" and confirmed(row)
        else row
        for row in labelled
    ]


def against_labels(labelled: list[Row], found: list[Row]) -> list[str]:
    # The held-out records against their labels, field by field, with and without the judgement
    # calls, and the checker against the same labels where it gives a value
    fields = dict.fromkeys(row["field"] for row in labelled)
    confirmed = with_slips(labelled, found)

    def counts(rows: list[Row]) -> list[object]:
        return [
            len(rows),
            matched(rows),
            matched(without(rows)),
            sum(row["engine_match"] == NO_CITATION for row in rows),
            matched(rows, "checker"),
            matched(without(rows), "checker"),
        ]

    # Each field, and again with the label slips confirmed after the run where they change it
    lines = []
    for field in fields:
        line = counts([r for r in labelled if r["field"] == field])
        twin = counts([r for r in confirmed if r["field"] == field])
        lines.append([field, *line])
        if twin != line:
            lines.append(
                [f"{field}, with the label slips confirmed after the run", *twin]
            )
    differ = [
        [
            *(
                row[k]
                for k in (
                    "record",
                    "field",
                    "item",
                    "label",
                    "engine",
                    "checker",
                    "judgement_call",
                )
            ),
            cause_of(found, f"label {row['field']}", row["record"], row["item"]),
        ]
        for row in labelled
        if {"no", NO_CITATION} & {row["engine_match"], row["checker_match"]}
    ]
    return [
        "",
        "## Held out: against the labels",
        "",
        (
            "Six records labelled from print and committed before the first run, with 32 focal "
            "decisions. Four records and one decision row are judgement calls, so each table is "
            "given with them and without. A record's fields carry its own flag, and a decision's "
            "fields the decision's. Deciding codes and text pages are matched as text, as the "
            "labels' README says. The checker gives no reasons or pages, so it has none to match "
            "there. A field the two label slips confirmed after the run touch is given again with "
            "the slips confirmed, counted as the engine's matches."
        ),
        *table(
            (
                "Field",
                "Items",
                "Engine right",
                "Without judgement calls",
                "No citation",
                "Checker right",
                "Without judgement calls",
            ),
            lines,
        ),
        "",
        "Every labelled item the engine or the checker doesn't match:",
        *listed(
            (
                "Record",
                "Field",
                "Item",
                "Label",
                "Engine",
                "Checker",
                "Judgement call",
                "Cause",
            ),
            differ,
        ),
    ]


def kinds(sweep: list[Row], decisions: list[Row]) -> list[str]:
    # Each set by kind of record and curriculum, so a fault shows where it sits
    statuses: dict[str, list[Row]] = defaultdict(list)
    for row in decisions:
        statuses[row["record"]].append(row)
    groups: dict[tuple[str, str, str], list[Row]] = defaultdict(list)
    for row in sweep:
        groups[row["set"], row["kind"], row["curriculum"]].append(row)

    def counts(rows: list[Row]) -> list[object]:
        theirs = [d for row in rows for d in statuses[row["record"]]]
        return [
            len(rows),
            rate(sum(row["plans_match"] == "yes" for row in rows), len(rows)),
            total(rows, "missing"),
            total(rows, "extra"),
            total(rows, "duplicate"),
            rate(sum(d["match"] == "yes" for d in theirs), len(theirs)),
            rate(
                total(rows, "slots") - total(rows, "slots_wrong"), total(rows, "slots")
            ),
        ]

    header = (
        "Set",
        "Kind",
        "Curriculum",
        "Records",
        "Plan sets right",
        "Missing",
        "Extra",
        "Twice",
        "Statuses right",
        "Slots right",
    )
    order = sorted(groups, key=lambda key: (list(SETS).index(key[0]), key[1], key[2]))
    return [
        "",
        "## By kind of record and curriculum",
        "",
        (
            "Base records are on track, every earlier course passed. Each failure record fails one "
            "previous-year core course (F, 40), or first-year maths and physics together; "
            "supplementary records defer one (FS, 46); arrears records fail it and pass two of her "
            "own year's courses, so FB5 puts her in her year owing it."
        ),
        *table(
            header, ([SETS[s], k, c, *counts(groups[s, k, c])] for s, k, c in order)
        ),
    ]


def relations(metamorphic: list[Row]) -> list[str]:
    rows = []
    for name in RELATIONS:
        for key, label in SETS.items():
            theirs = [
                r for r in metamorphic if r["relation"] == name and r["set"] == key
            ]
            if not theirs:
                continue
            applies = [r for r in theirs if r["applies"] == "yes"]
            broken = sum(r["held"] == "no" for r in applies)
            rows.append(
                [name, label, len(theirs), len(applies), wrong(broken, len(applies))]
            )
    return [
        "",
        "## Metamorphic relations",
        "",
        (
            "Reordered history: her lines shuffled give the same plan sets and statuses. Section "
            "removed: one alternative of one plan course's choice group taken away never adds a "
            "plan; it applies where the checker's FB3.4 drops don't change. Pass added: a pass in a "
            "course of her year's groups she hasn't passed, complementary courses aside, never turns "
            "another course from eligible to not_eligible, that course and those its pass covers "
            "aside."
        ),
        *table(("Relation", "Set", "Instances", "Applies", "Broken"), rows),
    ]


def timed(timings: list[Row]) -> list[str]:
    rows = []
    for key, label in SETS.items():
        theirs = [row for row in timings if row["set"] == key]
        if not theirs:
            continue
        every = runs(theirs)
        checks = [float(row["check"]) for row in theirs]
        checker = [float(row["checker"]) for row in theirs]
        rows.append(
            [
                label,
                len(theirs),
                seconds(median(every)),
                seconds(p95(every)),
                seconds(max(every)),
                wrong(sum(t > LIMIT for t in every), len(every)),
                seconds(median(checks)),
                seconds(p95(checks)),
                seconds(median(checker)),
                seconds(p95(checker)),
            ]
        )
    return [
        "",
        "## Times",
        "",
        (
            "Each record's plans were generated five times in one process, one record at a time, "
            "and its statuses checked once. Generate's times are over every run. The checker's are "
            "one run per record."
        ),
        *table(
            (
                "Set",
                "Records",
                "Generate p50",
                "p95",
                "Largest",
                "Runs over 10 s",
                "Check p50",
                "p95",
                "Checker p50",
                "p95",
            ),
            rows,
        ),
    ]


def cost(sweep: list[Row], checked: dict[str, bool]) -> list[Row]:
    # failure_cost.csv: what failing each course cost the student, from the engine's own plans and
    # reasons beside her on-track record's, with whether the checker agreed on that record
    base = {row["record"]: row for row in sweep if row["kind"] == "base"}
    rows = []
    for row in sweep:
        if row["set"] != "failure":
            continue
        excluded = row["engine_excluded"].split()
        rows.append(
            {
                "record": row["record"],
                "curriculum": row["curriculum"],
                "year": row["year"],
                "variant": row["kind"],
                "course": row["course"],
                "held_back": "yes"
                if int(row["checker_year"]) < int(row["year"])
                else "no",
                "plans_left": row["engine_plans"],
                "base_plans": base[row["base"]]["engine_plans"],
                "core_excluded": len(excluded),
                "core_excluded_codes": " ".join(excluded),
                "fb34_dropped": row["engine_dropped"],
                "conditional_courses": row["conditional_courses"],
                **{key: row[key] for key in row if key.startswith("reasons_")},
                "checker_agrees": "yes" if checked[row["record"]] else "no",
            }
        )
    return rows


def costs(rows: list[Row]) -> list[str]:
    repeat = [row for row in rows if row["variant"] == "fail"]
    held = sum(row["held_back"] == "yes" for row in repeat)
    arrears = [row for row in rows if row["variant"] == "arrears"]

    def lost(row: Row) -> tuple[int, int, str]:
        return (
            int(row["base_plans"]) - int(row["plans_left"]),
            int(row["core_excluded"]),
            row["record"],
        )

    # The ten that cost the most plans, and any tied with the tenth
    ranked = sorted(arrears, key=lost, reverse=True)
    cut = lost(ranked[9])[0] if len(ranked) > 9 else 0
    worst = [row for row in ranked if lost(row)[0] >= cut]
    # Every failure record that leaves her no plan at all, by curriculum, year and course
    none_left = sorted(
        (row for row in rows if row["plans_left"] == "0"),
        key=lambda row: (row["curriculum"], row["year"], row["variant"], row["course"]),
    )
    explained = sum(int(row["reasons_conflict"]) > 0 for row in none_left)
    header = (
        "Curriculum",
        "Year",
        "Course failed",
        "Plans left",
        "On track",
        "Core excluded",
        "FB3.4 drops",
        "Checker agrees",
    )

    def shown(row: Row) -> list[str]:
        return [
            row["curriculum"],
            row["year"],
            row["course"],
            row["plans_left"],
            row["base_plans"],
            f"{row['core_excluded']} {row['core_excluded_codes']}".strip(),
            row["fb34_dropped"],
            row["checker_agrees"],
        ]

    return [
        "",
        "## What failing a course costs",
        "",
        (
            f"FB5 held back {rate(held, len(repeat))} of the records that fail one course and pass "
            "nothing of her own year: each is in the previous year again, and her plans are the "
            "repeat alone. The arrears variants are the thesis's figure: the same failure, with two "
            "of her own year's courses passed, so she's in her year owing it. The ten that cost the "
            f"most plans, with every record tied with the tenth ({len(worst)} in all), from "
            "failure_cost.csv:"
        ),
        *listed(header, map(shown, worst)),
        "",
        (
            f"Every failure record that leaves her no plan at all: {len(none_left)}, of which "
            f"{explained} carry a set-level conflict reason saying why:"
        ),
        *listed(
            ("Variant", *header), ([row["variant"], *shown(row)] for row in none_left)
        ),
    ]


def disagreements(
    sweep: list[Row], decisions: list[Row], metamorphic: list[Row], found: list[Row]
) -> list[str]:
    # Every disagreement against the checker, with its cause once causes.csv gives one
    def cause(kind: str, record: str, course: str) -> str:
        return cause_of(found, kind, record, course)

    plans = [
        [
            row["record"],
            row["missing_plans"],
            row["extra_plans"],
            cause("plans", row["record"], ""),
        ]
        for row in sweep
        if row["plans_match"] == "no"
    ]
    details = [
        [row["record"], row["detail"], cause("slots", row["record"], "")]
        for row in sweep
        if row["detail"]
    ]
    pairs: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in decisions:
        if row["match"] == "no":
            pairs[row["course"], row["engine"], row["checker"]].append(row["record"])
    statuses = [
        [
            course,
            engine,
            checker,
            len(records),
            records[0],
            cause("status", records[0], course),
        ]
        for (course, engine, checker), records in sorted(pairs.items())
    ]
    broken = [
        [
            row["record"],
            row["relation"],
            row["course"],
            row["detail"],
            cause("relation", row["record"], row["course"]),
        ]
        for row in metamorphic
        if row["held"] == "no"
    ]
    return [
        "",
        "## Disagreements",
        "",
        "Plan sets that differ, as each plan's codes:",
        *listed(("Record", "Valid plans missing", "Plans not valid", "Cause"), plans),
        "",
        "Slots that differ and plans resting on judgement without a conditional reason:",
        *listed(("Record", "Detail", "Cause"), details),
        "",
        "Statuses that differ, by course, with how many records and the first:",
        *listed(("Course", "Engine", "Checker", "Records", "First", "Cause"), statuses),
        "",
        "Metamorphic relations broken:",
        *listed(("Record", "Relation", "Changed", "Detail", "Cause"), broken),
    ]


def written(name: str, rows: list[Row]) -> None:
    with (RESULTS / f"{name}.csv").open("w", encoding="utf-8", newline="") as file:
        writer = DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    labelled, sweep, decisions = load("labelled"), load("sweep"), load("decisions")
    metamorphic, timings = load("metamorphic"), load("timings")
    agrees = {row["record"]: row["plans_match"] == "yes" for row in sweep}
    for row in decisions:
        agrees[row["record"]] = agrees[row["record"]] and row["match"] == "yes"
    failure = cost(sweep, agrees)
    written("failure_cost", failure)
    candidates = {row["record"]: row["candidates"] for row in sweep}
    written(
        "scaling",
        [
            {
                "record": row["record"],
                "set": row["set"],
                "candidates": candidates[row["record"]],
                "engine_p50": f"{median(runs([row])):.4f}",
                "engine_p95": f"{p95(runs([row])):.4f}",
                "checker": row["checker"],
            }
            for row in timings
        ],
    )
    lines = [
        "# ATP-2: the engine's decisions and plans",
        "",
        (
            "report.py wrote this from the CSVs beside it, which run.py wrote, and causes.csv, "
            "written by hand after the first run. A rate has its 95% Wilson interval in brackets, "
            "and a count with none wrong gives the one-sided 95% upper bound, 1 − 0.05^(1/n). The "
            "held-out records lead. The failure sweep follows, and the base records come last, as "
            "the engine was built on on-track students."
        ),
        *verdicts(labelled, sweep, decisions, metamorphic, timings, causes()),
        *against_labels(labelled, causes()),
        *kinds(sweep, decisions),
        *relations(metamorphic),
        *timed(timings),
        *costs(failure),
        *disagreements(sweep, decisions, metamorphic, causes()),
        "",
        "## Inputs",
        "",
        "The SHA-256 of every file the run read.",
        *table(
            ("File", "SHA-256"),
            ([f"`{row['file']}`", f"`{row['sha256']}`"] for row in load("inputs")),
        ),
    ]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
