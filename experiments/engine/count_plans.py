# /// script
# requires-python = ">=3.12"
# ///
# Counts the plans an on-track student has in each curriculum and year from 2, under the two ways a
# plan could hold complementary studies, for Table 1 in README.md. A plan holds the year's core and
# a minimal set of its electives, so that none can be dropped with the year's rules still met, and no
# two of its courses clash. Courses with alternative sections are tested pair by pair, so a plan
# counts when each pair has some clash-free choice, which makes every count an upper bound. Entry
# rules are ignored, as an on-track student meets them. It reads the approved snapshot with the
# standard library alone, so it shares no code with the engine.
# Run from experiments/engine/: uv run count_plans.py 2026
import json
import sys
from collections import defaultdict
from itertools import combinations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPLEMENTARY = "complementary"
# The quarters run inside their semester
INSIDE = {"q1": "sem1", "q2": "sem1", "q3": "sem2", "q4": "sem2"}


def terms_overlap(a: str, b: str) -> bool:
    # A full year overlaps both semesters and every quarter, and winter and summer only themselves
    if a == b:
        return True
    if {a, b} & {"winter", "summer", "other"}:
        return False
    return "full_year" in (a, b) or INSIDE.get(a) == b or INSIDE.get(b) == a


def clash(m: dict, n: dict) -> bool:
    # A meeting with no printed day or time can't be placed, so it never clashes
    if None in (m["day"], m["start_time"], n["day"], n["start_time"]):
        return False
    return (
        m["day"] == n["day"]
        and terms_overlap(m["term"], n["term"])
        and m["start_time"] < n["end_time"]
        and n["start_time"] < m["end_time"]
    )


class Year:
    # One approved handbook year, with each course's ways of attending worked out once
    def __init__(self, year: int) -> None:
        path = ROOT / "data" / "rules" / str(year) / "rulebook.json"
        rules = json.loads(path.read_text(encoding="utf-8"))["rules"]
        self.credits = {c["code"]: c["credits"] for c in rules["courses"]}
        self.members: dict[str, list[str]] = defaultdict(list)
        for member in rules["course_group_members"]:
            self.members[member["group_key"]].append(member["course_code"])
        self.rules = {
            (r["curriculum_code"], r["year_of_study"]): r["rule"]["all"]
            for r in rules["curriculum_rules"]
        }
        self.linked: dict[str, set[str]] = defaultdict(set)
        for link in rules["timetable_slot_curricula"]:
            self.linked[link["slot_id"]].add(link["curriculum_code"])
        self.slots: dict[str, list[dict]] = defaultdict(list)
        for slot in rules["timetable_slots"]:
            self.slots[slot["course_code"]].append(slot)
        self._ways: dict[tuple[str, str], list[list[dict]]] = {}
        self._fit: dict[tuple[str, str, str], bool] = {}

    def ways(self, code: str, curriculum: str) -> list[list[dict]]:
        # Each way of attending a course: its compulsory meetings and one alternative per choice
        # group. A meeting linked to curricula is theirs alone.
        key = (code, curriculum)
        if key not in self._ways:
            meetings = [
                s
                for s in self.slots[code]
                if s["id"] not in self.linked or curriculum in self.linked[s["id"]]
            ]
            groups: dict[str, dict[str, list[dict]]] = defaultdict(
                lambda: defaultdict(list)
            )
            for s in meetings:
                if s["choice_group"]:
                    groups[s["choice_group"]][s["choice"]].append(s)
            compulsory = [s for s in meetings if not s["choice_group"]]
            self._ways[key] = [
                compulsory + [m for picked in choice for m in picked]
                for choice in product(*(g.values() for g in groups.values()))
            ]
        return self._ways[key]

    def fit(self, a: str, b: str, curriculum: str) -> bool:
        # Whether two courses have some clash-free way of attending both
        key = (min(a, b), max(a, b), curriculum)
        if key not in self._fit:
            self._fit[key] = any(
                not any(clash(m, n) for m in x for n in y)
                for x in self.ways(a, curriculum)
                for y in self.ways(b, curriculum)
            )
        return self._fit[key]


def minimal_sets(pool: list[str], meets) -> list[tuple]:
    # Every subset that meets the rules with no member spare. The rules only ever ask for at least
    # something, so once every set of one size meets them, each larger set holds one and has a
    # spare member, and the search stops there.
    found = []
    for size in range(len(pool) + 1):
        every = True
        for chosen in combinations(pool, size):
            if not meets(chosen):
                every = False
            elif not any(meets(tuple(c for c in chosen if c != d)) for d in chosen):
                found.append(chosen)
        if every:
            break
    return found


