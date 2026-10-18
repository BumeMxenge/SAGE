# Plants each of the 26 faults in a copy of the backend, runs the unit tests, and reports which test
# caught it: the 24 from my test review, and two in the review and approval the thesis rests on. The
# tests first run on the copy with no fault, and any failure stops the script, as a broken copy would
# make every fault look caught. The faults go into a temporary copy, so a run cut short never leaves
# one in the real code. A fault whose text no longer matches is reported as not applied, never as
# caught.
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

BACKEND = Path(__file__).resolve().parents[1]


class Fault(NamedTuple):
    number: int
    name: str
    file: str  # under backend/
    find: str
    replace: str
    stand_in: bool = (
        False  # in engine/stubs.py, so it goes when the engine replaces the stand-ins
    )


FAULTS = [
    Fault(
        1,
        "average: SP counts as 40",
        "src/sage/shared/students.py",
        'mark = 50 if line.result == "SP"',
        'mark = 40 if line.result == "SP"',
    ),
    Fault(
        2,
        "average: rounds half down",
        "src/sage/shared/students.py",
        "rounding=ROUND_HALF_UP",
        "rounding='ROUND_HALF_DOWN'",
    ),
    Fault(
        3,
        "average: unweighted mean",
        "src/sage/shared/students.py",
        "total += mark * line.credits\n            weight += line.credits",
        "total += mark\n            weight += 1",
    ),
    Fault(
        4,
        "accounts: staff domain matched with endswith",
        "src/sage/shared/accounts.py",
        'email.rpartition("@")[2] == STAFF_DOMAIN',
        "email.endswith(STAFF_DOMAIN)",
    ),
    Fault(
        5,
        "accounts: email not lower-cased",
        "src/sage/shared/accounts.py",
        'email = (identity.email or "").lower()',
        'email = identity.email or ""',
    ),
    Fault(
        6,
        "questionnaire threshold >= 5",
        "src/sage/features/plans/service.py",
        "len(rows.plans) > 5",
        "len(rows.plans) >= 5",
    ),
    Fault(
        7,
        "questionnaire threshold > 6",
        "src/sage/features/plans/service.py",
        "len(rows.plans) > 5",
        "len(rows.plans) > 6",
    ),
    Fault(
        8,
        "questionnaire: answers joined, not intersected",
        "src/sage/features/questionnaire/service.py",
        "kept &= set(options[question][option])",
        "kept |= set(options[question][option])",
    ),
    Fault(
        9,
        "questionnaire: answers that keep nothing allowed",
        "src/sage/features/questionnaire/service.py",
        "    if not kept:\n        raise NoPlanMatches()",
        "    if False:\n        raise NoPlanMatches()",
    ),
    Fault(
        10,
        "questionnaire: lunch overlap uses <= and >=",
        "src/sage/features/questionnaire/service.py",
        "meeting.start_time < LUNCH[1] and meeting.end_time > LUNCH[0]",
        "meeting.start_time <= LUNCH[1] and meeting.end_time >= LUNCH[0]",
    ),
    Fault(
        11,
        "questionnaire: week option that keeps no plans offered",
        "src/sage/features/questionnaire/service.py",
        "if 0 < len(keeps) < len(everyone)",
        "if len(keeps) < len(everyone)",
    ),
    Fault(
        12,
        "chats: pair not stored lowest id first",
        "src/sage/features/chats/service.py",
        "return min(plan_id, other_plan_id), max(plan_id, other_plan_id)",
        "return plan_id, other_plan_id",
    ),
    Fault(
        13,
        "chats: questionnaire gate off",
        "src/sage/features/chats/service.py",
        "if rows is not None and plans.questionnaire_needed(rows):",
        "if False:",
    ),
    Fault(
        14,
        "plans: credits not summed per term",
        "src/sage/features/plans/service.py",
        "totals[course.term] += course.credits",
        "totals[course.term] = course.credits",
    ),
    Fault(
        15,
        "plans: curriculum-only meetings shown to everyone",
        "src/sage/features/plans/service.py",
        "and (slot.id not in only_for or curriculum in only_for[slot.id])",
        "",
    ),
    Fault(
        16,
        "plans: unchosen alternatives hidden",
        "src/sage/features/plans/service.py",
        "slot.choice_group not in chosen or chosen[slot.choice_group] == slot.choice",
        "slot.choice_group is None or chosen.get(slot.choice_group) == slot.choice",
    ),
    Fault(
        17,
        "eligibility (stand-in): failed course counts as passed",
        "src/sage/engine/stubs.py",
        'if symbols[line.result].outcome in ("pass", "credited")',
        'if symbols[line.result].outcome != "credited"',
        stand_in=True,
    ),
    Fault(
        18,
        "eligibility (stand-in): equivalences ignored",
        "src/sage/engine/stubs.py",
        "covered.setdefault(rule.counts_as, rule.course_code)",
        "pass",
        stand_in=True,
    ),
    Fault(
        19,
        "onboarding: plans regenerated every time",
        "src/sage/features/onboarding/service.py",
        "if current is None or current.plan_set.period != year:",
        "if True:",
    ),
    Fault(
        20,
        "onboarding: unknown result symbol accepted",
        "src/sage/features/onboarding/service.py",
        "if line.result not in symbols:",
        "if False:",
    ),
    Fault(
        21,
        "onboarding: pending-results warning dropped",
        "src/sage/features/onboarding/service.py",
        "line.academic_year == previous and not line.result_printed",
        "False",
    ),
    Fault(
        22,
        "history: year of study off by one",
        "src/sage/features/history/service.py",
        "year_of_study=year - intake_year + 1",
        "year_of_study=year - intake_year",
    ),
    Fault(
        23,
        "history: oldest year first",
        "src/sage/features/history/service.py",
        "sorted(by_year.items(), reverse=True)",
        "sorted(by_year.items())",
    ),
    Fault(
        24,
        "electives: any code can be hearted",
        "src/sage/features/electives/service.py",
        "    if code not in {course.code for course in rulebook.year(year).courses}:\n"
        "        raise",
        "    if False:\n        raise",
    ),
    Fault(
        25,
        "review: a decision stays applied after its reading changes",
        "src/sage/ingestion/review.py",
        'if mine and mine.get("fingerprint") == row.fingerprint:',
        "if mine:",
    ),
    Fault(
        26,
        "approve: passes with a row pending",
        "src/sage/ingestion/review.py",
        "return not (self.pending or self.problems)",
        "return not self.problems",
    ),
]


