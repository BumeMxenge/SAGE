# ATP-2's run: the engine and the checker on every record, each timed, then compared, with three
# metamorphic relations on every sweep record. It writes one CSV per kind to results/, and
# report.py writes report.md from them alone. make atp2 runs it from backend/ once the checker's
# tests pass. It never edits what it tests and calls no model.
import csv
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

import sweep
from checker.plans import Checked, Curriculum, check
from checker.record import DONE, FAILED, Covers, Record

from sage.engine.eligibility import EntryRuleEligibility
from sage.engine.generator import ClingoPlanGenerator
from sage.ingestion.ingest import DATA, approved_snapshot
from sage.shared.planning import Eligibility
from sage.shared.printed_meetings import timetabled
from sage.shared.rules import COMPLEMENTARY, Course, ResultSymbol, RuleSet
from sage.shared.seed import load_seed
from sage.shared.students import (
    CourseHistoryLine,
    PlanReason,
    PlanSetRows,
    Student,
)

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RULEBOOK = DATA / "rules" / "2026" / "rulebook.json"
SYMBOLS = HERE.parents[2] / "backend" / "tests" / "fixtures" / "result_symbols.json"
ACCOUNT = UUID(int=sweep.SEED)  # the made-up account every record loads onto
REPEATS = 5  # runs of generate on each record, the first of which is compared
CAP = 50  # the most plans the engine keeps
GENERATOR = ClingoPlanGenerator()
ELIGIBILITY = EntryRuleEligibility()
# The base records are in-sample, as the engine was built on on-track students
SETS = {
    "base": "base",
    "fail": "failure",
    "supplementary": "failure",
    "arrears": "failure",
}


@dataclass(frozen=True)
class Engine:
    # What the engine gave for one record, in the checker's terms: each plan's courses in the
    # engine's order, each plan's slots, every reason and each course's eligibility
    plans: list[frozenset[str]]
    ids: dict[frozenset[str], list[UUID]]
    slots: dict[UUID, list[tuple[int, str | None, frozenset[str]]]]
    reasons: tuple[PlanReason, ...]
    statuses: dict[str, Eligibility]


def read(rows: PlanSetRows, statuses: dict[str, Eligibility]) -> Engine:
    courses: dict[UUID, set[str]] = defaultdict(set)
    for row in rows.plan_courses:
        courses[row.plan_id].add(row.course_code)
    plans = [frozenset(courses[plan.id]) for plan in rows.plans]
    ids: dict[frozenset[str], list[UUID]] = defaultdict(list)
    for plan, codes in zip(rows.plans, plans, strict=True):
        ids[codes].append(plan.id)
    slots: dict[UUID, list[tuple[int, str | None, frozenset[str]]]] = defaultdict(list)
    for reason in rows.plan_reasons:
        if reason.details and reason.plan_id:
            slots[reason.plan_id].append(
                (
                    reason.details["credits"],
                    reason.details.get("owed"),
                    frozenset(reason.details["fits"]),
                )
            )
    return Engine(plans, ids, slots, rows.plan_reasons, statuses)


def codes(sets: Iterable[frozenset[str]]) -> str:
    # Plans as a CSV cell: each plan's codes joined with spaces, plans with " | "
    return " | ".join(sorted(" ".join(sorted(s)) for s in sets))


def names(reason: PlanReason, code: str) -> bool:
    return reason.course_code == code or code in reason.message


def difference(want: frozenset[str] | None, got: frozenset[str] | None) -> str:
    # How the engine's list for one slot differs from the checker's
    if got is None:
        return "not given"
    if want is None:
        return "given, though not expected"
    return (
        f"fits missing {' '.join(sorted(want - got)) or 'none'}, "
        f"extra {' '.join(sorted(got - want)) or 'none'}"
    )


