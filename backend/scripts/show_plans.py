# Prints a student's plan set, with its reasons and slots, against an approved year's snapshot,
# data/rules/<year>/rulebook.json, with no database: for the student in a seed file, or for one on
# track in a curriculum and year, who has passed every course before it. The result symbols come
# from the tests' copy of the migration's rows.
# From backend/: uv run python scripts/show_plans.py --seed ../data/synthetic/mbali.json
# or: uv run python scripts/show_plans.py --curriculum EB011EEE05 --year 3
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from uuid import UUID

from sage.engine import printed
from sage.engine.generator import ClingoPlanGenerator, groups
from sage.ingestion.ingest import approved_snapshot
from sage.shared.rules import (
    COMPLEMENTARY,
    TERM_BY_SUFFIX,
    CreditsFromGroups,
    ResultSymbol,
    RuleSet,
)
from sage.shared.seed import load_seed
from sage.shared.students import CourseHistoryLine, PlanReason, PlanSetRows, Student

SYMBOLS = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "result_symbols.json"
)
ACCOUNT = UUID(int=1)  # a made-up account, as nothing is stored


def on_track(rules: RuleSet, curriculum: str, year: int) -> tuple[Student, list]:
    # A student in this year who has passed every course her earlier years' groups name, an
    # approved complementary course for each earlier year's complementary credits, and, on the
    # 576-credit curriculum, each course its footnotes place earlier
    (version,) = rules.handbook_versions
    intake = version.year - year + 1
    courses = {course.code: course for course in rules.courses}
    members: dict[str, list[str]] = defaultdict(list)
    for member in rules.course_group_members:
        members[member.group_key].append(member.course_code)
    by_year = {
        rule.year_of_study: rule.rule.all
        for rule in rules.curriculum_rules
        if rule.curriculum_code == curriculum
    }
    passed: dict[str, tuple[int, int]] = {}  # each code, with its year and credits
    for number in range(1, year):
        for part in by_year[number]:
            if isinstance(part, CreditsFromGroups) and part.from_groups == (
                COMPLEMENTARY,
            ):
                choice = next(
                    (
                        code
                        for code in sorted(members[COMPLEMENTARY])
                        if courses[code].credits >= part.credits and code not in passed
                    ),
                    None,
                )
                if choice:
                    passed[choice] = (number, courses[choice].credits)
                continue
            for group in groups(part):
                for code in members[group]:
                    passed[code] = (number, courses[code].credits)
    if version.year == printed.PLACES_YEAR and intake < printed.CHANGE:
        for place in printed.PLACES.get(curriculum, ()):
            if place.year < year:
                passed[place.code] = (place.year, place.credits)
    student = Student(id=ACCOUNT, curriculum_code=curriculum, intake_year=intake)
    history = [
        CourseHistoryLine(
            student_id=ACCOUNT,
            academic_year=intake + number - 1,
            term=TERM_BY_SUFFIX[code[-1]],
            course_code=code,
            course_name=courses[code].name if code in courses else code,
            credits=credits,
            result="1",
            mark=75,
        )
        for code, (number, credits) in passed.items()
    ]
    return student, history


def show(rows: PlanSetRows, rules: RuleSet, took: float) -> None:
    passages = {passage.id: passage for passage in rules.passages}
    credits = {course.code: course.credits for course in rules.courses}

    def said(reason: PlanReason, indent: str) -> None:
        passage = passages.get(reason.passage_id)
        cited = f"{passage.section}, p. {passage.page}" if passage else "no passage"
        print(f"{indent}[{reason.kind}] {reason.message} ({cited})")
        if reason.details:
            print(f"{indent}  fits: {', '.join(reason.details['fits']) or 'none'}")
            print(
                f"{indent}  untimed: {', '.join(reason.details['untimed']) or 'none'}"
            )

    print(f"{len(rows.plans)} plans in {took:.2f} s\n")
    for reason in rows.plan_reasons:
        if reason.plan_id is None:
            said(reason, "")
    for plan in rows.plans:
        held = [row for row in rows.plan_courses if row.plan_id == plan.id]
        total = sum(credits[row.course_code] for row in held)
        print(f"\n{plan.position}. {plan.name}, {total} credits")
        print(
            "   "
            + ", ".join(
                row.course_code
                + "".join(
                    f" ({group} {choice})"
                    for group, choice in (row.choices or {}).items()
                )
                for row in held
            )
        )
        for reason in rows.plan_reasons:
            if reason.plan_id == plan.id:
                said(reason, "   ")


def main() -> None:
    parser = argparse.ArgumentParser(prog="show_plans")
    parser.add_argument(
        "--rules", type=int, default=2026, help="the approved year to read"
    )
    parser.add_argument(
        "--seed", type=Path, help="a seed file whose student to plan for"
    )
    parser.add_argument(
        "--curriculum", help="a curriculum code, for an on-track student"
    )
    parser.add_argument(
        "--year", type=int, help="her year of study, for an on-track student"
    )
    arguments = parser.parse_args()
    if bool(arguments.seed) == bool(arguments.curriculum and arguments.year):
        parser.error("give --seed, or --curriculum with --year")
    rules = approved_snapshot(arguments.rules).rules
    if arguments.seed:
        seeded = load_seed(arguments.seed, ACCOUNT)
        student, history = seeded.student, list(seeded.course_history)
    else:
        student, history = on_track(rules, arguments.curriculum, arguments.year)
    symbols = {
        row["symbol"]: ResultSymbol.model_validate(row)
        for row in json.loads(SYMBOLS.read_text(encoding="utf-8"))
    }
    start = time.perf_counter()
    rows = ClingoPlanGenerator().generate(student, history, rules, symbols)
    show(rows, rules, time.perf_counter() - start)


if __name__ == "__main__":
    main()
