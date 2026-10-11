# Loads the made-up student from data/synthetic/ and stores her through the repository interfaces.
# Her rows carry no ids in the file, so this makes them: uuid5 values, the same on every run.
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sage.domain.base import Row
from sage.domain.repositories import RuleRepository, StudentRepository
from sage.domain.rules import RuleSet
from sage.domain.students import (
    Chat,
    CourseHistoryLine,
    Favourite,
    Message,
    MessageCitation,
    Plan,
    PlanCourse,
    PlanReason,
    PlanSet,
    Student,
    StudentState,
)

# Four folders up from this file: the repo root on a laptop, and / in the backend image, which copies
# the file there for the plan stand-in
SEED_FILE = Path(__file__).resolve().parents[4] / "data" / "synthetic" / "mbali.json"

# Rulebook ids come from the row alone, not the account, so every account seeded from the file
# shares the same timetable slots instead of adding its own copies
RULEBOOK_IDS = uuid5(NAMESPACE_URL, "https://github.com/BumeMxenge/SAGE/rulebook")


class Seed(Row):
    rules: RuleSet
    student: StudentState


class SeedResult(Row):
    written: dict[str, int]  # rows per table, as in the file
    # Rulebook rows already stored differently from the file, which seeding leaves alone
    rulebook_differences: tuple[str, ...]
    student_differences: tuple[str, ...]  # empty when her data reads back as written


def load_seed(path: Path, account_id: UUID) -> Seed:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    # Notes for people, and her made-up identity, which only the tests use: neither is her data
    data.pop("_readme", None)
    data.pop("fake_account", None)
    rules = _rulebook(data)
    student = _student(data, account_id)
    if data:
        unknown = ", ".join(sorted(data))
        raise ValueError(f"{path.name} has tables the seed doesn't know: {unknown}")
    return Seed(rules=rules, student=student)


def seed(rules: RuleRepository, students: StudentRepository, data: Seed) -> SeedResult:
    rules.add_missing(data.rules)
    students.replace(data.student)
    stored_rules = [rules.get(version.year) for version in data.rules.handbook_versions]
    stored_student = students.get(data.student.student.id)
    return SeedResult(
        written=counts(data),
        rulebook_differences=tuple(rulebook_differences(data.rules, stored_rules)),
        student_differences=tuple(student_differences(data.student, stored_student)),
    )


def counts(data: Seed) -> dict[str, int]:
    rules = {table: len(getattr(data.rules, table)) for table in RuleSet.model_fields}
    student = {table: len(_rows(data.student, table)) for table in _student_tables()}
    return rules | student


def rulebook_differences(expected: RuleSet, stored: list[RuleSet]) -> list[str]:
    problems = []
    for table in RuleSet.model_fields:
        have = {text for rules in stored for text in _canonical(getattr(rules, table))}
        missing = sum(text not in have for text in _canonical(getattr(expected, table)))
        if missing:
            problems.append(f"{table}: {missing} of the file's rows stored differently")
    return problems


def student_differences(
    expected: StudentState, stored: StudentState | None
) -> list[str]:
    if stored is None:
        return ["students: nothing stored"]
    problems = []
    for table in _student_tables():
        want, got = _rows(expected, table), _rows(stored, table)
        if _canonical(want) != _canonical(got):
            problems.append(f"{table}: {len(got)} stored, {len(want)} in the file")
    return problems


def _rulebook(data: dict[str, Any]) -> RuleSet:
    tables = {table: data.pop(table, []) for table in RuleSet.model_fields}
    tables["timetable_slots"] = [
        {
            "id": uuid5(
                RULEBOOK_IDS, "timetable_slots/" + json.dumps(row, sort_keys=True)
            )
        }
        | row
        for row in tables["timetable_slots"]
    ]
    return RuleSet.model_validate(tables)


def _student(data: dict[str, Any], account_id: UUID) -> StudentState:
    def new_id(table: str, key: str) -> UUID:
        # From the account and the row's key in the file, so every run makes the same ids
        return uuid5(account_id, f"{table}/{key}")

    owner = {"student_id": account_id}
    profiles = data.pop("students")
    if len(profiles) != 1:
        raise ValueError("a seed file holds exactly one student")

    plan_sets: dict[str, PlanSet] = {}
    for row in data.pop("plan_sets", []):
        key = row.pop("key")
        plan_sets[key] = PlanSet(id=new_id("plan_sets", key), **owner, **row)

    plans: dict[str, Plan] = {}
    periods: dict[UUID, int] = {}  # each plan's year, from its plan set
    for row in data.pop("plans", []):
        key, plan_set = row.pop("key"), plan_sets[row.pop("plan_set")]
        plan = Plan(id=new_id("plans", key), plan_set_id=plan_set.id, **owner, **row)
        plans[key], periods[plan.id] = plan, plan_set.period

    plan_courses = []
    for row in data.pop("plan_courses", []):
        plan_id = plans[row.pop("plan")].id
        # The course link needs the plan set's year, so the year comes from the set
        year = periods[plan_id]
        if row.pop("handbook_year", year) != year:
            course = row["course_code"]
            raise ValueError(
                f"plan_courses: {course} isn't in its plan set's year, {year}"
            )
        plan_courses.append(
            PlanCourse(plan_id=plan_id, handbook_year=year, **owner, **row)
        )

    plan_reasons = []
    for row in data.pop("plan_reasons", []):
        key, plan_set, plan = (
            row.pop("key"),
            plan_sets[row.pop("plan_set")],
            row.pop("plan"),
        )
        plan_reasons.append(
            PlanReason(
                id=new_id("plan_reasons", key),
                plan_set_id=plan_set.id,
                plan_id=plans[plan].id if plan else None,
                **owner,
                **row,
            )
        )

    chats: dict[str, Chat] = {}
    for row in data.pop("chats", []):
        key, plan, other = row.pop("key"), row.pop("plan"), row.pop("other_plan")
        first, second = plans[plan].id, plans[other].id if other else None
        # A pair is stored lowest id first, as the table demands, and the ids only exist now
        if second is not None and second < first:
            first, second = second, first
        chats[key] = Chat(
            id=new_id("chats", key), plan_id=first, other_plan_id=second, **owner, **row
        )

    messages = []
    for row in data.pop("messages", []):
        key, chat = row.pop("key"), chats[row.pop("chat")]
        messages.append(
            Message(id=new_id("messages", key), chat_id=chat.id, **owner, **row)
        )

    return StudentState(
        student=Student(id=account_id, **profiles[0]),
        course_history=tuple(
            CourseHistoryLine(**owner, **row) for row in data.pop("course_history", [])
        ),
        favourites=tuple(
            Favourite(**owner, **row) for row in data.pop("favourites", [])
        ),
        plan_sets=tuple(plan_sets.values()),
        plans=tuple(plans.values()),
        plan_courses=tuple(plan_courses),
        plan_reasons=tuple(plan_reasons),
        chats=tuple(chats.values()),
        messages=tuple(messages),
        message_citations=tuple(
            MessageCitation(**owner, **row) for row in data.pop("message_citations", [])
        ),
    )


def _student_tables() -> list[str]:
    # Her tables by name: the profile field holds the one students row
    return [
        "students" if field == "student" else field
        for field in StudentState.model_fields
    ]


def _rows(state: StudentState, table: str) -> tuple[Row, ...]:
    return (state.student,) if table == "students" else getattr(state, table)


def _canonical(rows: Iterable[Row]) -> list[str]:
    # Rows as sorted JSON text, so neither row order nor the key order jsonb stores matters
    return sorted(
        json.dumps(row.model_dump(mode="json"), sort_keys=True) for row in rows
    )