def compared(
    checked: Checked, engine: Engine, core: set[str]
) -> tuple[dict[str, Any], list[tuple[str, str, str, str]]]:
    # The engine against the checker on one record: its plan sets, each plan's slots and the
    # conditional reasons its judged courses need, then every status the checker gives
    found = Counter(engine.plans)
    expected = set(checked.plans)
    missing = expected - set(found)
    extra = set(found) - expected
    duplicate = sum(n - 1 for n in found.values())
    # Past the cap the engine keeps its best 50, so 50 of the valid plans are expected
    capped = len(expected) > CAP
    short = max(0, CAP - len(expected & set(found))) if capped else len(missing)
    if capped:
        missing = set()
    slots = wrong = judged = judged_wrong = 0
    detail = []
    for plan in sorted(expected & set(found), key=sorted):
        plan_id, name = engine.ids[plan][0], " ".join(sorted(plan))
        theirs = Counter((s.credits, s.owed, s.fits) for s in checked.slots[plan])
        ours = Counter(engine.slots.get(plan_id, []))
        size = max(theirs.total(), ours.total())
        slots += size
        wrong += size - (theirs & ours).total()
        expect = {(c, owed): fits for c, owed, fits in theirs}
        given = {(c, owed): fits for c, owed, fits in ours}
        for credits, owed in sorted(set(expect) | set(given), key=str):
            want, got = expect.get((credits, owed)), given.get((credits, owed))
            if want != got:
                detail.append(
                    f"{name}: slot {owed or credits}: {difference(want, got)}"
                )
        resting = checked.judged[plan]
        if resting:
            judged += 1
            unnamed = [
                code
                for code in sorted(resting)
                if not any(
                    r.kind == "conditional"
                    and r.plan_id in (plan_id, None)
                    and names(r, code)
                    for r in engine.reasons
                )
            ]
            judged_wrong += bool(unnamed)
            if unnamed:
                detail.append(
                    f"{name}: no conditional reason names {' '.join(unnamed)}"
                )
    kinds = Counter(r.kind for r in engine.reasons)
    row = {
        "checker_year": checked.year,
        "engine_plans": len(engine.plans),
        "checker_plans": len(checked.plans),
        "missing": short,
        "extra": len(extra),
        "duplicate": duplicate,
        "capped": "yes" if capped else "no",
        "plans_match": "yes" if not (short or extra or duplicate) else "no",
        "missing_plans": codes(missing),
        "extra_plans": codes(extra),
        "slots": slots,
        "slots_wrong": wrong,
        "judged_plans": judged,
        "judged_wrong": judged_wrong,
        "engine_excluded": " ".join(
            sorted(
                {
                    r.course_code
                    for r in engine.reasons
                    if r.kind == "excluded" and r.course_code in core
                }
            )
        ),
        "checker_excluded": " ".join(sorted(checked.excluded)),
        "engine_dropped": " ".join(
            sorted(
                {
                    r.course_code
                    for r in engine.reasons
                    if r.kind == "conflict" and r.course_code
                }
            )
        ),
        "checker_dropped": " ".join(sorted(checked.dropped)),
        "conditional_courses": len(
            {
                r.course_code
                for r in engine.reasons
                if r.kind == "conditional" and r.course_code
            }
        ),
        **{
            f"reasons_{kind}": kinds[kind]
            for kind in ("excluded", "conflict", "conditional", "included")
        },
        "candidates": checked.candidates,
        "detail": "; ".join(detail),
    }
    decisions = [
        (
            code,
            engine.statuses[code].status,
            checked.statuses[code],
            engine.statuses[code].reason or "",
        )
        for code in sorted(engine.statuses)
    ]
    return row, decisions


def timed[T](call: Callable[[], T]) -> tuple[T, float]:
    start = time.perf_counter()
    found = call()
    return found, time.perf_counter() - start


def ran(
    student: Student,
    history: Sequence[CourseHistoryLine],
    rules: RuleSet,
    symbols: Mapping[str, ResultSymbol],
    focal: Iterable[str] = (),
) -> tuple[Checked, Engine, list[Course], dict[str, Any]]:
    # The checker once, then generate five times, comparing the first, and check once, each timed,
    # on the courses in her year's groups and the focal courses
    checked, checker = timed(lambda: check(student, history, rules, symbols))
    wanted = checked.groups | set(focal)
    courses = [course for course in rules.courses if course.code in wanted]
    runs = [
        timed(lambda: GENERATOR.generate(student, history, rules, symbols))
        for _ in range(REPEATS)
    ]
    statuses, checking = timed(
        lambda: ELIGIBILITY.check(courses, history, rules, symbols, student)
    )
    times = {f"generate_{i + 1}": f"{t:.4f}" for i, (_, t) in enumerate(runs)}
    times |= {"check": f"{checking:.4f}", "checker": f"{checker:.4f}"}
    return checked, read(runs[0][0], statuses), courses, times