def run_tests(copy: Path) -> subprocess.CompletedProcess[str]:
    # The unit tests on the copy, ahead of the real code, with no bytecode cache that could outlive a
    # fault
    env = os.environ | {"PYTHONPATH": str(copy / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", "-m", "not integration"],
        cwd=copy,
        env=env,
        capture_output=True,
        text=True,
        check=False,  # a failing test is the result, which the caller reads
    )


def failing(tests: subprocess.CompletedProcess[str]) -> list[str]:
    # pytest's summary line for each test that failed or wouldn't import
    return [
        line
        for line in tests.stdout.splitlines()
        if line.startswith(("FAILED ", "ERROR "))
    ]


def plant(fault: Fault, copy: Path) -> str:
    # The fault's outcome: caught, and by which test, survived, or not applied
    path = copy / fault.file
    original = path.read_text(encoding="utf-8")
    matches = original.count(fault.find)
    if matches == 0:
        return "not applied"
    if matches > 1:
        raise ValueError(
            f"Fault {fault.number} matches {matches} places in {fault.file}"
        )
    path.write_text(original.replace(fault.find, fault.replace), encoding="utf-8")
    try:
        tests = run_tests(copy)
    finally:
        path.write_text(original, encoding="utf-8")
    if tests.returncode == 0:
        return "survived"
    # 1 is a failed test, 2 a test file that wouldn't import. Anything else is pytest itself failing.
    if tests.returncode not in (1, 2):
        raise RuntimeError(
            f"pytest didn't run for fault {fault.number}:\n{tests.stdout}"
        )
    failures = failing(tests)
    return f"caught by {failures[0].split()[1]}" if failures else "caught"


def main() -> None:
    with tempfile.TemporaryDirectory() as work:
        copy = Path(work) / "backend"
        for part in ("src", "tests"):
            shutil.copytree(
                BACKEND / part,
                copy / part,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        shutil.copy2(BACKEND / "pyproject.toml", copy)
        # SEED_FILE and DATA, where the tests find the approved 2026, are four folders up from their
        # modules, and E2's prompt four up from the drafter's test, so data/ and experiments/ go
        # beside the copy, as in the repo. data/ is copied, not linked, so a fault that loses a
        # function's folder can't write to the real one.
        shutil.copytree(BACKEND.parent / "data", Path(work) / "data")
        (Path(work) / "experiments").symlink_to(BACKEND.parent / "experiments")
        baseline = run_tests(copy)
        if baseline.returncode != 0:
            shown = failing(baseline) or baseline.stdout.splitlines()[-20:]
            sys.exit(
                "The tests fail on the copy with no fault, so the copy is broken:\n"
                + "\n".join(shown)
            )
        print("The tests pass on the copy with no fault.", flush=True)
        outcomes = {}
        for fault in FAULTS:
            outcomes[fault] = plant(fault, copy)
            print(f"{fault.number:>2}  {fault.name}: {outcomes[fault]}", flush=True)

    applied = [fault for fault, outcome in outcomes.items() if outcome != "not applied"]
    caught = [fault for fault in applied if outcomes[fault].startswith("caught")]
    stand_ins = " and ".join(str(fault.number) for fault in applied if fault.stand_in)
    print(f"\nCaught {len(caught)} of {len(applied)} planted faults.", end="")
    print(f" {stand_ins} are in the eligibility stand-in." if stand_ins else "")
    if len(applied) < len(FAULTS):
        print(
            f"{len(FAULTS) - len(applied)} no longer match the code and weren't applied."
        )
    # A survivor, or a fault that no longer applies, needs someone's attention
    sys.exit(len(caught) < len(FAULTS))


if __name__ == "__main__":
    main()
