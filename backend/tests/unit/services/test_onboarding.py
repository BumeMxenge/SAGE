# Checks Finish setup generates one plan set a year however often she presses it, from the lines she
# confirmed and that year's rules
from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.domain.rules import RuleSet
from sage.domain.students import (
    CourseHistoryLine,
    PlanSet,
    PlanSetRows,
    Student,
    StudentState,
)
from sage.services import onboarding
from sage.services.rulebook import Rulebook
from sage.services.seed import load_seed

STUDENT = UUID(int=1)


class Generator:
    # Stands in for the engine: records every call, and gives each set new ids, as the engine will.
    # The seeded stand-in can't show a second set, as it makes the same ids every time.
    def __init__(self) -> None:
        self.calls: list[tuple[Sequence[CourseHistoryLine], RuleSet]] = []

    def generate(
        self, student: Student, history: Sequence[CourseHistoryLine], rules: RuleSet
    ) -> PlanSetRows:
        self.calls.append((history, rules))
        return PlanSetRows(
            plan_set=PlanSet(id=uuid4(), student_id=student.id, period=2026, version=1)
        )


@pytest.fixture
def setup(seed_file, result_symbols):
    # Her stores with the 2026 rulebook and nothing of hers, and the lines she confirms
    data = load_seed(seed_file, STUDENT)
    rules = InMemoryRuleRepository(result_symbols)
    rules.add_missing(data.rules)
    return InMemoryStudentRepository(), Rulebook(rules), data.student.course_history


def finish(setup, generator: Generator) -> None:
    students, rulebook, history = setup
    onboarding.complete(STUDENT, "EB011EEE05", history, students, rulebook, generator)


def test_finishing_setup_twice_generates_one_plan_set(setup):
    students, rulebook, history = setup
    generator = Generator()
    finish(setup, generator)
    finish(setup, generator)
    assert generator.calls == [(history, rulebook.year(2026))]
    assert len(students.get(STUDENT).plan_sets) == 1


def test_a_plan_set_from_an_earlier_year_gets_this_years_after_it(setup):
    students = setup[0]
    earlier = PlanSet(
        id=uuid4(), student_id=STUDENT, period=2025, version=1, complete=True
    )
    students.replace(StudentState(student=Student(id=STUDENT), plan_sets=(earlier,)))
    generator = Generator()
    finish(setup, generator)
    assert len(generator.calls) == 1
    assert [row.period for row in students.get(STUDENT).plan_sets] == [2025, 2026]
