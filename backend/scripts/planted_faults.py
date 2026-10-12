# Plants each of the 24 faults from my test review in a copy of the backend, runs the unit tests, and
# reports which test caught it. The faults go into a temporary copy, so a run cut short never leaves
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
        False  # in services/stubs.py, so it goes when the engine replaces the stand-ins
    )


FAULTS = [
    Fault(
        1,
        "average: SP counts as 40",
        "src/sage/domain/students.py",
        'mark = 50 if line.result == "SP"',
        'mark = 40 if line.result == "SP"',
    ),
    Fault(
        2,
        "average: rounds half down",
        "src/sage/domain/students.py",
        "rounding=ROUND_HALF_UP",
        "rounding='ROUND_HALF_DOWN'",
    ),
    Fault(
        3,
        "average: unweighted mean",
        "src/sage/domain/students.py",
        "total += mark * line.credits\n            weight += line.credits",
        "total += mark\n            weight += 1",
    ),
    Fault(
        4,
        "accounts: staff domain matched with endswith",
        "src/sage/services/accounts.py",
        'email.rpartition("@")[2] == STAFF_DOMAIN',
        "email.endswith(STAFF_DOMAIN)",
    ),
    Fault(
        5,
        "accounts: email not lower-cased",
        "src/sage/services/accounts.py",
        'email = (identity.email or "").lower()',
        'email = identity.email or ""',
    ),
    Fault(
        6,
        "questionnaire threshold >= 5",
        "src/sage/services/plans.py",
        "len(rows.plans) > 5",
        "len(rows.plans) >= 5",
    ),
    Fault(
        7,
        "questionnaire threshold > 6",
        "src/sage/services/plans.py",
        "len(rows.plans) > 5",
        "len(rows.plans) > 6",
    ),
    Fault(
        8,
        "questionnaire: answers joined, not intersected",
        "src/sage/services/questionnaire.py",
        "kept &= set(options[question][option])",
        "kept |= set(options[question][option])",
    ),
    Fault(
        9,
        "questionnaire: answers that keep nothing allowed",
        "src/sage/services/questionnaire.py",
        "    if not kept:\n        raise NoPlanMatches()",
        "    if False:\n        raise NoPlanMatches()",
    ),
    Fault(
        10,
        "questionnaire: lunch overlap uses <= and >=",
        "src/sage/services/questionnaire.py",
        "meeting.start_time < LUNCH[1] and meeting.end_time > LUNCH[0]",
        "meeting.start_time <= LUNCH[1] and meeting.end_time >= LUNCH[0]",
    ),
    Fault(
        11,
        "questionnaire: week option that keeps no plans offered",
        "src/sage/services/questionnaire.py",
        "if 0 < len(keeps) < len(everyone)",
        "if len(keeps) < len(everyone)",
    ),
    Fault(
        12,
        "chats: pair not stored lowest id first",
        "src/sage/services/chats.py",
        "return min(plan_id, other_plan_id), max(plan_id, other_plan_id)",
        "return plan_id, other_plan_id",
    ),
    Fault(
        13,
        "chats: questionnaire gate off",
        "src/sage/services/chats.py",
        "if rows is not None and plans.questionnaire_needed(rows):",
        "if False:",
    ),
    Fault(
        14,
        "plans: credits not summed per term",
        "src/sage/services/plans.py",
        "totals[course.term] += course.credits",
        "totals[course.term] = course.credits",
    ),
    Fault(
        15,
        "plans: curriculum-only meetings shown to everyone",
        "src/sage/services/plans.py",
        "and (slot.id not in only_for or curriculum in only_for[slot.id])",
        "",
    ),
    Fault(
        16,
        "plans: unchosen alternatives hidden",
        "src/sage/services/plans.py",
        "slot.choice_group not in chosen or chosen[slot.choice_group] == slot.choice",
        "slot.choice_group is None or chosen.get(slot.choice_group) == slot.choice",
    ),
    Fault(
        17,
        "eligibility (stand-in): failed course counts as passed",
        "src/sage/services/stubs.py",
        'if symbols[line.result].outcome in ("pass", "credited")',
        'if symbols[line.result].outcome != "credited"',
        stand_in=True,
    ),
    Fault(
        18,
        "eligibility (stand-in): equivalences ignored",
        "src/sage/services/stubs.py",
        "covered.setdefault(rule.counts_as, rule.course_code)",
        "pass",
        stand_in=True,
    ),
    Fault(
        19,
        "onboarding: plans regenerated every time",
        "src/sage/services/onboarding.py",
        "if current is None or current.plan_set.period != year:",
        "if True:",
    ),
    Fault(
        20,
        "onboarding: unknown result symbol accepted",
        "src/sage/services/onboarding.py",
        "if line.result not in symbols:",
        "if False:",
    ),
    Fault(
        21,
        "onboarding: pending-results warning dropped",
        "src/sage/services/onboarding.py",
        "line.academic_year == previous and not line.result_printed",
        "False",
    ),
    Fault(
        22,
        "history: year of study off by one",
        "src/sage/services/history.py",
        "year_of_study=year - intake_year + 1",
        "year_of_study=year - intake_year",
    ),
    Fault(
        23,
        "history: oldest year first",
        "src/sage/services/history.py",
        "sorted(by_year.items(), reverse=True)",
        "sorted(by_year.items())",
    ),
    Fault(
        24,
        "electives: any code can be hearted",
        "src/sage/services/electives.py",
        "    if code not in {course.code for course in rulebook.year(year).courses}:\n"
        "        raise",
        "    if False:\n        raise",
    ),
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
    # The copy ahead of the real code, and no bytecode cache that could outlive a fault
    env = os.environ | {"PYTHONPATH": str(copy / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    path.write_text(original.replace(fault.find, fault.replace), encoding="utf-8")
    try:
        tests = subprocess.run(
            [sys.executable, "-m", "pytest", "-x", "-q", "-m", "not integration"],
            cwd=copy,
            env=env,
            capture_output=True,
            text=True,
            check=False,  # a failing test is the result, read below
        )
    finally:
        path.write_text(original, encoding="utf-8")
    if tests.returncode == 0:
        return "survived"
    # 1 is a failed test, 2 a test file that wouldn't import. Anything else is pytest itself failing.
    if tests.returncode not in (1, 2):
        raise RuntimeError(
            f"pytest didn't run for fault {fault.number}:\n{tests.stdout}"
        )
    failures = [
        line
        for line in tests.stdout.splitlines()
        if line.startswith(("FAILED ", "ERROR "))
    ]
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
        # SEED_FILE is four folders up from seed.py, so data/ goes beside the copy, as in the repo
        (Path(work) / "data").symlink_to(BACKEND.parent / "data")
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
