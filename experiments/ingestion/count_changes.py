# Counts the rules that changed between two approved handbook years, from their snapshots in
# data/rules/<year>/rulebook.json, for the change-control record in README.md. Entry rules count per
# course, curriculum rules per curriculum's year of study, course lists per entry, and courses by the
# facts a plan reads: name, credits, NQF level and term. A convener is shown, not a rule, so a change
# to one is counted apart. Run from experiments/ingestion/: uv run python count_changes.py 2023 2026
import sys

from sage.services.ingest import approved_snapshot


def changes(before: dict, after: dict) -> tuple[int, int, int]:
    # Keys added and removed, and those in both whose value differs
    shared = before.keys() & after.keys()
    return (
        len(after.keys() - before.keys()),
        len(before.keys() - after.keys()),
        sum(before[key] != after[key] for key in shared),
    )


def main(first: int, second: int) -> None:
    years = [approved_snapshot(year).rules for year in (first, second)]
    kinds = {
        "Entry rules": lambda rules: {
            c.code: c.entry_rule for c in rules.courses if c.entry_rule is not None
        },
        "Curriculum rules": lambda rules: {
            (r.curriculum_code, r.year_of_study): r.rule for r in rules.curriculum_rules
        },
        "Course list entries": lambda rules: {
            (m.group_key, m.course_code): m.category for m in rules.course_group_members
        },
        "Courses": lambda rules: {
            c.code: (c.name, c.credits, c.nqf_level, c.term) for c in rules.courses
        },
        "Equivalences": lambda rules: {
            (e.course_code, e.counts_as): None for e in rules.equivalences
        },
    }
    print(f"| Changed from {first} to {second} | Added | Removed | Changed |")
    print("| --- | --- | --- | --- |")
    for name, rows in kinds.items():
        added, removed, changed = changes(*(rows(rules) for rules in years))
        print(f"| {name} | {added} | {removed} | {changed} |")
    conveners = changes(
        *({c.code: c.convener for c in rules.courses} for rules in years)
    )[2]
    print(
        f"\nConveners changed on {conveners} courses in both years, not counted as rules."
    )


if __name__ == "__main__":
    main(*map(int, sys.argv[1:]))
