# Loads the made-up student from data/synthetic/ and stores her through the repository interfaces.
# Her rows carry no ids in the file, so this makes them: uuid5 values, the same on every run. The
# file holds her data only: the rules her plans point into come from an approved year, which only
# sage load writes.
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from sage.shared.base import Row, canonical
from sage.shared.repositories import RuleRepository, StudentRepository
from sage.shared.students import (
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


class YearNotLoaded(Exception):
    # Her plans point into this handbook year's rules, and the database holds no approved copy
    pass


class SeedResult(Row):
    written: dict[str, int]  # rows per table, as in the file
    student_differences: tuple[str, ...]  # empty when her data reads back as written


def load_seed(path: Path, account_id: UUID) -> StudentState:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    # Notes for people, and her made-up identity, which the tests and sage sign-in use: neither is
    # her data
    data.pop("_readme", None)
    data.pop("fake_account", None)
    student = _student(data, account_id)
    if data:
        unknown = ", ".join(sorted(data))
        raise ValueError(f"{path.name} has tables the seed doesn't know: {unknown}")
    return student


def require_loaded(rules: RuleRepository, years: Iterable[int]) -> None:
    # Her plans point into their year's rules, so nothing of hers is written until each year is
    # loaded and approved
    for year in years:
        if not any(version.approved for version in rules.get(year).handbook_versions):
            raise YearNotLoaded(year)


def seed(
    rules: RuleRepository, students: StudentRepository, data: StudentState
) -> SeedResult:
    require_loaded(rules, {plan_set.period for plan_set in data.plan_sets})
    students.replace(data)
    stored = students.get(data.student.id)
    return SeedResult(
        written=counts(data),
        student_differences=tuple(student_differences(data, stored)),
    )


def counts(data: StudentState) -> dict[str, int]:
    return {table: len(_rows(data, table)) for table in _student_tables()}


def student_differences(
    expected: StudentState, stored: StudentState | None
) -> list[str]:
    if stored is None:
        return ["students: nothing stored"]
    problems = []
    for table in _student_tables():
        want, got = _rows(expected, table), _rows(stored, table)
        if canonical(want) != canonical(got):
            problems.append(f"{table}: {len(got)} stored, {len(want)} in the file")
    return problems


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
        offered = row.pop("open_plan", None)  # a plan the reply offers to open
        messages.append(
            Message(
                id=new_id("messages", key),
                chat_id=chat.id,
                open_plan_id=plans[offered].id if offered else None,
                **owner,
                **row,
            )
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