def metamorphic(
    one: sweep.Made,
    student: Student,
    history: Sequence[CourseHistoryLine],
    rules: RuleSet,
    symbols: Mapping[str, ResultSymbol],
    checked: Checked,
    engine: Engine,
    courses: list[Course],
) -> list[dict[str, str]]:
    rng = random.Random(f"{sweep.SEED}/{one.record}")
    found = []

    def relation(
        name: str, course: str, applies: bool, held: bool, detail: str = ""
    ) -> None:
        found.append(
            {
                "record": one.record,
                "set": SETS[one.kind],
                "relation": name,
                "course": course,
                "applies": "yes" if applies else "no",
                "held": ("yes" if held else "no") if applies else "",
                "detail": detail,
            }
        )

    # Her history in another order gives the same plan sets and statuses
    shuffled = list(history)
    rng.shuffle(shuffled)
    again = read(
        GENERATOR.generate(student, shuffled, rules, symbols),
        ELIGIBILITY.check(courses, shuffled, rules, symbols, student),
    )
    changed = sorted(
        code
        for code in engine.statuses
        if again.statuses[code].status != engine.statuses[code].status
    )
    same = Counter(again.plans) == Counter(engine.plans)
    relation(
        "reordered history",
        "",
        True,
        same and not changed,
        " ".join(changed) + ("" if same else " plans changed"),
    )

    # One alternative section of a plan course taken away never adds a plan. FB3.4 can then leave
    # out a current-year core course that clashes with a repeated or arrears one, which gives new
    # sets rightly, so the relation applies where the checker's FB3.4 drops don't change.
    held = {code for plan in engine.plans for code in plan}
    alternatives: dict[tuple[str, str], set[str]] = defaultdict(set)
    for slot in rules.timetable_slots:
        if slot.choice_group and slot.course_code in held:
            alternatives[slot.course_code, slot.choice_group].add(slot.choice)
    choosable = sorted(key for key, options in alternatives.items() if len(options) > 1)
    if not choosable:
        relation("section removed", "", False, True)
    else:
        code, group = rng.choice(choosable)
        choice = rng.choice(sorted(alternatives[code, group]))
        fewer = rules.model_copy(
            update={
                "timetable_slots": tuple(
                    slot
                    for slot in rules.timetable_slots
                    if (slot.course_code, slot.choice_group, slot.choice)
                    != (code, group, choice)
                )
            }
        )
        core = frozenset.intersection(*checked.plans) if checked.plans else frozenset()
        first = checked.owed or any(
            symbols[line.result].outcome in FAILED for line in history
        )
        unchanged = (
            code not in core
            or not first
            or check(student, history, fewer, symbols).dropped == checked.dropped
        )
        after = read(GENERATOR.generate(student, history, fewer, symbols), {})
        added = set(after.plans) - set(engine.plans)
        relation(
            "section removed",
            f"{code} {group} {choice}",
            unchanged,
            not added,
            codes(added),
        )

    # A pass in a course she hasn't passed never turns another course from eligible to
    # not_eligible. The course itself, and every course its pass covers, turn not_eligible as
    # already passed, so they're left out.
    covers = Covers(rules)
    record = Record(history, covers, symbols)
    approved = {
        m.course_code
        for m in rules.course_group_members
        if m.group_key == COMPLEMENTARY
    }
    for course in courses:
        if course.code in approved or record.has(course.code, DONE):
            continue
        line = CourseHistoryLine(
            student_id=student.id,
            academic_year=2025,
            term=course.term,
            course_code=course.code,
            course_name=course.name,
            credits=course.credits,
            nqf_level=course.nqf_level,
            result="1",
            mark=75,
        )
        after = ELIGIBILITY.check(courses, [*history, line], rules, symbols, student)
        exempt = covers(course.code, course.credits)
        turned = [
            code
            for code, was in sorted(engine.statuses.items())
            if code not in exempt
            and was.status == "eligible"
            and after[code].status == "not_eligible"
        ]
        relation("pass added", course.code, True, not turned, " ".join(turned))
    return found


def written(name: str, rows: Sequence[Mapping[str, Any]]) -> None:
    with (RESULTS / f"{name}.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rules = timetabled(approved_snapshot(2026).rules)
    symbols = {
        row["symbol"]: ResultSymbol(**row)
        for row in json.loads(SYMBOLS.read_text(encoding="utf-8"))
    }
    made = sweep.made(rules)
    sweep.write(made, RESULTS / "sweep")
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    started = time.perf_counter()
    for n, one in enumerate(made, start=1):
        state = load_seed(RESULTS / "sweep" / f"{one.record}.json", ACCOUNT)
        student, history = state.student, state.course_history
        checked, engine, courses, times = ran(student, history, rules, symbols)
        tables = Curriculum(rules, one.curriculum)
        core = {code for year in tables.years for code in tables.core(year)}
        row, decisions = compared(checked, engine, core)
        the_set = SETS[one.kind]
        about = {
            "record": one.record,
            "set": the_set,
            "kind": one.kind,
            "curriculum": one.curriculum,
            "intake": one.intake,
            "year": one.year,
            "course": one.course,
            "base": one.base,
        }
        rows["sweep"].append(about | row)
        rows["decisions"] += [
            {
                "record": one.record,
                "set": the_set,
                "course": code,
                "engine": ours,
                "checker": theirs,
                "match": "yes" if ours == theirs else "no",
                "reason": reason,
            }
            for code, ours, theirs, reason in decisions
        ]
        rows["timings"].append(
            {
                "record": one.record,
                "set": the_set,
                **times,
                "candidates": checked.candidates,
            }
        )
        rows["metamorphic"] += metamorphic(
            one, student, history, rules, symbols, checked, engine, courses
        )
        if n % 25 == 0:
            print(
                f"{n} of {len(made)} records, {time.perf_counter() - started:.0f} s",
                file=sys.stderr,
            )
    for name, found in rows.items():
        written(name, found)
    written(
        "inputs",
        [
            {"file": str(path.relative_to(HERE.parents[2])), "sha256": sha256(path)}
            for path in (RULEBOOK, SYMBOLS)
        ],
    )


if __name__ == "__main__":
    main()
