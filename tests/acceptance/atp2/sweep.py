# ATP-2's sweep of made-up records, with seed 4022. Each curriculum and continuing year gets an
# on-track record built from the approved 2026 curriculum tables. From each one come a record per
# previous-year core course failed and one per course with a supplementary pending, first-year maths
# and physics failed together where they're core, and an arrears variant of each failure that also
# passes two of her own year's courses. run.py writes them to results/sweep/ in the seed file's shape.
import csv
import json
import random
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from checker.plans import FIRST_560, PLACES, Curriculum
from checker.record import Covers

from sage.shared.rules import (
    COMPLEMENTARY,
    AllOf,
    AllOfGroup,
    AnyOf,
    ChooseFromGroup,
    Course,
    CourseNeed,
    CreditsFromGroups,
    EntryRule,
    RuleSet,
    TotalCredits,
)

SEED = 4022
FAILED = ("F", 40)
DEFERRED = ("FS", 46)  # a fail with a supplementary exam allowed
# Failed together on the 4-year curricula's year-2 records, as first-year maths and physics
MATHS_AND_PHYSICS = ("MAM1020F", "PHY1012F")
# The 2026 rules print no entry for ASL1200S, so its line is as the 2023 rules hold it (p. 167)
ASL1200S = Course(
    handbook_year=2023,
    code="ASL1200S",
    name="Africa: Culture, ID & Globalisation",
    credits=8,
    nqf_level=5,
    term="sem2",
)
MANIFEST = ("record", "curriculum", "intake", "year", "kind", "course", "base")


@dataclass(frozen=True)
class Made:
    record: str  # its id, which names its file
    curriculum: str
    intake: int
    year: int  # the year of study her on-track record reaches
    kind: str  # base, fail, supplementary or arrears
    course: str  # the course failed or deferred, or both joined by +
    base: str  # the on-track record it comes from
    history: tuple[dict[str, Any], ...]


def symbol(mark: int) -> str:
    # UCT's classes, as the result_symbols table labels them
    if mark >= 75:
        return "1"
    if mark >= 70:
        return "2+"
    return "2-" if mark >= 60 else "3"


def passed(course: Course, year: int, rng: random.Random) -> dict[str, Any]:
    # A pass with a plausible mark, or PA for practical training, which prints none
    mark = None if course.code.endswith("X") else rng.randint(55, 85)
    return {
        "academic_year": year,
        "term": course.term,
        "course_code": course.code,
        "course_name": course.name,
        "credits": course.credits,
        "nqf_level": course.nqf_level,
        "result": "PA" if mark is None else symbol(mark),
        "mark": mark,
    }


def leaves(rule: EntryRule | None) -> set[str]:
    # Every course an entry rule names
    match rule:
        case AllOf():
            return set().union(*map(leaves, rule.all))
        case AnyOf():
            return set().union(*map(leaves, rule.any))
        case CourseNeed():
            return {rule.course}
    return set()


def electives(tables: Curriculum, credits: dict[str, int], year: int) -> set[str]:
    # The cheapest set of a year's electives that meets its choose and credits rules and its
    # printed total, fewest courses and then code order breaking ties
    rules = tables.years[year]
    asked = [
        rule
        for rule in rules
        if isinstance(rule, ChooseFromGroup)
        or (
            isinstance(rule, CreditsFromGroups) and rule.from_groups != (COMPLEMENTARY,)
        )
    ]
    if not asked:
        return set()

    def credit(codes: set[str]) -> int:
        return sum(credits[code] for code in codes)

    total = next(rule.total_credits for rule in rules if isinstance(rule, TotalCredits))
    lines = sum(
        rule.credits
        for rule in rules
        if isinstance(rule, CreditsFromGroups) and rule.from_groups == (COMPLEMENTARY,)
    )
    load = credit(tables.core(year)) + lines
    pool = sorted(set().union(*(tables.named(rule) for rule in asked)))

    def meets(chosen: set[str]) -> bool:
        return load + credit(chosen) >= total and all(
            len(chosen & tables.named(rule)) >= rule.choose
            if isinstance(rule, ChooseFromGroup)
            else credit(chosen & tables.named(rule)) >= rule.credits
            for rule in asked
        )

    sets = (set(s) for size in range(len(pool) + 1) for s in combinations(pool, size))
    return min(
        filter(meets, sets),
        key=lambda s: (credit(s), len(s), sorted(s)),
    )


