# Writes ATP-1's report, results/report.md, from the CSVs run.py writes and nothing else, so every
# number traces to their rows. It prints no date, so a rerun from the cached drafts reproduces it
# byte for byte. make atp1 runs it after run.py, from backend/.
from collections import Counter
from collections.abc import Iterable, Sequence
from csv import DictReader
from datetime import datetime
from pathlib import Path

import transcripts
from scoring import ACCEPTED, NOT_STORED, REVIEWED, bound, wilson

RESULTS = Path(__file__).resolve().parent / "results"
# Each sheet's CSV, the held-out set first, as it's the headline for requirement trees
SHEETS = {
    "held_out": "Held out",
    "courses_2026": "Courses 2026",
    "courses_2023": "Courses 2023",
    "timetable": "Timetable",
    "complementary": "Complementary",
}
TEXTS = ("requirement", "corequisite")
# The labelled changes recall counts: a course's rule, and a course added or removed
RECALLED = ("entry_rule", "course")
FLAGGED = ("wording change", "false alarm")

Row = dict[str, str]


def main() -> None:
    sheets = {name: load(name) for name in SHEETS}
    changes, read_back = load("changes"), load("transcripts")
    lines = [
        "# ATP-1: how well ingestion reads print",
        "",
        (
            "report.py wrote this from the CSVs beside it, which run.py wrote. The labels in "
            "`../labels/` were written from print and committed before any run. A rate has its 95% "
            "Wilson interval in brackets, and a count with none wrong gives the one-sided 95% upper "
            "bound, 1 − 0.05^(1/n). Each table is given for all rows and without the judgement calls: "
            "labels whose Note records a judgement, or marked Ambiguous. Tables that compare nothing "
            "with a label, such as the refusals, the minutes and the change count, have none to leave "
            "out. Verdicts are on all rows."
        ),
        *verdicts(sheets, changes, read_back),
        *by_sheet(sheets),
        *trees(sheets),
        *(line for name, rows in sheets.items() for line in fields(name, rows)),
        *changed(changes),
        *refusals(sheets),
        *new_department(sheets["held_out"], load("sittings")),
        *minutes(load("sittings")),
        *counts(load("counts")),
        *read_backs(read_back),
        *not_stored(sheets),
        "",
        "## Not run",
        "",
        (
            "Reproducing a 2023 decision while 2026 is current needs the engine, so it runs in the "
            "engine milestone and is reported beside this result."
        ),
        *disagreements(sheets, read_back),
        *inputs(load("inputs")),
    ]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load(name: str) -> list[Row]:
    with (RESULTS / f"{name}.csv").open(encoding="utf-8", newline="") as file:
        return list(DictReader(file))


def percent(share: float) -> str:
    return f"{100 * share:.1f}%"


def rate(k: int, n: int) -> str:
    # k of n, its share and its 95% Wilson interval
    if not n:
        return "none to count"
    low, high = wilson(k, n)
    return f"{k} of {n}, {percent(k / n)} ({percent(low)} to {percent(high)})"


def wrong_of(rows: Sequence[Row]) -> str:
    # How many of the rows are wrong, with E2's bound when none is
    wrong = sum(row["match"] == "no" for row in rows)
    upper = bound(wrong, len(rows)) if rows else None
    if upper is None:
        return rate(wrong, len(rows))
    return f"0 of {len(rows)} (95% upper bound {percent(upper)})"