def count(year: Year, curriculum: str, year_of_study: int) -> dict:
    parts = year.rules[(curriculum, year_of_study)]
    # Practical training (X) has no credits or meetings, so it changes no count
    core = [
        code
        for part in parts
        if "all_of_group" in part
        for code in year.members[part["all_of_group"]]
        if not code.endswith("X")
    ]
    chooses = [(p["choose"], p["from_group"]) for p in parts if "choose" in p]
    sums = [(p["credits"], p["from_groups"]) for p in parts if "credits" in p]
    total = next(p["total_credits"] for p in parts if "total_credits" in p)
    slot = sum(n for n, groups in sums if groups == [COMPLEMENTARY])
    elective_sums = [(n, groups) for n, groups in sums if groups != [COMPLEMENTARY]]
    groups = {g for _, g in chooses} | {g for _, gs in elective_sums for g in gs}
    pool = sorted({c for g in groups for c in year.members[g]} - set(core))
    core_credits = sum(year.credits[c] for c in core)

    def meets(chosen: tuple) -> bool:
        held = set(chosen)
        return (
            all(len(held & set(year.members[g])) >= n for n, g in chooses)
            and all(
                sum(
                    year.credits[c]
                    for c in held
                    if any(c in year.members[g] for g in gs)
                )
                >= n
                for n, gs in elective_sums
            )
            and core_credits + sum(year.credits[c] for c in held) + slot >= total
        )

    plans = []
    for electives in minimal_sets(pool, meets):
        courses = core + list(electives)
        if all(year.fit(a, b, curriculum) for a, b in combinations(courses, 2)):
            plans.append(courses)

    complementary = sorted(year.members[COMPLEMENTARY])
    fits, members = [], []
    for courses in plans:
        fitting = [
            k for k in complementary if all(year.fit(k, c, curriculum) for c in courses)
        ]
        fits.append(len(fitting))
        if not slot:
            members.append(1)
            continue
        # Each complementary course a plan member: every minimal set of fitting courses that
        # reaches the slot's credits, with no two of them clashing
        reach = [
            chosen
            for chosen in minimal_sets(
                fitting, lambda chosen: sum(year.credits[c] for c in chosen) >= slot
            )
            if all(year.fit(a, b, curriculum) for a, b in combinations(chosen, 2))
        ]
        members.append(len(reach))
    return {
        "curriculum": curriculum,
        "year": year_of_study,
        "years": max(y for c, y in year.rules if c == curriculum),
        "choices": len(pool),
        "slot": slot,
        "plans": len(plans),
        "members": sum(members),
        "fits": fits,
        # A 576-credit student's places multiply each plan by the courses that fit it, once a place
        "one_place": sum(m * f for m, f in zip(members, fits, strict=True)),
        "two_places": sum(m * f * f for m, f in zip(members, fits, strict=True)),
    }


def span(values: list[int]) -> str:
    low, high = min(values), max(values)
    return f"{low:,}" if low == high else f"{low:,} to {high:,}"


def main(handbook_year: int) -> None:
    year = Year(handbook_year)
    cases = [
        count(year, curriculum, y) for curriculum, y in sorted(year.rules) if y >= 2
    ]
    print(
        "| Curriculum | Year | Open EEE choices | Plans, each complementary course a member "
        "| Plans, complementary credits as one slot | Complementary courses that fit each plan |"
    )
    print("| --- | --- | --- | --- | --- | --- |")
    for case in cases:
        fits = span(case["fits"]) if case["slot"] else "None needed"
        print(
            f"| {case['curriculum']} | {case['year']} | {case['choices']} | {case['members']:,} "
            f"| {case['plans']} | {fits} |"
        )

    final = [c for c in cases if c["year"] == c["years"]]
    four = [c for c in cases if c["slot"] and c["years"] == 4]
    five = [c for c in cases if c["slot"] and c["years"] == 5]
    rows = [
        ("Final year, all six curricula", final, "members", "None needed"),
        ("Year 3", four, "members", None),
        ("ASPECT year with complementary credits", five, "members", None),
        (
            "Year 3, 576-credit student owing one complementary place",
            four,
            "one_place",
            None,
        ),
        ("Year 3, 576-credit student owing two places", four, "two_places", None),
    ]
    print(f"\nTable 1 from the approved {handbook_year}:\n")
    print(
        "| Case | Open EEE choices | Plans, each complementary course a member "
        "| Plans, complementary credits as one slot | Complementary courses that fit each plan |"
    )
    print("| --- | --- | --- | --- | --- |")
    for label, group, column, fits in rows:
        names = ", ".join(f"{c['curriculum']} y{c['year']}" for c in group)
        fitting = fits or span([f for c in group for f in c["fits"]])
        print(
            f"| {label} ({names}) | {span([c['choices'] for c in group])} "
            f"| {span([c[column] for c in group])} | {span([c['plans'] for c in group])} "
            f"| {fitting} |"
        )


if __name__ == "__main__":
    main(int(sys.argv[1]))