def made(rules: RuleSet) -> list[Made]:
    rng = random.Random(SEED)
    courses = {course.code: course for course in rules.courses}
    credits = {code: course.credits for code, course in courses.items()}
    covers = Covers(rules)
    # One fixed approved complementary course for every earlier line: the first by code at the
    # line's 18 credits with no entry rule
    approved = {
        m.course_code
        for m in rules.course_group_members
        if m.group_key == COMPLEMENTARY
    }
    complementary = min(
        code
        for code in approved
        if courses[code].credits == 18 and courses[code].entry_rule is None
    )
    found = []
    for curriculum in sorted(c.code for c in rules.curricula):
        tables = Curriculum(rules, curriculum)
        for year in range(2, tables.final + 1):
            found += records(
                tables, curriculum, year, courses, credits, covers, complementary, rng
            )
    return found


def records(
    tables: Curriculum,
    curriculum: str,
    year: int,
    courses: dict[str, Course],
    credits: dict[str, int],
    covers: Covers,
    complementary: str,
    rng: random.Random,
) -> Iterator[Made]:
    intake = 2026 - (year - 1)
    places = PLACES[curriculum] if intake < FIRST_560 else {}
    held = {**courses, ASL1200S.code: ASL1200S}
    history = []
    for y in range(1, year):
        taken = intake + y - 1
        for rule in tables.years[y]:
            if isinstance(rule, AllOfGroup):
                history += [
                    passed(courses[code], taken, rng)
                    for code in sorted(tables.members[rule.all_of_group])
                ]
            elif isinstance(rule, CreditsFromGroups) and rule.from_groups == (
                COMPLEMENTARY,
            ):
                history.append(passed(courses[complementary], taken, rng))
        history += [
            passed(courses[code], taken, rng)
            for code in sorted(electives(tables, credits, y))
        ]
        # A 576-credit place's own course, passed in the year its footnote marks
        history += [
            passed(held[code], taken, rng)
            for code, at in sorted(places.items())
            if at == y
        ]
    base = f"{curriculum}-y{year}-base"

    def record(kind: str, course: str, lines: list[dict[str, Any]]) -> Made:
        name = base if kind == "base" else f"{curriculum}-y{year}-{kind}-{course}"
        return Made(name, curriculum, intake, year, kind, course, base, tuple(lines))

    def with_results(
        codes: Sequence[str], result: tuple[str, int]
    ) -> list[dict[str, Any]]:
        symbol, mark = result
        return [
            {**line, "result": symbol, "mark": mark}
            if line["course_code"] in codes
            else line
            for line in history
        ]

    def arrears(codes: Sequence[str]) -> list[dict[str, Any]]:
        # Passes in the first two of her own year's core courses, by code, whose entry rules name
        # nothing the failed courses cover, so FB5 puts her in her year owing them
        failed = set().union(*(covers(code, held[code].credits) for code in codes))
        early = [
            code
            for code in sorted(tables.core(year))
            if not leaves(courses[code].entry_rule) & failed
        ]
        return [passed(courses[code], intake + year - 2, rng) for code in early[:2]]

    yield record("base", "", history)
    previous = sorted(tables.core(year - 1)) + sorted(
        code for code, at in places.items() if at == year - 1
    )
    failures = [(code,) for code in previous]
    if year == 2 and set(MATHS_AND_PHYSICS) <= tables.core(1):
        failures.append(MATHS_AND_PHYSICS)
    for codes in failures:
        course = "+".join(codes)
        failing = with_results(codes, FAILED)
        yield record("fail", course, failing)
        yield record("arrears", course, failing + arrears(codes))
        if len(codes) == 1:
            yield record("supplementary", course, with_results(codes, DEFERRED))


def write(records: Sequence[Made], folder: Path) -> None:
    # Each record as a seed file, which load_seed reads, and the manifest saying what each is
    folder.mkdir(parents=True, exist_ok=True)
    for one in records:
        student = {
            "curriculum_code": one.curriculum,
            "intake_year": one.intake,
            "onboarding_complete": True,
        }
        seed = {"students": [student], "course_history": list(one.history)}
        (folder / f"{one.record}.json").write_text(
            json.dumps(seed, indent=2) + "\n", encoding="utf-8"
        )
    with (folder / "manifest.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(MANIFEST)
        writer.writerows(
            (r.record, r.curriculum, r.intake, r.year, r.kind, r.course, r.base)
            for r in records
        )
