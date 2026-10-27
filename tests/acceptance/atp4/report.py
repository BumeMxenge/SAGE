# ATP-4's report, results/report.md, from results/runs.csv alone, with no date, so a rerun on the same
# runs writes it byte for byte. One row per scenario as built, then the planted fault's rows beneath.
import csv
from math import comb

from check import CHECKS, RESULTS

SCENARIOS = {
    "S1": "Ask, then switch plan before the reply",
    "S2": "Switch plan, then ask",
    "S3": "Compare two plans, then ask",
    "S4": "Reload mid-reply",
    "S5": "Two tabs ask on different plans at once",
    "S6": "Press Open Plan on a hidden plan a reply offers",
}
WORDS = {
    "in_right_chat": "a reply outside the chat of the plan or pair it names",
    "exchanges_once": "a chat not holding exactly its own exchanges, once each",
    "address_matches_chat": "the address's plan not matching the chat's",
    "plan_set_unchanged": "her plan set changed",
}


def pass_k(consistent: int, runs: int, k: int) -> float:
    # Equation 2.2's estimate from one scenario's runs: the chance that k runs all stay consistent
    return comb(consistent, k) / comb(runs, k) if runs >= k else float("nan")


def table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Scenario | Runs | Races provoked | Inconsistent runs | pass^10 | What failed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for scenario, title in SCENARIOS.items():
        runs = [row for row in rows if row["scenario"] == scenario]
        if not runs:
            continue
        bad = [row for row in runs if row["consistent"] == "no"]
        failed = sorted(
            {check for row in bad for check in CHECKS if row[check] == "fail"}
        )
        lines.append(
            f"| {scenario}: {title} | {len(runs)} | {sum(row['race'] == 'yes' for row in runs)} | "
            f"{len(bad)} | {pass_k(len(runs) - len(bad), len(runs), 10):.2f} | "
            f"{'; '.join(WORDS[check] for check in failed) or 'nothing'} |"
        )
    return lines


def causes(rows: list[dict[str, str]]) -> list[str]:
    path = RESULTS / "causes.csv"
    found = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as file:
            found = {
                (c["scenario"], c["run"], c["planted"]): c for c in csv.DictReader(file)
            }
    lines = [
        "| Scenario | Run | Planted fault | Cause | What the run saw |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        if row["consistent"] == "yes":
            continue
        cause = found.get((row["scenario"], row["run"], row["planted"]), {})
        lines.append(
            f"| {row['scenario']} | {row['run']} | {row['planted']} | "
            f"{cause.get('cause', 'to be classed')} | {cause.get('note', '')} |"
        )
    return lines


def main() -> None:
    with (RESULTS / "runs.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    built = [row for row in rows if row["planted"] == "no"]
    planted = [row for row in rows if row["planted"] == "yes"]
    caught = [row["scenario"] for row in planted if row["consistent"] == "no"]
    lines = [
        "# ATP-4: context consistency",
        "",
        (
            "report.py wrote this from runs.csv, one row per run. Each scenario ran ten times, "
            "with delays of 0 to 8 s and switch times drawn inside them from seed 4022. A run is "
            "consistent when all four checks pass: each reply sits in the chat of the plan or pair "
            "it names, each chat holds exactly its own exchanges once each, after a reload too, the "
            "address's plan matches the chat's, and her plan set is unchanged except that a hidden "
            "plan offered by Open Plan joins the shown list. pass^10 is the chance that ten runs all "
            "stay consistent, Equation 2.2's estimate from the scenario's runs."
        ),
        "",
        "## The scenarios as built",
        "",
        *table(built),
        "",
        (
            "Regenerate after a record change: not applicable, as version 1 allows no change to "
            "her record after setup."
        ),
        "",
        "## The planted fault",
        "",
        (
            "planted-fault.patch makes the assistant write each returned exchange into whichever "
            "chat is open when it lands. With it applied, S1 and S5 ran ten times each again, with "
            "the same delays and switch times."
        ),
        "",
        *table(planted),
        "",
        (
            f"The test caught it: {len(caught)} inconsistent runs, in "
            f"{', '.join(sorted(set(caught)))}."
            if caught
            else "The test didn't catch it: every run stayed consistent."
        ),
        "",
        "## Every inconsistent run, with its cause",
        "",
        "The cause is my judgement, read at Stop 3 from what the run saw, as `causes.csv` holds it.",
        "",
        *causes(rows),
    ]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("results/report.md written")


if __name__ == "__main__":
    main()