def table(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    def line(cells: Sequence[object]) -> str:
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"

    return ["", line(header), line(["---"] * len(header)), *map(line, rows)]


def listed(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    # A table, or a line saying there's nothing to list
    rows = list(rows)
    return table(header, rows) if rows else ["", "None."]


def without(rows: Iterable[Row]) -> list[Row]:
    return [row for row in rows if row["judgement"] == "no"]


def accepted(rows: Iterable[Row]) -> list[Row]:
    return [row for row in rows if row["review"] == ACCEPTED]


def right(rows: Sequence[Row]) -> str:
    return rate(sum(row["match"] == "yes" for row in rows), len(rows))


def verdicts(
    sheets: dict[str, list[Row]], changes: list[Row], read_back: list[Row]
) -> list[str]:
    every = [row for rows in sheets.values() for row in rows]
    held = [row for row in sheets["held_out"] if row["field"].endswith("_tree")]
    recall = [
        row
        for row in changes
        if row["field"] in RECALLED and row["outcome"] in ("recalled", "missed")
    ]
    printed = [row for row in read_back if row["outcome"] not in ("extra", "warning")]
    recovered = sum(row["outcome"] == "recovered" for row in printed)
    flagged = sum(row["outcome"] in ("unverified", "GPA warning") for row in printed)
    dropped = sum(row["outcome"] == "dropped" for row in printed)

    def recalled(rows: Sequence[Row]) -> str:
        return rate(sum(row["outcome"] == "recalled" for row in rows), len(rows))

    def counted(rows: Iterable[Row], outcome: str) -> int:
        return sum(row["outcome"] == outcome for row in rows)

    def met(done: bool) -> str:
        return "met" if done else "not met"

    rows = [
        (
            "Wrong items accepted without review, all five sheets",
            wrong_of(accepted(every)),
            wrong_of(accepted(without(every))),
            "0",
            met(not any(row["match"] == "no" for row in accepted(every))),
        ),
        (
            "Held out: wrong strings accepted without review",
            wrong_of(accepted(held)),
            wrong_of(accepted(without(held))),
            "0",
            met(not any(row["match"] == "no" for row in accepted(held))),
        ),
        (
            "Delta recall: rules changed, and courses added or removed",
            recalled(recall),
            recalled(without(recall)),
            "100%",
            met(all(row["outcome"] == "recalled" for row in recall)),
        ),
        (
            "Transcript rows recovered or flagged",
            f"{rate(recovered + flagged, len(printed))}; {dropped} dropped",
            "no judgement calls",
            "100%, none dropped",
            met(recovered + flagged == len(printed) and not dropped),
        ),
        (
            "Transcript rows recovered alone",
            rate(recovered, len(printed)),
            "no judgement calls",
            "",
            "reported",
        ),
        (
            "Items accepted without review, all five sheets",
            rate(len(accepted(every)), len(every)),
            rate(len(accepted(without(every))), len(without(every))),
            "",
            "reported",
        ),
        (
            "Items sent to review, all five sheets",
            rate(sum(row["review"] == REVIEWED for row in every), len(every)),
            rate(
                sum(row["review"] == REVIEWED for row in without(every)),
                len(without(every)),
            ),
            "",
            "reported",
        ),
        (
            "Held out: strings accepted without review",
            rate(len(accepted(held)), len(held)),
            rate(len(accepted(without(held))), len(without(held))),
            "",
            "reported",
        ),
        (
            "Wording changes: flagged, though the rule didn't change",
            counted(changes, "wording change"),
            counted(without(changes), "wording change"),
            "",
            "reported",
        ),
        (
            "False alarms: flagged, though neither rule nor wording changed",
            counted(changes, "false alarm"),
            counted(without(changes), "false alarm"),
            "",
            "reported",
        ),
    ]
    return [
        "",
        "## Verdicts",
        *table(
            ("Measure", "All rows", "Without judgement calls", "Target", "Verdict"),
            rows,
        ),
    ]


def by_sheet(sheets: dict[str, list[Row]]) -> list[str]:
    # What SAGE accepted without review on each sheet, and how much of that is wrong
    def counts(rows: list[Row]) -> list[object]:
        reviewed = sum(row["review"] == REVIEWED for row in rows)
        stored = sum(row["review"] == NOT_STORED for row in rows)
        return [
            len(rows),
            rate(len(accepted(rows)), len(rows)),
            reviewed,
            stored,
            wrong_of(accepted(rows)),
        ]

    header = (
        "Sheet",
        "Items",
        "Accepted without review",
        "Reviewed",
        "Not stored",
        "Wrong among accepted",
    )
    return [
        "",
        "## Accepted without review, by sheet",
        "",
        (
            "An item is one labelled field of one row. It counts as reviewed when a decided review row "
            "showed it, in its year or in 2023 when unchanged since. A held-out string counts as "
            "reviewed when the grammar refused it."
        ),
        *table(
            header, ([SHEETS[name], *counts(rows)] for name, rows in sheets.items())
        ),
        "",
        "Without judgement calls:",
        *table(
            header,
            ([SHEETS[name], *counts(without(rows))] for name, rows in sheets.items()),
        ),
    ]


def trees(sheets: dict[str, list[Row]]) -> list[str]:
    # Requirement trees, the held-out set first: per string there, per course on the course sheets
    sets = {
        "Held out, per string": [
            r for r in sheets["held_out"] if r["field"].endswith("_tree")
        ],
        "Courses 2026, per course": [
            r for r in sheets["courses_2026"] if r["field"] == "entry_rule"
        ],
        "Courses 2023, per course": [
            r for r in sheets["courses_2023"] if r["field"] == "entry_rule"
        ],
    }

    def counts(rows: list[Row]) -> list[object]:
        reviewed = [row for row in rows if row["review"] == REVIEWED]
        return [
            right(rows),
            len(accepted(rows)),
            wrong_of(accepted(rows)),
            len(reviewed),
            right(reviewed),
        ]

    header = (
        "Set",
        "Right",
        "Accepted without review",
        "Wrong among them",
        "Reviewed",
        "Right among reviewed",
    )
    held = sets["Held out, per string"]
    drafted = [row for row in held if row["draft"]]
    kept = [row for row in drafted if row["draft"] == "kept"]
    return [
        "",
        "## Requirement trees",
        "",
        (
            "The held-out set is the headline: no build branch opened Chemical Engineering or "
            "Construction Economics. The course sheets are an in-sample check, as the grammar was "
            "written from their fields."
        ),
        *table(header, ([name, *counts(rows)] for name, rows in sets.items())),
        "",
        "Without judgement calls:",
        *table(header, ([name, *counts(without(rows))] for name, rows in sets.items())),
        "",
        (
            f"Held-out strings the grammar refused: {len(drafted)}. Drafts kept: {len(kept)}, of "
            f"which exactly right: {rate(sum(r['match'] == 'yes' for r in kept), len(kept))}. Drafts "
            f"that weren't rule trees, so a refer leaf of the printed words took their place: "
            f"{len(drafted) - len(kept)}. A person reviews each refused string either way."
        ),
    ]


def fields(name: str, rows: list[Row]) -> list[str]:
    order = dict.fromkeys(row["field"] for row in rows)
    return [
        "",
        f"## {SHEETS[name]}: right, by field",
        *table(
            ("Field", "All rows", "Without judgement calls"),
            (
                [
                    field,
                    right([r for r in rows if r["field"] == field]),
                    right(without(r for r in rows if r["field"] == field)),
                ]
                for field in order
            ),
        ),
    ]


def changed(changes: list[Row]) -> list[str]:
    recall = [
        r
        for r in changes
        if r["field"] in RECALLED and r["outcome"] in ("recalled", "missed")
    ]
    apart = [
        r
        for r in changes
        if r["field"] not in RECALLED and r["outcome"] in ("recalled", "missed")
    ]
    flagged = [r for r in changes if r["outcome"] in FLAGGED]
    header = (
        "Course",
        "Field",
        "Change",
        "2023 label",
        "2026 label",
        "Flag",
        "Outcome",
        "Judgement call",
    )

    def shown(rows: list[Row]) -> list[str]:
        keys = (
            "code",
            "field",
            "change",
            "label_2023",
            "label_2026",
            "flag",
            "outcome",
            "judgement",
        )
        return listed(header, ([r[k] for k in keys] for r in rows))

    def recalled(rows: list[Row]) -> str:
        return rate(sum(r["outcome"] == "recalled" for r in rows), len(rows))

    return [
        "",
        "## Changes from 2023 to 2026",
        "",
        (
            "Labelled changes come from the two course sheets alone, on the courses they hold. Recall "
            "counts a course's rule, compared in normal form, and a course added or removed. A change "
            "is recalled when SAGE's 2026 review records a delta for that course and field, flagged or "
            f"not: {recalled(recall)} of all, and {recalled(without(recall))} without judgement calls."
        ),
        *shown(recall),
        "",
        (
            "Changes of title, credits, NQF level or term, counted apart: "
            f"{recalled(apart)} recorded."
        ),
        *shown(apart),
        "",
        (
            "Flagged 2026 deltas where the labels show no change of rule: a wording change where the "
            "labelled requirement or co-requisite text changed, and otherwise a false alarm."
        ),
        *shown(flagged),
    ]


def refusals(sheets: dict[str, list[Row]]) -> list[str]:
    # What the grammar made of each printed string the reader read, per course on each sheet
    sets = {
        "Courses 2023": sheets["courses_2023"],
        "Courses 2026": sheets["courses_2026"],
        "Held out": sheets["held_out"],
    }
    causes = {
        name: Counter(
            row["cause"] for row in rows if row["field"] in TEXTS and row["cause"]
        )
        for name, rows in sets.items()
    }
    total = sum(causes.values(), Counter())
    order = [
        "read",
        *sorted((c for c in total if c != "read"), key=lambda c: (-total[c], c)),
    ]
    return [
        "",
        "## Refusals by cause",
        "",
        (
            "Each printed requirement and co-requisite as SAGE's handbook reader read it, through the "
            "grammar, once per course that prints it."
        ),
        *table(
            ("Cause", *sets),
            (
                *(
                    [cause, *(counted[cause] for counted in causes.values())]
                    for cause in order
                ),
                [
                    "Refused",
                    *(
                        rate(sum(c.values()) - c["read"], sum(c.values()))
                        for c in causes.values()
                    ),
                ],
            ),
        ),
    ]


def new_department(held: list[Row], sittings: list[Row]) -> list[str]:
    # The review CHE and CON's own entries would bring, and the time it would take at CP2's pace
    entries = dict.fromkeys(row["item"] for row in held)
    refused = {
        row["item"]
        for row in held
        if row["field"] in TEXTS and row["cause"] not in ("", "read")
    }
    # SAGE reviews one row per distinct printed line: an entry's requirement and co-requisite
    lines = {
        tuple(
            row["sage"] for row in held if row["item"] == item and row["field"] in TEXTS
        )
        for item in refused
    }
    spent = sum(map(span, sittings))
    decided = sum(int(row["decided"]) for row in sittings)
    pace = spent / decided
    return [
        "",
        "## The review a new department would need",
        "",
        (
            f"Held-out entries with a printed string the grammar refused: "
            f"{rate(len(refused), len(entries))}. SAGE reviews one row per distinct printed line, so "
            f"Chemical Engineering's and Construction Economics' first year would bring review rows: "
            f"{len(lines)}. At CP2's pace of {pace:.2f} minutes a decision ({spent:.1f} minutes over "
            f"{decided} decisions), that's about {len(lines) * pace:.0f} minutes. At that rate, a "
            f"department printing n entries brings about {len(refused) / len(entries):.2f}n review "
            "rows, fewer where entries share a line."
        ),
    ]


def span(sitting: Row) -> float:
    # A sitting's minutes, from its start to its last save
    start, end = (datetime.fromisoformat(sitting[key]) for key in ("start", "end"))
    return (end - start).total_seconds() / 60


def minutes(sittings: list[Row]) -> list[str]:
    years = dict.fromkeys(row["year"] for row in sittings)
    rows = []
    for year in years:
        theirs = [row for row in sittings if row["year"] == year]
        spent = sum(map(span, theirs))
        decided = sum(int(row["decided"]) for row in theirs)
        rows.append(
            [year, len(theirs), f"{spent:.1f}", decided, f"{spent / decided:.2f}"]
        )
    return [
        "",
        "## Review minutes at CP2",
        "",
        "`sage review` timed each sitting, and the ingestion README records them.",
        *table(
            ("Year", "Sittings", "Minutes", "Decisions", "Minutes a decision"), rows
        ),
    ]


def counts(rows: list[Row]) -> list[str]:
    return [
        "",
        "## What changed between the approved years",
        "",
        (
            "From `experiments/ingestion/count_changes.py`, on both approved snapshots. Conveners aren't "
            "rules, so they're counted apart."
        ),
        *table(
            ("Kind", "Added", "Removed", "Changed"),
            (
                [row["kind"], row["added"], row["removed"], row["changed"]]
                for row in rows
            ),
        ),
    ]


def read_backs(read_back: list[Row]) -> list[str]:
    printed = [row for row in read_back if row["outcome"] not in ("extra", "warning")]
    kinds = dict.fromkeys(row["kind"] for row in printed)
    outcomes = ("recovered", "unverified", "GPA warning", "dropped")

    def counted(rows: list[Row]) -> list[int]:
        return [
            len(rows),
            *(sum(row["outcome"] == o for row in rows) for o in outcomes),
        ]

    students = dict.fromkeys(row["student"] for row in printed)
    extra = sum(row["outcome"] == "extra" for row in read_back)
    warned = sum(row["outcome"] == "warning" for row in read_back)
    return [
        "",
        "## Transcripts",
        "",
        (
            f"Made-up records: {len(students)}, drawn with seed {transcripts.SEED}, printed as "
            "`backend/tests/pdf.py` prints PDFs and read by SAGE's transcript reader. Unverified "
            "lines and rows covered only by their year's Term GPA warning are flagged. A row with "
            "neither, read wrongly or not at all, is dropped."
        ),
        *table(
            ("Kind", "Rows", "Recovered", "Unverified", "GPA warning", "Dropped"),
            (
                *(
                    [kind, *counted([r for r in printed if r["kind"] == kind])]
                    for kind in kinds
                ),
                ["All", *counted(printed)],
            ),
        ),
        "",
        (
            f"Lines no printed row accounts for: {extra}. Warnings, which a made-up record should "
            f"never raise: {warned}."
        ),
    ]


def not_stored(sheets: dict[str, list[Row]]) -> list[str]:
    # Each labelled item SAGE holds nothing from, with the course a timetable cell names
    found: dict[tuple[str, str], str] = {}
    for name, rows in sheets.items():
        for row in rows:
            if row["review"] == NOT_STORED:
                named = found.setdefault((SHEETS[name], row["item"]), "")
                found[SHEETS[name], row["item"]] = named or (
                    row["label"] if row["field"] == "course" else ""
                )
    return [
        "",
        "## Not stored",
        "",
        (
            "Labelled items SAGE holds nothing from, such as a timetable cell whose course the 2026 "
            "manifest leaves out. Each is still scored against the reader, and counts as neither "
            "accepted nor reviewed."
        ),
        *listed(
            ("Sheet", "Item", "Course"),
            ([sheet, item, course] for (sheet, item), course in found.items()),
        ),
    ]


def disagreements(sheets: dict[str, list[Row]], read_back: list[Row]) -> list[str]:
    rows = [
        [
            SHEETS[name],
            *(
                row[k]
                for k in (
                    "row",
                    "item",
                    "field",
                    "label",
                    "sage",
                    "review",
                    "judgement",
                )
            ),
        ]
        for name, theirs in sheets.items()
        for row in theirs
        if row["match"] == "no"
    ]
    misread = [
        [row[k] for k in ("student", "year", "code", "printed", "read", "outcome")]
        for row in read_back
        if row["outcome"] != "recovered"
    ]
    return [
        "",
        "## Disagreements",
        "",
        "Every labelled field where SAGE and the label differ. Row is the sheet's row.",
        *listed(
            (
                "Sheet",
                "Row",
                "Item",
                "Field",
                "Label",
                "SAGE",
                "Review",
                "Judgement call",
            ),
            rows,
        ),
        "",
        "Every transcript row not recovered, every extra line and every warning:",
        *listed(("Student", "Year", "Code", "Printed", "Read", "Outcome"), misread),
    ]


def inputs(rows: list[Row]) -> list[str]:
    return [
        "",
        "## Inputs",
        "",
        "The SHA-256 of every file the run read.",
        *table(
            ("File", "SHA-256"),
            ([f"`{row['file']}`", f"`{row['sha256']}`"] for row in rows),
        ),
    ]


if __name__ == "__main__":
    main()
