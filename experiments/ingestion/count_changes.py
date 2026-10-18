# Counts the rules that changed between two approved handbook years, from their snapshots in
# data/rules/<year>/rulebook.json, for the change-control record in README.md. Entry rules count per
# course, curriculum rules per curriculum's year of study, course lists per entry, and courses by the
# facts a plan reads: name, credits, NQF level and term. A convener is shown, not a rule, so a change
# to one is counted apart. Run from experiments/ingestion/: uv run python count_changes.py 2023 2026
import sys
from collections.abc import Hashable

from sage.services.ingest import approved_snapshot
from sage.shared.rules import RuleSet

# What a year holds of one kind, by what identifies each
Keyed = dict[Hashable, object]


def changes(before: Keyed, after: Keyed) -> tuple[int, int, int]:
    # Keys added and removed, and those in both whose value differs
    shared = before.keys() & after.keys()
    return (
        len(after.keys() - before.keys()),
        len(before.keys() - after.keys()),
        sum(before[key] != after[key] for key in shared),
    )


def kinds(rules: RuleSet) -> dict[str, Keyed]:
    # Each kind of rule one approved year holds
    return {
        "Entry rules": {
            c.code: c.entry_rule for c in rules.courses if c.entry_rule is not None
        },
        "Curriculum rules": {
            (r.curriculum_code, r.year_of_study): r.rule for r in rules.curriculum_rules
        },
        "Course list entries": {
            (m.group_key, m.course_code): m.category for m in rules.course_group_members
        },
        "Courses": {
            c.code: (c.name, c.credits, c.nqf_level, c.term) for c in rules.courses
        },
        "Equivalences": {
            (e.course_code, e.counts_as): None for e in rules.equivalences
        },
    }


def conveners(rules: RuleSet) -> Keyed:
    return {c.code: c.convener for c in rules.courses}


def main(first: int, second: int) -> None:
    old, new = approved_snapshot(first).rules, approved_snapshot(second).rules
    before, after = kinds(old), kinds(new)
    print(f"| Changed from {first} to {second} | Added | Removed | Changed |")
    print("| --- | --- | --- | --- |")
    for name in before:
        added, removed, changed = changes(before[name], after[name])
        print(f"| {name} | {added} | {removed} | {changed} |")
    moved = changes(conveners(old), conveners(new))[2]
    print(
        f"\nConveners changed on {moved} courses in both years, not counted as rules."
    )


if __name__ == "__main__":
    first, second = map(int, sys.argv[1:])
    main(first, second)
